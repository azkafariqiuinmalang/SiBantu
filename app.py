"""Demo lokal proses penilaian GDSS."""

import json
import os
import secrets
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, session, url_for

from decision_engine import CRITERIA, PAIRS, SCALE, VERSION, SUPPORTED_VERSIONS, criteria_for_version, ahp, borda, inconsistency_hints, demo_snapshot, topsis
from fieldwork import register_fieldwork
from auth import ROLES, register_auth, require_role
from database import PostgresConnection, load_environment, migrate, sqlite_connection

ROOT = Path(__file__).resolve().parent
SCHEMA = """
CREATE TABLE IF NOT EXISTS assessment_round (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    snapshot TEXT NOT NULL,
    locked_at TEXT NOT NULL,
    algorithm_version TEXT NOT NULL,
    group_result TEXT,
    finalized_at TEXT
);
CREATE TABLE IF NOT EXISTS assessment (
    role TEXT PRIMARY KEY,
    choices TEXT NOT NULL,
    revision INTEGER NOT NULL,
    submitted_at TEXT,
    result TEXT
);
"""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_app(database=None):
    load_environment(ROOT)
    app = Flask(__name__, instance_path=str(ROOT / "instance"))
    secret_path = ROOT / "instance" / "session.key"
    secret_path.parent.mkdir(parents=True, exist_ok=True)
    if not secret_path.exists():
        try:
            with secret_path.open("x", encoding="utf-8") as file:
                file.write(secrets.token_hex(32))
        except FileExistsError:
            pass
    app.secret_key = os.environ.get("SECRET_KEY") or secret_path.read_text(encoding="utf-8").strip()
    app.config["MAX_CONTENT_LENGTH"] = 16_384
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE") == "1"
    supabase_url = "" if database is not None else os.environ.get("SUPABASE_DB_URL", "").strip()
    if supabase_url and not supabase_url.startswith(("postgresql://", "postgres://")):
        raise RuntimeError("SUPABASE_DB_URL harus berupa URI PostgreSQL dari panel Connect Supabase.")
    db_path = Path(database or os.environ.get("GDSS_DB_PATH") or ROOT / "instance" / "assessment.sqlite3")
    app.config["DATABASE"] = db_path
    app.config["DATABASE_BACKEND"] = "supabase" if supabase_url else "sqlite"

    def connect():
        return closing(PostgresConnection(supabase_url) if supabase_url else sqlite_connection(db_path))

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db, db:
        migrate(db, ROOT, SCHEMA)
        existing = db.execute("SELECT algorithm_version FROM assessment_round WHERE id = 1").fetchone()
        if existing is None:
            seed = json.loads((ROOT / "examples" / "seed_case.json").read_text(encoding="utf-8"))
            if seed.get("is_simulation") is not True:
                raise ValueError("Demo lokal memerlukan seed berlabel SIMULASI.")
            db.execute(
                "INSERT INTO assessment_round VALUES (1, ?, ?, ?, NULL, NULL) ON CONFLICT(id) DO NOTHING",
                (json.dumps(demo_snapshot(seed)), now(), VERSION),
            )
        elif existing["algorithm_version"] not in SUPPORTED_VERSIONS:
            raise RuntimeError("Versi mesin berbeda dari versi ronde yang tersimpan.")
        if db.execute("SELECT id FROM decision_rounds LIMIT 1").fetchone() is None:
            db.execute("""INSERT INTO decision_rounds(case_id,snapshot,locked_at,algorithm_version,group_result,finalized_at)
                       SELECT NULL,snapshot,locked_at,algorithm_version,group_result,finalized_at FROM assessment_round""")

    def round_state(db):
        raw = request.args.get("round_id")
        if raw is None and request.method == "POST":
            raw = request.form.get("round_id")
        if raw is None:
            record = db.execute("SELECT * FROM decision_rounds ORDER BY id DESC LIMIT 1").fetchone()
        else:
            try:
                selected = int(raw)
            except ValueError:
                abort(400)
            record = db.execute("SELECT * FROM decision_rounds WHERE id=?",(selected,)).fetchone()
        if record is None:
            abort(404)
        assessments = {row["role"]: row for row in db.execute("SELECT * FROM round_assessments WHERE round_id=?",(record["id"],))}
        return record, assessments

    def show(role=None, choices=None, preview=None, message=None, status=200,
             section="assessment", form_revision=None):
        with connect() as db, db:
            db.execute("BEGIN")
            record, assessments = round_state(db)
            rounds = [dict(id=row["id"],name=json.loads(row["snapshot"])["name"]) for row in
                      db.execute("SELECT id,snapshot FROM decision_rounds ORDER BY id DESC")]
        snapshot = json.loads(record["snapshot"])
        active = assessments.get(role)
        if choices is None or (active and active["submitted_at"]):
            choices = json.loads(active["choices"]) if active else [""] * len(PAIRS)
        results = {
            key: json.loads(row["result"])
            for key, row in assessments.items() if row["submitted_at"]
        }
        if active and active["submitted_at"]:
            preview = json.loads(active["result"])["ahp"]
        hints = []
        if preview and not preview["valid"] and all(choice in SCALE for choice in choices):
            hints = inconsistency_hints(choices)
        token = session.setdefault("form_token", secrets.token_urlsafe(24))
        return render_template(
            "assessment.html", roles=ROLES, role=role, active=active, assessments=assessments,
            choices=choices, criteria=snapshot.get("criteria",criteria_for_version(record["algorithm_version"])), pairs=PAIRS, scale=SCALE, record=record,
            snapshot=snapshot, preview=preview, results=results, message=message, token=token,
            group=json.loads(record["group_result"]) if record["group_result"] else [],
            section=section, form_revision=form_revision, rounds=rounds, selected_round_id=record["id"],
            is_legacy=record["algorithm_version"] != VERSION, hints=hints,
        ), status

    def check_form():
        token = session.get("form_token")
        if not token or not secrets.compare_digest(token.encode(), request.form.get("token", "").encode()):
            abort(400, "Muat ulang halaman dan coba lagi.")

    register_auth(app, connect, check_form)
    from accounts import register_accounts
    register_accounts(app, connect, check_form)
    register_fieldwork(app, connect, check_form)
    from dashboard import register_dashboard
    register_dashboard(app, connect)
    from simulation import register_simulation
    register_simulation(app,connect)

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(409)
    @app.errorhandler(413)
    @app.errorhandler(500)
    def error_page(error):
        messages = {
            400: ("Permintaan belum sesuai", "Muat ulang halaman, kemudian coba kembali."),
            403: ("Akses dibatasi", "Halaman atau tindakan ini belum tersedia untuk peran Anda."),
            404: ("Halaman tidak ditemukan", "Periksa kembali tautan atau pilih menu yang tersedia."),
            409: ("Data telah berubah", "Muat ulang halaman untuk melihat status terbaru."),
            413: ("Data terlalu besar", "Kurangi isi formulir lalu kirim kembali."),
            500: ("Halaman belum dapat dimuat", "Terjadi kendala pada server. Coba kembali beberapa saat lagi."),
        }
        title, message = messages[error.code]
        if error.code != 500 and error.description != type(error).description:
            message = error.description
        return render_template("error.html", title=title, message=message), error.code

    @app.get("/")
    def index():
        return redirect(url_for("dashboard"))

    @app.route("/penilaian/<role>", methods=["GET", "POST"])
    def assessment(role):
        if role not in ROLES:
            abort(404)
        require_role(role)
        if request.method == "GET":
            return show(role)

        require_role(role)
        check_form()
        with connect() as db:
            selected_record,_ = round_state(db)
        if selected_record["algorithm_version"] != VERSION:
            return show(role,message="Ronde ini merupakan arsip dengan C6 lama. Gunakan ronde terbaru dengan jarak C6 dalam kilometer.",status=409)
        if request.form.get("round_id") != str(selected_record["id"]):
            return show(role,message="Muat ulang halaman agar penilaian terhubung ke ronde yang dipilih.",status=409)
        action = request.form.get("action")
        if action not in {"draft", "preview", "submit"}:
            abort(400)
        choices = [request.form.get(f"pair_{index}", "") for index in range(len(PAIRS))]
        form_revision = request.form.get("revision", "")
        if any(choice and choice not in SCALE for choice in choices):
            return show(role, choices, message="Gunakan pilihan dari skala Saaty yang tersedia.",
                        status=422, form_revision=form_revision)
        if action == "preview":
            try:
                return show(role, choices, preview=ahp(choices), form_revision=form_revision)
            except ValueError as error:
                return show(role, choices, message=str(error), status=422, form_revision=form_revision)

        preview = None
        if action == "submit":
            try:
                preview = ahp(choices)
            except ValueError as error:
                return show(role, choices, message=str(error), status=422, form_revision=form_revision)
            if not preview["valid"]:
                return show(role, choices, preview, "CR melebihi 0,10. Tinjau ulang perbandingan; lihat saran pasangan pada panel Konsistensi AHP.", 422,
                            form_revision=form_revision)

        with connect() as db, db:
            db.execute("BEGIN IMMEDIATE")
            record, assessments = round_state(db)
            current = assessments.get(role)
            revision = current["revision"] if current else 0
            if record["finalized_at"] or (current and current["submitted_at"]):
                return show(role, message="Penilaian sudah terkunci.", status=409)
            if form_revision != str(revision):
                return show(role, message="Penilaian berubah di tab lain. Form telah dimuat ulang.", status=409)
            result = None
            submitted_at = None
            if action == "submit":
                districts = json.loads(record["snapshot"])["districts"]
                result = dict(ahp=preview, topsis=topsis(districts, preview["weights"]))
                submitted_at = now()
            db.execute(
                """INSERT INTO round_assessments(round_id,role,choices,revision,submitted_at,result) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(round_id,role) DO UPDATE SET choices=excluded.choices,
                revision=excluded.revision, submitted_at=excluded.submitted_at, result=excluded.result""",
                (record["id"], role, json.dumps(choices), revision + 1, submitted_at,
                 json.dumps(result) if result else None),
            )
            if result and all(key == role or (key in assessments and assessments[key]["submitted_at"])
                              for key in ROLES):
                all_results = [result if key == role else json.loads(assessments[key]["result"]) for key in ROLES]
                rankings = [[row["code"] for row in item["topsis"]["rows"]] for item in all_results]
                db.execute("UPDATE decision_rounds SET group_result = ? WHERE id = ?",
                           (json.dumps(borda(districts, rankings)),record["id"]))
        return redirect(url_for("assessment", role=role,round_id=record["id"]), code=303)

    @app.get("/hasil")
    def group_results():
        return show(section="results")

    @app.post("/penilaian/bpbd/finalisasi")
    def finalize():
        require_role("bpbd")
        check_form()
        with connect() as db, db:
            db.execute("BEGIN IMMEDIATE")
            record, _ = round_state(db)
            if record["algorithm_version"] != VERSION:
                abort(409,"Ronde ini merupakan arsip baca-saja dengan definisi kriteria sebelumnya.")
            if request.form.get("round_id") != str(record["id"]):
                abort(409,"Muat ulang halaman sebelum mengesahkan ronde ini.")
            if not record["group_result"]:
                return show(section="results", message="Tunggu ketiga penilaian dikirim.", status=409)
            if not record["finalized_at"]:
                db.execute("UPDATE decision_rounds SET finalized_at = ? WHERE id = ?", (now(),record["id"]))
        return redirect(url_for("group_results",round_id=record["id"]), code=303)

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=int(os.environ.get("GDSS_PORT", "5000")))
