"""Demo lokal proses penilaian GDSS."""

import json
import os
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, session, url_for

from decision_engine import CRITERIA, PAIRS, SCALE, VERSION, ahp, borda, demo_snapshot, topsis
from fieldwork import register_fieldwork

ROOT = Path(__file__).resolve().parent
ROLES = {
    "bpbd": "Kepala BPBD",
    "lapangan": "Koordinator Tim Lapangan",
    "sosial": "Perwakilan Dinas Sosial",
}
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
    app = Flask(__name__, instance_path=str(ROOT / "instance"))
    app.secret_key = secrets.token_hex(32)
    app.config["MAX_CONTENT_LENGTH"] = 16_384
    db_path = Path(database or os.environ.get("GDSS_DB_PATH") or ROOT / "instance" / "assessment.sqlite3")
    app.config["DATABASE"] = db_path

    def connect():
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return closing(connection)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db, db:
        db.execute("BEGIN IMMEDIATE")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version > 2:
            raise RuntimeError("Versi database lebih baru dari aplikasi.")
        if version == 0:
            for statement in SCHEMA.split(";"):
                if statement.strip():
                    db.execute(statement)
        if version < 2:
            migration = (ROOT / "migrations" / "002_fieldwork.sql").read_text(encoding="utf-8")
            for statement in migration.split(";"):
                if statement.strip():
                    db.execute(statement)
            db.execute("PRAGMA user_version = 2")
        existing = db.execute("SELECT algorithm_version FROM assessment_round WHERE id = 1").fetchone()
        if existing is None:
            seed = json.loads((ROOT / "examples" / "seed_case.json").read_text(encoding="utf-8"))
            if seed.get("is_simulation") is not True:
                raise ValueError("Demo lokal memerlukan seed berlabel SIMULASI.")
            db.execute(
                "INSERT OR IGNORE INTO assessment_round VALUES (1, ?, ?, ?, NULL, NULL)",
                (json.dumps(demo_snapshot(seed)), now(), VERSION),
            )
        elif existing["algorithm_version"] != VERSION:
            raise RuntimeError("Versi mesin berbeda dari versi ronde yang tersimpan.")

    def round_state(db):
        record = db.execute("SELECT * FROM assessment_round WHERE id = 1").fetchone()
        assessments = {row["role"]: row for row in db.execute("SELECT * FROM assessment")}
        return record, assessments

    def show(role=None, choices=None, preview=None, message=None, status=200,
             section="assessment", form_revision=None):
        with connect() as db, db:
            db.execute("BEGIN")
            record, assessments = round_state(db)
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
        token = session.setdefault("form_token", secrets.token_urlsafe(24))
        return render_template(
            "assessment.html", roles=ROLES, role=role, active=active, assessments=assessments,
            choices=choices, criteria=CRITERIA, pairs=PAIRS, scale=SCALE, record=record,
            snapshot=snapshot, preview=preview, results=results, message=message, token=token,
            group=json.loads(record["group_result"]) if record["group_result"] else [],
            section=section, form_revision=form_revision,
        ), status

    def check_form():
        token = session.get("form_token")
        if not token or not secrets.compare_digest(token.encode(), request.form.get("token", "").encode()):
            abort(400, "Muat ulang halaman dan coba lagi.")

    register_fieldwork(app, connect, check_form)

    @app.get("/")
    def index():
        return redirect(url_for("assessment", role="bpbd"))

    @app.route("/penilaian/<role>", methods=["GET", "POST"])
    def assessment(role):
        if role not in ROLES:
            abort(404)
        if request.method == "GET":
            return show(role)

        check_form()
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
                return show(role, choices, preview, "CR melebihi 0,10. Tinjau ulang perbandingan.", 422,
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
                """INSERT INTO assessment VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(role) DO UPDATE SET choices=excluded.choices,
                revision=excluded.revision, submitted_at=excluded.submitted_at, result=excluded.result""",
                (role, json.dumps(choices), revision + 1, submitted_at,
                 json.dumps(result) if result else None),
            )
            if result and all(key == role or (key in assessments and assessments[key]["submitted_at"])
                              for key in ROLES):
                all_results = [result if key == role else json.loads(assessments[key]["result"]) for key in ROLES]
                rankings = [[row["code"] for row in item["topsis"]["rows"]] for item in all_results]
                db.execute("UPDATE assessment_round SET group_result = ? WHERE id = 1",
                           (json.dumps(borda(districts, rankings)),))
        return redirect(url_for("assessment", role=role), code=303)

    @app.get("/hasil")
    def group_results():
        return show(section="results")

    @app.post("/penilaian/bpbd/finalisasi")
    def finalize():
        check_form()
        with connect() as db, db:
            db.execute("BEGIN IMMEDIATE")
            record, _ = round_state(db)
            if not record["group_result"]:
                return show(section="results", message="Tunggu ketiga penilaian dikirim.", status=409)
            if not record["finalized_at"]:
                db.execute("UPDATE assessment_round SET finalized_at = ? WHERE id = 1", (now(),))
        return redirect(url_for("group_results"), code=303)

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=int(os.environ.get("GDSS_PORT", "5000")))
