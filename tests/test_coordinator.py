import json
import re
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app import ROOT, SCHEMA, create_app
from decision_engine import CRITERIA, LEGACY_CRITERIA, VERSION, topsis
from simulation import simulation_data
from support import login,seed_users


class CoordinatorTest(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database=Path(temporary.name)/"coordinator.sqlite3"
        self.app=create_app(self.database)
        seed_users(self.database)
        result=self.app.test_cli_runner().invoke(args=["seed-malang-simulation"])
        self.assertEqual(result.exit_code,0,result.output)
        self.client=self.app.test_client()
        self.token=login(self.client,"lapangan")
        with closing(sqlite3.connect(self.database)) as db:
            self.assignment,self.report=db.execute("SELECT assignment_id,id FROM field_reports ORDER BY id LIMIT 1").fetchone()

    def data(self):
        item=simulation_data()["districts"][0]
        result={key:value for key,value in item.items() if key not in {"code","name"}}
        result.update(token=self.token,action="submit",stamp=f"{self.report}:1",observed_at="2026-11-20T15:45",source_note="Survei simulasi")
        return result

    def test_coordinator_home_only_contains_tasks(self):
        page=self.client.get("/pendataan")
        self.assertEqual(page.status_code,200)
        self.assertIn(b"Tugas saya",page.data)
        self.assertIn(b'data-task',page.data)
        self.assertNotIn(b"Daftar kejadian",page.data)
        self.assertNotIn(b"Daftarkan kejadian",page.data)
        self.assertEqual(self.client.post("/pendataan/kejadian",data=dict(token=self.token)).status_code,403)
        login(self.client,"bpbd")
        self.assertIn(b"Daftar kejadian",self.client.get("/pendataan").data)

    def test_observation_calendar_wib_and_distance_are_saved(self):
        page=self.client.get(f"/pendataan/tugas/{self.assignment}")
        self.assertEqual(page.status_code,200)
        self.assertRegex(page.data,rb'id="observed_at"[^>]*type="datetime-local"')
        self.assertIn(b'value="2026-11-20T14:00"',page.data)
        self.assertIn(b'name="distance_to_epicenter_km"',page.data)
        self.assertNotIn(b'name="hours_since_last_delivery"',page.data)
        data=self.data(); data["distance_to_epicenter_km"]="12.5"
        self.assertEqual(self.client.post(f"/pendataan/tugas/{self.assignment}",data=data).status_code,303)
        with closing(sqlite3.connect(self.database)) as db:
            observations,values,version=db.execute("SELECT observations,criterion_values,criteria_version FROM field_reports ORDER BY id DESC LIMIT 1").fetchone()
            self.assertEqual(json.loads(observations)["observed_at"],"2026-11-20T08:45:00+00:00")
            self.assertEqual(json.loads(values)[5],12.5)
            self.assertEqual(version,VERSION)
            self.assertNotIn("hours_since_last_delivery",json.loads(observations))

    def test_invalid_distance_or_observation_is_rejected_and_preserves_fields(self):
        for key,value in [("distance_to_epicenter_km",""),("distance_to_epicenter_km","-1"),("distance_to_epicenter_km","nan"),("distance_to_epicenter_km","inf"),("observed_at","2999-01-01T12:00"),("observed_at","2020-01-01T12:00")]:
            with self.subTest(key=key,value=value):
                data=self.data(); data[key]=value
                response=self.client.post(f"/pendataan/tugas/{self.assignment}",data=data)
                self.assertEqual(response.status_code,422)
                self.assertIn(f'href="#{key}"'.encode(),response.data)
                self.assertIn(b"Survei simulasi",response.data)
        data=self.data(); data.pop("distance_to_epicenter_km"); data["hours_since_last_delivery"]="40"
        self.assertEqual(self.client.post(f"/pendataan/tugas/{self.assignment}",data=data).status_code,422)
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM field_reports").fetchone()[0],4)

    def test_partial_draft_and_c6_benefit(self):
        response=self.client.post(f"/pendataan/tugas/{self.assignment}",data=dict(token=self.token,action="draft",stamp=f"{self.report}:1",source_note="Draf"))
        self.assertEqual(response.status_code,303)
        with closing(sqlite3.connect(self.database)) as db:
            observations,status=db.execute("SELECT observations,status FROM field_reports ORDER BY id DESC LIMIT 1").fetchone()
            self.assertIsNone(json.loads(observations)["distance_to_epicenter_km"])
            self.assertEqual(status,"DRAFT")
        self.assertEqual(CRITERIA[-1],("C6","Jarak posko induk ke titik gempa","km","benefit"))
        rows=topsis([dict(code="near",name="near",values=[10,3,20,3,40,10]),dict(code="far",name="far",values=[10,3,20,3,40,100])],[1/6]*6)["rows"]
        self.assertEqual(rows[0]["code"],"far")

    def test_legacy_hours_are_archived_and_simulation_upgrade_creates_new_versions(self):
        originals={}
        with closing(sqlite3.connect(self.database)) as db,db:
            rows=db.execute("SELECT id,observations,criterion_values FROM field_reports").fetchall()
            for report_id,observations,values in rows:
                observed=json.loads(observations); observed.pop("distance_to_epicenter_km"); observed["hours_since_last_delivery"]=48
                criteria=json.loads(values); criteria[5]=48
                observed=json.dumps(observed); criteria=json.dumps(criteria)
                db.execute("UPDATE field_reports SET observations=?,criterion_values=?,criteria_version='1.0' WHERE id=?",(observed,criteria,report_id))
                originals[report_id]=(observed,criteria)
            round_id,snapshot=db.execute("SELECT id,snapshot FROM decision_rounds WHERE case_id=1").fetchone()
            snapshot=json.loads(snapshot); snapshot["criteria"]=list(LEGACY_CRITERIA)
            snapshot=json.dumps(snapshot)
            db.execute("UPDATE decision_rounds SET algorithm_version='1.0',snapshot=? WHERE id=?",(snapshot,round_id))
        page=self.client.get(f"/pendataan/tugas/{self.assignment}")
        self.assertNotIn(b'name="hours_since_last_delivery"',page.data)
        self.assertRegex(page.data,rb'id="distance_to_epicenter_km"[^>]*value=""')
        data=self.client.get("/api/map?case_id=1").json
        self.assertTrue(all(feature["properties"]["criterion_values"][5] is None for feature in data["features"] if feature["properties"]["is_affected"]))
        result=self.app.test_cli_runner().invoke(args=["seed-malang-simulation"])
        self.assertEqual(result.exit_code,0,result.output)
        result=self.app.test_cli_runner().invoke(args=["seed-malang-simulation"])
        self.assertEqual(result.exit_code,0,result.output)
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM field_reports").fetchone()[0],8)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM decision_rounds WHERE case_id=1 AND algorithm_version=?",(VERSION,)).fetchone()[0],1)
            self.assertEqual(db.execute("SELECT snapshot FROM decision_rounds WHERE id=?",(round_id,)).fetchone()[0],snapshot)
            for report_id,old in originals.items():
                self.assertEqual(db.execute("SELECT observations,criterion_values FROM field_reports WHERE id=?",(report_id,)).fetchone(),old)
        self.assertEqual(self.client.post(f"/penilaian/lapangan?round_id={round_id}",data=dict(token=self.token,round_id=round_id,action="draft",revision="0")).status_code,409)

    def test_version_five_upgrade_does_not_reinterpret_old_hours(self):
        path=self.database.with_name("legacy-v5.sqlite3")
        old=json.dumps(dict(hours_since_last_delivery=48))
        with closing(sqlite3.connect(path)) as db,db:
            db.executescript(SCHEMA)
            for name in ("002_fieldwork.sql","003_auth.sql","004_accounts.sql","005_decision_rounds.sql"):
                db.executescript((ROOT/"migrations"/name).read_text(encoding="utf-8"))
            db.execute("PRAGMA user_version=5")
            db.execute("INSERT INTO disaster_cases VALUES (1,'OLD','Lama','2025-01-01','Jawa Timur','Malang Raya',NULL,'Simulasi',1,'original')")
            db.execute("INSERT INTO districts(case_id,district_code,district_name) VALUES (1,'35.07.29','Gedangan')")
            db.execute("INSERT INTO assignments(district_id,officer_id,assigned_at) VALUES (1,'lapangan','original')")
            db.execute("INSERT INTO field_reports(assignment_id,district_id,version,status,observations,criterion_values,created_at) VALUES (1,1,1,'VERIFIED',?,'[10,3,20,3,40,48]','original')",(old,))
        create_app(path)
        with closing(sqlite3.connect(path)) as db:
            self.assertEqual(db.execute("SELECT observations,criteria_version,criterion_values FROM field_reports").fetchone(),(old,"1.0","[10,3,20,3,40,48]"))
