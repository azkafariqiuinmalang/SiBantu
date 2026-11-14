"""Pencatatan kejadian, penugasan dan verifikasi laporan lapangan."""

import json
import secrets
import sqlite3
from datetime import datetime, timezone
from math import isfinite

from flask import abort, redirect, render_template, request, session, url_for

from decision_engine import field_criterion_values

ACTORS = {
    "admin": "Admin",
    "petugas-1": "Petugas Lapangan 1",
    "petugas-2": "Petugas Lapangan 2",
}
FIELDS = (
    ("evacuees", "Pengungsi (orang)", int, 0, 2**63 - 1),
    ("vulnerable_people", "Pengungsi rentan (orang)", int, 0, 2**63 - 1),
    ("housing_damage_score", "Kerusakan hunian (1–5)", int, 1, 5),
    ("essential_services_disruption_score", "Gangguan layanan dasar (1–5)", int, 1, 5),
    ("available_package_equivalents", "Stok (setara paket)", float, 0, None),
    ("required_package_equivalents", "Kebutuhan (setara paket)", float, 0, None),
    ("hours_since_last_delivery", "Waktu sejak bantuan terakhir (jam)", float, 0, None),
)


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def text_field(data, key, label, limit=120, required=True):
    value = data.get(key, "").strip()
    if (required and not value) or len(value) > limit:
        raise ValueError(f"{label} harus diisi (maksimal {limit} karakter)." if not value
                         else f"{label} maksimal {limit} karakter.")
    return value


def time_field(value, label):
    try:
        date = datetime.fromisoformat(value)
        if "T" not in value or date.tzinfo is None:
            raise ValueError
        date = date.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise ValueError(f"{label} harus memakai waktu ISO dengan zona, misalnya 2026-05-01T08:00+07:00.") from None
    if date > datetime.now(timezone.utc):
        raise ValueError(f"{label} tidak boleh di masa depan.")
    return date.isoformat()


def read_observations(data, incident_at, complete):
    observed = data.get("observed_at", "").strip()
    if complete or observed:
        observed = time_field(observed, "Waktu observasi")
        if datetime.fromisoformat(observed) < datetime.fromisoformat(incident_at):
            raise ValueError("Waktu observasi tidak boleh mendahului kejadian.")
    source = text_field(data, "source_note", "Sumber observasi", 500, complete)
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
            raise ValueError(f"Periksa nilai {label}.") from None
        result[key] = value
    total, vulnerable, _, _, _, needed, _ = (result[key] for key, *_ in FIELDS)
    if total is not None and vulnerable is not None and vulnerable > total:
        raise ValueError("Jumlah pengungsi rentan tidak boleh melebihi jumlah pengungsi.")
    if complete and needed == 0:
        raise ValueError("Kebutuhan logistik nol memerlukan verifikasi khusus sebelum laporan bisa dikirim.")
    return result


def register_fieldwork(app, connect, check_form):
    def actor():
        return session.get("field_actor")

    def require_role(admin=False):
        current = actor()
        if current not in ACTORS or (current == "admin") != admin:
            abort(403)
        return current

    def one(db, query, args):
        row = db.execute(query, args).fetchone()
        if row is None:
            abort(404)
        return row

    def audit(db, action, entity, entity_id):
        db.execute("INSERT INTO fieldwork_audit(actor_id, action, entity_type, entity_id, created_at) "
                   "VALUES (?, ?, ?, ?, ?)", (actor(), action, entity, entity_id, timestamp()))

    def page(section, **context):
        token = session.setdefault("form_token", secrets.token_urlsafe(24))
        return render_template("fieldwork.html", section=section, actors=ACTORS, actor=actor(),
                               token=token, fields=FIELDS, **context)

    @app.get("/pendataan")
    def fieldwork_home():
        with connect() as db:
            cases, assignments = [], []
            if actor() == "admin":
                cases = db.execute("SELECT * FROM disaster_cases ORDER BY id DESC").fetchall()
            elif actor() in ACTORS:
                assignments = db.execute(
                    """SELECT a.id, d.district_name, c.name AS case_name, c.is_simulation
                    FROM assignments a JOIN districts d ON a.district_id=d.id
                    JOIN disaster_cases c ON d.case_id=c.id
                    WHERE a.officer_id=? ORDER BY a.id DESC""", (actor(),),
                ).fetchall()
        return page("home", cases=cases, assignments=assignments)

    @app.post("/pendataan/peran")
    def fieldwork_actor():
        check_form()
        chosen = request.form.get("actor")
        if chosen not in ACTORS:
            abort(422, "Peran demo tidak dikenal.")
        session["field_actor"] = chosen
        return redirect(url_for("fieldwork_home"), code=303)

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
                time_field(data.get("incident_at", ""), "Waktu kejadian"),
                text_field(data, "province", "Provinsi"),
                text_field(data, "regency", "Kabupaten/kota"),
                magnitude, text_field(data, "information_source", "Sumber informasi", 500),
                int(data.get("is_simulation") == "1"), timestamp(),
            )
        except ValueError as error:
            return page("new_case", error=str(error), form=data), 422
        with connect() as db, db:
            try:
                cursor = db.execute(
                    """INSERT INTO disaster_cases(case_code, name, incident_at, province, regency,
                    magnitude, information_source, is_simulation, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    values,
                )
            except sqlite3.IntegrityError:
                return page("new_case", error="Kode kejadian sudah dipakai.", form=data), 409
            case_id = cursor.lastrowid
            audit(db, "CREATE", "disaster_case", case_id)
        return redirect(url_for("fieldwork_case", case_id=case_id), code=303)

    @app.route("/pendataan/kejadian/<int:case_id>", methods=["GET", "POST"])
    def fieldwork_case(case_id):
        require_role(admin=True)
        error = None
        status = 200
        if request.method == "POST":
            check_form()
        with connect() as db, db:
            db.execute("BEGIN IMMEDIATE" if request.method == "POST" else "BEGIN")
            case = one(db, "SELECT * FROM disaster_cases WHERE id=?", (case_id,))
            if request.method == "POST":
                try:
                    data = request.form
                    action = data.get("action")
                    if action == "district":
                        cursor = db.execute("INSERT INTO districts(case_id, district_code, district_name) VALUES (?, ?, ?)",
                                            (case_id, text_field(data, "district_code", "Kode kecamatan", 40).upper(),
                                             text_field(data, "district_name", "Nama kecamatan")))
                        audit(db, "CREATE", "district", cursor.lastrowid)
                    elif action == "assign":
                        district = one(db, "SELECT id FROM districts WHERE id=? AND case_id=?",
                                       (data.get("district_id"), case_id))
                        officer = data.get("officer_id")
                        if officer not in ACTORS or officer == "admin":
                            raise ValueError("Pilih petugas lapangan yang tersedia.")
                        cursor = db.execute("INSERT INTO assignments(district_id, officer_id, assigned_at) VALUES (?, ?, ?)",
                                            (district["id"], officer, timestamp()))
                        audit(db, "ASSIGN", "assignment", cursor.lastrowid)
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
        latest = {}
        for report in reports:
            latest.setdefault(report["district_id"], report["status"])
        verified = sum(state == "VERIFIED" for state in latest.values())
        return page("case", case=case, districts=districts, assignments=assignments, reports=reports,
                    verified=verified, error=error, form=request.form), status

    @app.route("/pendataan/tugas/<int:assignment_id>", methods=["GET", "POST"])
    def fieldwork_assignment(assignment_id):
        officer = require_role()
        error = None
        status = 200
        if request.method == "POST":
            check_form()
        with connect() as db, db:
            db.execute("BEGIN IMMEDIATE" if request.method == "POST" else "BEGIN")
            task = one(db, """SELECT a.*, d.district_name, c.name AS case_name, c.incident_at, c.is_simulation
                              FROM assignments a JOIN districts d ON d.id=a.district_id
                              JOIN disaster_cases c ON c.id=d.case_id WHERE a.id=?""", (assignment_id,))
            if task["officer_id"] != officer:
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
                    else:
                        next_status = "SUBMITTED" if action == "submit" else "DRAFT"
                        criteria = (field_criterion_values(*(observations[key] for key, *_ in FIELDS))
                                    if action == "submit" else None)
                        values = (next_status, json.dumps(observations), json.dumps(criteria) if criteria else None,
                                  timestamp() if action == "submit" else None)
                        if owned and latest["status"] == "DRAFT":
                            report_id = latest["id"]
                            db.execute("""UPDATE field_reports SET status=?, observations=?, criterion_values=?,
                                       submitted_at=?, revision=revision+1 WHERE id=?""", (*values, report_id))
                        else:
                            version = latest["version"] + 1 if latest else 1
                            report_id = db.execute(
                                """INSERT INTO field_reports(status, observations, criterion_values, submitted_at,
                                assignment_id, district_id, version, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                (*values, assignment_id, task["district_id"], version, timestamp()),
                            ).lastrowid
                        audit(db, "SUBMIT" if action == "submit" else "SAVE_DRAFT", "field_report", report_id)
                        return redirect(url_for("fieldwork_assignment", assignment_id=assignment_id), code=303)
        return page("assignment", task=task, reports=[row for row in reports if row["assignment_id"] == assignment_id],
                    editable=editable, stamp=stamp, error=error, form=form), status

    @app.route("/pendataan/laporan/<int:report_id>", methods=["GET", "POST"])
    def fieldwork_review(report_id):
        admin = require_role(admin=True)
        error = None
        if request.method == "POST":
            check_form()
        with connect() as db, db:
            db.execute("BEGIN IMMEDIATE" if request.method == "POST" else "BEGIN")
            report = one(db, """SELECT r.*, d.case_id, d.district_name, c.is_simulation,
                             a.officer_id, v.note FROM field_reports r JOIN districts d ON d.id=r.district_id
                             JOIN disaster_cases c ON c.id=d.case_id
                             JOIN assignments a ON a.id=r.assignment_id
                             LEFT JOIN field_report_reviews v ON v.report_id=r.id WHERE r.id=?""", (report_id,))
            if request.method == "POST":
                if report["status"] != "SUBMITTED":
                    abort(409, "Hanya laporan yang sudah dikirim yang dapat diperiksa.")
                outcome = request.form.get("outcome")
                if outcome not in {"VERIFIED", "REJECTED"}:
                    abort(400)
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
                    error=error), 422 if error else 200
