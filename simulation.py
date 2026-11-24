"""Contoh Malang Raya yang eksplisit fiktif, idempoten, tanpa penilaian aktor otomatis."""

import json
from datetime import datetime, timezone
from pathlib import Path

import click

from dashboard import district_catalog
from database import insert_id
from decision_engine import VERSION, demo_snapshot
from fieldwork import FIELDS, read_observations, time_field
from rounds import open_round

SIMULATION_PATH = Path(__file__).resolve().parent / "examples" / "malang_raya_simulation.json"


def simulation_data():
    data = json.loads(SIMULATION_PATH.read_text(encoding="utf-8"))
    if data.get("is_simulation") is not True:
        raise ValueError("Contoh ini harus ditandai SIMULASI.")
    catalog = {item["code"]:item["name"] for item in district_catalog()}
    for district in data["districts"]:
        if catalog.get(district["code"]) != district["name"]:
            raise ValueError("Kode dan nama kecamatan tidak cocok dengan katalog peta.")
    demo_snapshot(data)
    return data


def seed_simulation(db):
    data = simulation_data()
    existing = db.execute("SELECT * FROM disaster_cases WHERE case_code=?", (data["case_code"],)).fetchone()
    if existing:
        if not existing["is_simulation"]:
            raise ValueError("Kode simulasi sudah digunakan oleh kejadian lain.")
        previous = db.execute("SELECT id,algorithm_version FROM decision_rounds WHERE case_id=? ORDER BY id DESC LIMIT 1",
                              (existing["id"],)).fetchone()
        if previous and previous["algorithm_version"] != VERSION:
            upgrade_distance_simulation(db,existing,data)
            return existing["id"],open_round(db,existing["id"])[0],True
        round_id = previous["id"] if previous else open_round(db,existing["id"])[0]
        return existing["id"],round_id,False
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    incident = time_field(data["incident_at"],"Waktu kejadian")
    case_id = insert_id(db,"""INSERT INTO disaster_cases(case_code,name,incident_at,province,regency,
                        information_source,is_simulation,created_at) VALUES (?,?,?,?,?,?,?,?)""",
                        (data["case_code"],data["name"],incident,data["province"],data["regency"],data["information_source"],1,now))

    def audit(action, entity, entity_id):
        db.execute("INSERT INTO fieldwork_audit(actor_id,action,entity_type,entity_id,created_at) VALUES (?,?,?,?,?)",
                   ("simulation",action,entity,entity_id,now))

    audit("SEED_SIMULATION","disaster_case",case_id)
    for item, derived in zip(data["districts"],demo_snapshot(data)["districts"]):
        district_id = insert_id(db,"""INSERT INTO districts(case_id,district_code,district_name,verification_status,proposed_by)
                                VALUES (?,?,?,'APPROVED','simulation')""",(case_id,item["code"],item["name"]))
        assignment_id = insert_id(db,"INSERT INTO assignments(district_id,officer_id,assigned_at) VALUES (?,'lapangan',?)",(district_id,now))
        audit("SEED_SIMULATION","district",district_id)
        audit("SEED_SIMULATION","assignment",assignment_id)
        raw = {key:str(item[key]) for key,*_ in FIELDS}
        raw.update(observed_at=data["observed_at"],source_note=data["information_source"])
        observations = read_observations(raw,incident,True)
        report_id = insert_id(db,"""INSERT INTO field_reports(assignment_id,district_id,version,revision,status,
                              observations,criterion_values,created_at,submitted_at,criteria_version) VALUES (?,?,1,1,'VERIFIED',?,?,?,?,?)""",
                              (assignment_id,district_id,json.dumps(observations),json.dumps(derived["values"]),now,now,VERSION))
        db.execute("INSERT INTO field_report_reviews(report_id,reviewer_id,outcome,note,reviewed_at) "
                   "VALUES (?,'simulation','VERIFIED',?,?)",
                   (report_id,"Verifikasi otomatis khusus data SIMULASI, bukan pemeriksaan lapangan nyata.",now))
        audit("SEED_SIMULATION","field_report",report_id)
    round_id,_ = open_round(db,case_id)
    audit("OPEN_ROUND","decision_round",round_id)
    return case_id,round_id,True


def upgrade_distance_simulation(db,case,data):
    """Hanya memperbarui C6 kasus contoh milik aplikasi, sebagai versi laporan baru."""
    now=datetime.now(timezone.utc).isoformat(timespec="seconds")
    for item in data["districts"]:
        latest=db.execute("""SELECT r.* FROM field_reports r JOIN districts d ON d.id=r.district_id
                          WHERE d.case_id=? AND d.district_code=? ORDER BY r.version DESC LIMIT 1""",
                          (case["id"],item["code"])).fetchone()
        if latest and latest["criteria_version"]==VERSION:
            continue
        if not latest or latest["status"] not in {"VERIFIED","REJECTED"}:
            raise ValueError("Selesaikan laporan aktif sebelum memperbarui C6 simulasi.")
        observations=json.loads(latest["observations"])
        observations.pop("hours_since_last_delivery",None)
        observations["distance_to_epicenter_km"]=item["distance_to_epicenter_km"]
        observations["source_note"]="SIMULASI: nilai C6 jarak fiktif untuk latihan. Angka jam versi sebelumnya tidak dikonversi."
        values=json.loads(latest["criterion_values"])
        values[-1]=item["distance_to_epicenter_km"]
        report_id=insert_id(db,"""INSERT INTO field_reports(assignment_id,district_id,version,revision,status,
                           observations,criterion_values,created_at,submitted_at,criteria_version)
                           VALUES (?,?,?,1,'VERIFIED',?,?,?,?,?)""",
                           (latest["assignment_id"],latest["district_id"],latest["version"]+1,
                            json.dumps(observations),json.dumps(values),now,now,VERSION))
        db.execute("INSERT INTO field_report_reviews VALUES (?,'simulation','VERIFIED',?,?)",
                   (report_id,"Verifikasi otomatis khusus pembaruan C6 SIMULASI.",now))
        db.execute("INSERT INTO fieldwork_audit(actor_id,action,entity_type,entity_id,created_at) VALUES ('simulation','UPGRADE_C6','field_report',?,?)",
                   (report_id,now))


def register_simulation(app,connect):
    @app.cli.command("seed-malang-simulation")
    def seed_command():
        """Buat empat wilayah simulasi dan ronde baru, tanpa menimpa data/hasil lama."""
        with connect() as db, db:
            db.execute("BEGIN IMMEDIATE")
            case_id,round_id,created = seed_simulation(db)
        click.echo(f"Simulasi {'dibuat' if created else 'sudah tersedia'}: kejadian {case_id}, ronde {round_id}.")
        click.echo("Empat kecamatan siap dinilai. Penilaian ketiga aktor tidak diisi otomatis.")
