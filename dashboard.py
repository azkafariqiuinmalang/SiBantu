import json
from functools import lru_cache
from pathlib import Path

from flask import abort, jsonify, render_template, request, url_for
from auth import ROLES
from decision_engine import CRITERIA, VERSION

DATA_PATH = Path(__file__).resolve().parent / "data" / "malang_raya.geojson"
STATUS_LABELS = {
    "UNREGISTERED": "Belum dicatat",
    "PENDING": "Usulan kecamatan",
    "ASSIGNED": "Menunggu laporan",
    "DRAFT": "Draf laporan",
    "SUBMITTED": "Menunggu verifikasi",
    "REJECTED": "Perlu perbaikan",
    "VERIFIED": "Terverifikasi",
}


@lru_cache(maxsize=1)
def boundaries():
    return json.loads(DATA_PATH.read_text(encoding="utf-8-sig"))


@lru_cache(maxsize=1)
def district_catalog():
    return [feature["properties"] for feature in boundaries()["features"]]


def register_dashboard(app, connect):
    def selected_data():
        with connect() as db, db:
            db.execute("BEGIN")
            cases = [dict(row) for row in db.execute("SELECT * FROM disaster_cases ORDER BY id DESC")]
            raw = request.args.get("case_id")
            try:
                selected = int(raw) if raw else (cases[0]["id"] if cases else None)
            except ValueError:
                abort(400)
            current = next((item for item in cases if item["id"] == selected), None)
            if selected is not None and current is None:
                abort(404)
            districts = [dict(row) for row in db.execute(
                """SELECT d.*,r.status AS report_status,r.criterion_values,r.criteria_version FROM districts d
                LEFT JOIN field_reports r ON r.id=(SELECT id FROM field_reports WHERE district_id=d.id
                ORDER BY version DESC LIMIT 1) WHERE d.case_id=? ORDER BY d.district_name""", (selected,),
            )] if current else []
            decision = db.execute("SELECT * FROM decision_rounds WHERE case_id=? ORDER BY id DESC LIMIT 1",
                                  (selected,)).fetchone() if current else None
            round_info = None
            group = {}
            if decision:
                submitted = {row["role"] for row in db.execute("SELECT role FROM round_assessments "
                             "WHERE round_id=? AND submitted_at IS NOT NULL",(decision["id"],))}
                round_info = dict(id=decision["id"],submitted_count=len(submitted),finalized=bool(decision["finalized_at"]),legacy=decision["algorithm_version"]!=VERSION,
                    actors=[dict(role=role,name=name,submitted=role in submitted) for role,name in ROLES.items()])
                if decision["algorithm_version"]==VERSION:
                    group = {row["code"]:row for row in json.loads(decision["group_result"] or "[]")}
        by_code = {item["district_code"]: item for item in districts}
        features = []
        for original in boundaries()["features"]:
            properties = dict(original["properties"])
            district = by_code.get(properties["code"])
            status = "UNREGISTERED"
            if district:
                status = ("PENDING" if district["verification_status"] == "PENDING"
                          else district["report_status"] or "ASSIGNED")
            values=json.loads(district["criterion_values"]) if district and district["criterion_values"] else None
            requires_update=bool(district and district["criteria_version"] and district["criteria_version"]!=VERSION)
            if values and requires_update:
                values[-1]=None
            properties.update(status=status, status_label=STATUS_LABELS[status],requires_distance_update=requires_update,
                              is_affected=district is not None,
                              criterion_values=values,
                              group_rank=group.get(properties["code"],{}).get("rank"),
                              group_points=group.get(properties["code"],{}).get("total"),
                              case_url=url_for("fieldwork_case", case_id=selected) if selected else None)
            features.append(dict(type="Feature", properties=properties, geometry=original["geometry"]))
        return cases, current, features, districts, round_info

    @app.get("/dashboard")
    def dashboard():
        cases, current, features, districts, round_info = selected_data()
        mapped = [item["properties"] for item in features]
        counts = {
            "registered": sum(item["status"] != "UNREGISTERED" for item in mapped),
            "submitted": sum(item["status"] == "SUBMITTED" for item in mapped),
            "verified": sum(item["status"] == "VERIFIED" for item in mapped),
            "evacuees": sum(item["criterion_values"][0] for item in mapped if item["criterion_values"]),
        }
        mapped_codes = {item["code"] for item in mapped}
        unmapped = [item for item in districts if item["district_code"] not in mapped_codes]
        return render_template("dashboard.html", cases=cases, current_case=current,
                               districts=mapped, counts=counts, unmapped=unmapped, decision_round=round_info,
                               selected_round_id=round_info["id"] if round_info else None,
                               affected=[item for item in mapped if item["is_affected"]])

    @app.get("/api/map")
    def map_data():
        _, current, features, _, round_info = selected_data()
        response = jsonify(type="FeatureCollection", features=features,
                           case_id=current["id"] if current else None,
                           is_simulation=bool(current and current["is_simulation"]),
                           round=round_info,criteria=[dict(code=code,name=name,unit=unit,direction=direction) for code,name,unit,direction in CRITERIA],
                           source="cahyadsn/wilayah_boundaries melalui aaronsanger/idn-geojson")
        response.headers["Cache-Control"] = "private, no-store"
        return response
