"""Pencatatan kejadian, penugasan dan verifikasi laporan lapangan."""

import json
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from math import isfinite

from flask import abort, flash, g, redirect, render_template, request, session, url_for

from decision_engine import VERSION, field_criterion_values
from auth import ROLES, require_role as authorize
from database import insert_id
from rounds import open_round

ACTORS = dict(ROLES)
HISTORIC_LABELS = {**ACTORS, "admin": "Kepala BPBD (riwayat)",
                   "petugas-1": "Petugas 1 (riwayat)", "petugas-2": "Petugas 2 (riwayat)"}
FIELD_OWNERS = ("lapangan", "petugas-1", "petugas-2")
WIB = timezone(timedelta(hours=7))
FIELDS = (
    ("evacuees", "Pengungsi (orang)", int, 0, 2**63 - 1),
    ("vulnerable_people", "Pengungsi rentan (orang)", int, 0, 2**63 - 1),
    ("housing_damage_score", "Kerusakan hunian (1–5)", int, 1, 5),
    ("essential_services_disruption_score", "Gangguan layanan dasar (1–5)", int, 1, 5),
    ("available_package_equivalents", "Stok (setara paket)", float, 0, None),
    ("required_package_equivalents", "Kebutuhan (setara paket)", float, 0, None),
    ("distance_to_epicenter_km", "Jarak posko induk ke titik gempa (km)", float, 0, None),
)
LEGACY_FIELDS = FIELDS[:-1] + (("hours_since_last_delivery", "Waktu sejak bantuan terakhir (jam, arsip)", float, 0, None),)


class ObservationError(ValueError):
    def __init__(self, field, message):
        super().__init__(message)
        self.field = field


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def text_field(data, key, label, limit=120, required=True):
    value = data.get(key, "").strip()
    if (required and not value) or len(value) > limit:
        raise ValueError(f"{label} harus diisi (maksimal {limit} karakter)." if not value
                         else f"{label} maksimal {limit} karakter.")
    return value


def time_field(value, label, assume_wib=False):
    try:
        date = datetime.fromisoformat(value)
        if "T" not in value:
            raise ValueError
        if date.tzinfo is None:
            if not assume_wib:
                raise ValueError
            date = date.replace(tzinfo=WIB)
        date = date.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        if assume_wib:
            raise ValueError(f"Pilih tanggal dan jam {label.lower()} yang valid melalui kalender.") from None
        raise ValueError(f"{label} harus memakai waktu ISO dengan zona, misalnya 2026-05-01T08:00+07:00.") from None
    if date > datetime.now(timezone.utc):
        raise ValueError(f"{label} tidak boleh di masa depan.")
    return date.isoformat()


def read_observations(data, incident_at, complete):
    observed = data.get("observed_at", "").strip()
    if complete or observed:
        try:
            observed = time_field(observed, "Waktu observasi", assume_wib=True)
        except ValueError as error:
            raise ObservationError("observed_at",str(error)) from None
        if datetime.fromisoformat(observed) < datetime.fromisoformat(incident_at):
            raise ObservationError("observed_at","Waktu observasi tidak boleh mendahului kejadian.")
    try:
        source = text_field(data, "source_note", "Sumber observasi", 500, complete)
    except ValueError as error:
        raise ObservationError("source_note",str(error)) from None
    result = dict(observed_at=observed, source_note=source)
    for key, label, cast, low, high in FIELDS:
        raw = data.get(key, "").strip()
        if not raw and not complete:
            result[key] = None
            continue
        try:
            value = cast(raw)
            if not isfinite(value) or value < low or (high is not None and value > high):
                raise ValueError
        except (ValueError, OverflowError):
            raise ObservationError(key,f"Periksa nilai {label}.") from None
        result[key] = value
    total, vulnerable, _, _, _, needed, _ = (result[key] for key, *_ in FIELDS)
    if total is not None and vulnerable is not None and vulnerable > total:
        raise ObservationError("vulnerable_people","Jumlah pengungsi rentan tidak boleh melebihi jumlah pengungsi.")
    if complete and needed == 0:
        raise ObservationError("required_package_equivalents","Kebutuhan logistik nol memerlukan verifikasi khusus sebelum laporan bisa dikirim.")
    return result


def register_fieldwork(app, connect, check_form):
    @app.template_filter("datetime_input_wib")
    def datetime_input_wib(value):
        if not value:
            return ""
        try:
            date = datetime.fromisoformat(value)
            if date.tzinfo is not None:
                date = date.astimezone(WIB)
            return date.strftime("%Y-%m-%dT%H:%M")
        except (ValueError, OverflowError):
            return ""

    @app.template_filter("datetime_display_wib")
    def datetime_display_wib(value):
        try:
            date = datetime.fromisoformat(value)
            date = date.replace(tzinfo=WIB) if date.tzinfo is None else date.astimezone(WIB)
            return date.strftime("%d/%m/%Y, %H:%M WIB")
        except (ValueError, OverflowError):
            return value

    def actor():
        return g.user["role"]

    def require_role(admin=False):
        return authorize("bpbd" if admin else "lapangan")

    def one(db, query, args):
        row = db.execute(query, args).fetchone()
        if row is None:
            abort(404)
        return row

    def audit(db, action, entity, entity_id):
        db.execute("INSERT INTO fieldwork_audit(actor_id, action, entity_type, entity_id, created_at) "
                   "VALUES (?, ?, ?, ?, ?)", (str(g.user["id"]), action, entity, entity_id, timestamp()))

    def page(section, **context):
        token = session.setdefault("form_token", secrets.token_urlsafe(24))
        from dashboard import district_catalog
        return render_template("fieldwork.html", section=section, actors=HISTORIC_LABELS, actor=actor(),
                               catalog=district_catalog(),
                               token=token, fields=context.pop("fields",FIELDS),
                               field_errors=context.pop("field_errors",{}),
                               incident_time_max=datetime.now(WIB).strftime("%Y-%m-%dT%H:%M"), **context)

    @app.get("/pendataan")
    def fieldwork_home():
        with connect() as db:
            cases = db.execute("SELECT * FROM disaster_cases ORDER BY id DESC").fetchall() if actor() != "lapangan" else []
            assignments = []
            if actor() == "lapangan":
                assignments = db.execute(
                    """SELECT a.id, d.district_name, c.name AS case_name, c.case_code, c.is_simulation,
                    r.status,r.criteria_version,r.version AS report_version
                    FROM assignments a JOIN districts d ON a.district_id=d.id
                    JOIN disaster_cases c ON d.case_id=c.id
                    LEFT JOIN field_reports r ON r.id=(SELECT id FROM field_reports WHERE district_id=d.id ORDER BY version DESC LIMIT 1)
                    WHERE a.officer_id IN (?, ?, ?) ORDER BY c.id DESC,d.district_name""", FIELD_OWNERS,
                ).fetchall()
        stats=dict(total=len(assignments),todo=sum(not row["status"] or row["status"] in {"DRAFT","REJECTED"} or row["criteria_version"] != VERSION for row in assignments),
                   submitted=sum(row["status"]=="SUBMITTED" for row in assignments),
                   verified=sum(row["status"]=="VERIFIED" and row["criteria_version"]==VERSION for row in assignments))
        return page("home", cases=cases, assignments=assignments,task_stats=stats,current_criteria_version=VERSION)

    @app.post("/pendataan/kejadian")
    def fieldwork_new_case():
        require_role(admin=True)
        check_form()
        data = request.form
        try:
            raw_magnitude = data.get("magnitude", "").strip()
            magnitude = float(raw_magnitude) if raw_magnitude else None
            if magnitude is not None and not isfinite(magnitude):
                raise ValueError("Magnitudo harus berupa angka.")
            values = (
                text_field(data, "case_code", "Kode kejadian", 40).upper(),
                text_field(data, "name", "Nama kejadian"),
                time_field(data.get("incident_at", ""), "Waktu kejadian", assume_wib=True),
                text_field(data, "province", "Provinsi"),
                text_field(data, "regency", "Kabupaten/kota"),
                magnitude, text_field(data, "information_source", "Sumber informasi", 500),
                int(data.get("is_simulation") == "1"), timestamp(),
            )
        except ValueError as error:
            return page("new_case", error=str(error), form=data), 422
        with connect() as db, db:
            try:
                case_id = insert_id(db,
                    """INSERT INTO disaster_cases(case_code, name, incident_at, province, regency,
                    magnitude, information_source, is_simulation, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    values,
                )
            except sqlite3.IntegrityError:
                return page("new_case", error="Kode kejadian sudah dipakai.", form=data), 409
            audit(db, "CREATE", "disaster_case", case_id)
        return redirect(url_for("fieldwork_case", case_id=case_id), code=303)

    @app.route("/pendataan/kejadian/<int:case_id>", methods=["GET", "POST"])
    def fieldwork_case(case_id):
        authorize("bpbd", "lapangan", "sosial")
        error = None
        status = 200
        if request.method == "POST":
            authorize("bpbd", "lapangan")
            check_form()
        with connect() as db, db:
            db.execute("BEGIN IMMEDIATE" if request.method == "POST" else "BEGIN")
            case = one(db, "SELECT * FROM disaster_cases WHERE id=?", (case_id,))
            if request.method == "POST":
                try:
                    data = request.form
                    action = data.get("action")
                    if action == "district":
                        from dashboard import district_catalog
                        code = data.get("district_code")
                        district = next((item for item in district_catalog() if item["code"] == code), None)
                        if district is None:
                            raise ValueError("Pilih kecamatan dari wilayah Malang Raya.")
                        if case["regency"] in {"Kabupaten Malang", "Kota Malang", "Kota Batu"} and case["regency"] != district["regency"]:
                            raise ValueError("Kecamatan harus berada dalam wilayah kejadian.")
                        district_id = insert_id(db, """INSERT INTO districts(case_id, district_code, district_name,
                                                verification_status, proposed_by) VALUES (?, ?, ?, ?, ?)""",
                                                (case_id, code, district["name"],
                                                 "APPROVED" if actor() == "bpbd" else "PENDING", actor()))
                        audit(db, "CREATE", "district", district_id)
                        if actor() == "lapangan":
                            assignment_id = insert_id(db, "INSERT INTO assignments(district_id, officer_id, assigned_at) "
                                                      "VALUES (?, ?, ?)", (district_id, "lapangan", timestamp()))
                            audit(db, "ASSIGN", "assignment", assignment_id)
                    elif action == "assign":
                        authorize("bpbd")
                        district = one(db, "SELECT id FROM districts WHERE id=? AND case_id=?",
                                       (data.get("district_id"), case_id))
                        assignment_id = insert_id(db, "INSERT INTO assignments(district_id, officer_id, assigned_at) VALUES (?, ?, ?)",
                                                  (district["id"], "lapangan", timestamp()))
                        audit(db, "ASSIGN", "assignment", assignment_id)
                    elif action == "approve_district":
                        authorize("bpbd")
                        district = one(db, "SELECT * FROM districts WHERE id=? AND case_id=?",
                                       (data.get("district_id"), case_id))
                        if district["verification_status"] != "PENDING":
                            abort(409)
                        db.execute("UPDATE districts SET verification_status='APPROVED' WHERE id=?", (district["id"],))
                        audit(db, "APPROVE", "district", district["id"])
                    elif action == "open_round":
                        authorize("bpbd")
                        round_id,created = open_round(db,case_id)
                        if created:
                            audit(db,"OPEN_ROUND","decision_round",round_id)
                        return redirect(url_for("assessment",role="bpbd",round_id=round_id),code=303)
                    else:
                        abort(400)
                except ValueError as exc:
                    error, status = str(exc), 422
                except sqlite3.IntegrityError:
                    error = "Kode kecamatan sudah dipakai." if action == "district" else "Petugas sudah ditugaskan."
                    status = 409
                else:
                    return redirect(url_for("fieldwork_case", case_id=case_id), code=303)
            districts = db.execute("SELECT * FROM districts WHERE case_id=? ORDER BY district_code", (case_id,)).fetchall()
            assignments = db.execute(
                """SELECT a.* FROM assignments a JOIN districts d ON d.id=a.district_id WHERE d.case_id=?""",
                (case_id,),
            ).fetchall()
            reports = db.execute(
                """SELECT r.*, v.note, a.officer_id FROM field_reports r
                JOIN districts d ON d.id=r.district_id JOIN assignments a ON a.id=r.assignment_id
                LEFT JOIN field_report_reviews v ON v.report_id=r.id
                WHERE d.case_id=? ORDER BY r.version DESC""", (case_id,),
            ).fetchall()
            decision_round = db.execute("SELECT id,finalized_at,algorithm_version FROM decision_rounds WHERE case_id=? ORDER BY id DESC LIMIT 1",
                                        (case_id,)).fetchone()
        latest = {}
        for report in reports:
            latest.setdefault(report["district_id"], report["status"])
        verified = sum(state == "VERIFIED" for state in latest.values())
        return page("case", case=case, districts=districts, assignments=assignments, reports=reports,
                    verified=verified, error=error, form=request.form, decision_round=decision_round,
                    selected_round_id=decision_round["id"] if decision_round else None,current_criteria_version=VERSION), status

    @app.route("/pendataan/tugas/<int:assignment_id>", methods=["GET", "POST"])
    def fieldwork_assignment(assignment_id):
        officer = require_role()
        error = None
        field_errors = {}
        status = 200
        if request.method == "POST":
            check_form()
        with connect() as db, db:
            db.execute("BEGIN IMMEDIATE" if request.method == "POST" else "BEGIN")
            task = one(db, """SELECT a.*, d.district_name, c.name AS case_name,c.case_code, c.incident_at, c.is_simulation
                              FROM assignments a JOIN districts d ON d.id=a.district_id
                              JOIN disaster_cases c ON c.id=d.case_id WHERE a.id=?""", (assignment_id,))
            if task["officer_id"] not in FIELD_OWNERS:
                abort(403)
            reports = db.execute(
                """SELECT r.*, v.note FROM field_reports r LEFT JOIN field_report_reviews v ON v.report_id=r.id
                WHERE r.district_id=? ORDER BY r.version DESC""", (task["district_id"],),
            ).fetchall()
            latest = reports[0] if reports else None
            owned = latest and latest["assignment_id"] == assignment_id
            editable = latest is None or latest["status"] in {"REJECTED", "VERIFIED"} or (
                owned and latest["status"] == "DRAFT")
            stamp = f"{latest['id']}:{latest['revision']}" if latest else "0"
            form = json.loads(latest["observations"]) if owned else {}
            if request.method == "POST":
                data = request.form
                action = data.get("action")
                if action not in {"draft", "submit"}:
                    abort(400)
                if not editable or data.get("stamp") != stamp:
                    error, status = "Status laporan berubah. Periksa kembali versi terbaru.", 409
                else:
                    form = data
                    try:
                        observations = read_observations(data, task["incident_at"], action == "submit")
                    except ValueError as exc:
                        error, status = str(exc), 422
                        if isinstance(exc,ObservationError):
                            field_errors[exc.field]=str(exc)
                    else:
                        next_status = "SUBMITTED" if action == "submit" else "DRAFT"
                        criteria = (field_criterion_values(*(observations[key] for key, *_ in FIELDS))
                                    if action == "submit" else None)
                        values = (next_status, json.dumps(observations), json.dumps(criteria) if criteria else None,
                                  timestamp() if action == "submit" else None)
                        if owned and latest["status"] == "DRAFT":
                            report_id = latest["id"]
                            db.execute("""UPDATE field_reports SET status=?, observations=?, criterion_values=?,
                                       submitted_at=?,criteria_version=?, revision=revision+1 WHERE id=?""", (*values, VERSION,report_id))
                        else:
                            version = latest["version"] + 1 if latest else 1
                            report_id = insert_id(db,
                                """INSERT INTO field_reports(status, observations, criterion_values, submitted_at,
                                assignment_id, district_id, version, created_at,criteria_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?,?)""",
                                (*values, assignment_id, task["district_id"], version, timestamp(),VERSION),
                            )
                        audit(db, "SUBMIT" if action == "submit" else "SAVE_DRAFT", "field_report", report_id)
                        flash("Laporan berhasil dikirim untuk verifikasi Kepala BPBD." if action == "submit" else "Draf laporan berhasil disimpan.")
                        return redirect(url_for("fieldwork_assignment", assignment_id=assignment_id), code=303)
        return page("assignment", task=task, reports=[row for row in reports if row["assignment_id"] == assignment_id],
                    editable=editable, stamp=stamp, error=error, form=form,field_errors=field_errors,
                    latest=latest,needs_distance_update=bool(latest and latest["criteria_version"] != VERSION),
                    summary_values=json.loads(latest["criterion_values"]) if latest and latest["criterion_values"] else None,
                    observation_time_min=task["incident_at"]), status

    @app.route("/pendataan/laporan/<int:report_id>", methods=["GET", "POST"])
    def fieldwork_review(report_id):
        admin = authorize("bpbd", "lapangan", "sosial")
        error = None
        if request.method == "POST":
            require_role(admin=True)
            check_form()
        with connect() as db, db:
            db.execute("BEGIN IMMEDIATE" if request.method == "POST" else "BEGIN")
            report = one(db, """SELECT r.*, d.case_id, d.district_name, d.verification_status, c.is_simulation,
                             a.officer_id, v.note FROM field_reports r JOIN districts d ON d.id=r.district_id
                             JOIN disaster_cases c ON c.id=d.case_id
                             JOIN assignments a ON a.id=r.assignment_id
                             LEFT JOIN field_report_reviews v ON v.report_id=r.id WHERE r.id=?""", (report_id,))
            if request.method == "POST":
                if report["status"] != "SUBMITTED":
                    abort(409, "Hanya laporan yang sudah dikirim yang dapat diperiksa.")
                if report["verification_status"] != "APPROVED":
                    abort(409, "Setujui usulan kecamatan sebelum memverifikasi laporannya.")
                outcome = request.form.get("outcome")
                if outcome not in {"VERIFIED", "REJECTED"}:
                    abort(400)
                if outcome == "VERIFIED" and report["criteria_version"] != VERSION:
                    abort(409,"Laporan ini memakai C6 lama. Kembalikan untuk revisi jarak C6 sebelum menyetujuinya.")
                try:
                    note = text_field(request.form, "note", "Alasan penolakan" if outcome == "REJECTED"
                                      else "Catatan", 500, outcome == "REJECTED")
                except ValueError as exc:
                    error = str(exc)
                else:
                    db.execute("UPDATE field_reports SET status=?, revision=revision+1 WHERE id=?", (outcome, report_id))
                    db.execute("INSERT INTO field_report_reviews VALUES (?, ?, ?, ?, ?)",
                               (report_id, admin, outcome, note, timestamp()))
                    audit(db, outcome, "field_report", report_id)
                    return redirect(url_for("fieldwork_case", case_id=report["case_id"]), code=303)
        return page("review", report=report, form=json.loads(report["observations"]),
                    criteria=json.loads(report["criterion_values"]) if report["criterion_values"] else None,
                    error=error,fields=FIELDS if report["criteria_version"]==VERSION else LEGACY_FIELDS), 422 if error else 200
