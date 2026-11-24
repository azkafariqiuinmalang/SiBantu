"""Snapshot independen per ronde; laporan terbaru tidak mengubah ronde terkunci."""

import json
from datetime import datetime, timezone

from database import insert_id
from decision_engine import CRITERIA, VERSION


def open_round(db, case_id):
    case = db.execute("SELECT * FROM disaster_cases WHERE id=?", (case_id,)).fetchone()
    if not case:
        raise ValueError("Kejadian tidak ditemukan.")
    existing = db.execute("SELECT id FROM decision_rounds WHERE case_id=? AND finalized_at IS NULL AND algorithm_version=? "
                          "ORDER BY id DESC LIMIT 1", (case_id,VERSION)).fetchone()
    if existing:
        return existing["id"], False
    rows = db.execute("""SELECT d.*, r.id AS report_id,r.version AS report_version,r.status,
                      r.criterion_values,r.observations,r.criteria_version FROM districts d
                      LEFT JOIN field_reports r ON r.id=(SELECT id FROM field_reports
                      WHERE district_id=d.id ORDER BY version DESC LIMIT 1)
                      WHERE d.case_id=? ORDER BY d.district_code""", (case_id,)).fetchall()
    if len(rows) < 2 or any(row["verification_status"] != "APPROVED" or row["status"] != "VERIFIED" for row in rows):
        raise ValueError("Minimal dua kecamatan diperlukan. Semua kecamatan dan laporan terbarunya harus sudah disetujui.")
    if any(row["criteria_version"] != VERSION for row in rows):
        raise ValueError("Perbarui laporan C6 menjadi jarak posko induk ke titik gempa (km), lalu verifikasi sebelum membuka ronde baru.")
    snapshot = dict(case_id=case_id,case_code=case["case_code"],name=case["name"],source=case["information_source"],
                    incident_at=case["incident_at"],is_simulation=bool(case["is_simulation"]),
                    criteria=list(CRITERIA),districts=[])
    for row in rows:
        snapshot["districts"].append(dict(code=row["district_code"],name=row["district_name"],
            values=json.loads(row["criterion_values"]),report_id=row["report_id"],
            report_version=row["report_version"],observations=json.loads(row["observations"])))
    round_id = insert_id(db,"INSERT INTO decision_rounds(case_id,snapshot,locked_at,algorithm_version) VALUES (?,?,?,?)",
                         (case_id,json.dumps(snapshot),datetime.now(timezone.utc).isoformat(timespec="seconds"),VERSION))
    return round_id, True
