import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from fractions import Fraction
from pathlib import Path

from app import ROOT, SCHEMA, create_app
from decision_engine import PAIRS, VERSION, demo_snapshot
from simulation import simulation_data
from support import login, seed_users


class SimulationTest(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database=Path(temporary.name)/"simulation.sqlite3"
        self.app=create_app(self.database)
        seed_users(self.database)
        self.client=self.app.test_client()
        result=self.app.test_cli_runner().invoke(args=["seed-malang-simulation"])
        self.assertEqual(result.exit_code,0,result.output)
        with closing(sqlite3.connect(self.database)) as db:
            self.case_id=db.execute("SELECT id FROM disaster_cases WHERE case_code='GB-SIM-MLG-001'").fetchone()[0]
            self.round_id=db.execute("SELECT id FROM decision_rounds WHERE case_id=?",(self.case_id,)).fetchone()[0]
        self.token=login(self.client,"bpbd")

    def map(self):
        return self.client.get(f"/api/map?case_id={self.case_id}").json

    def submit(self,role,weights):
        self.token=login(self.client,role)
        choices=[str(Fraction(weights[i],weights[j])) for i,j in PAIRS]
        response=self.client.post(f"/penilaian/{role}?round_id={self.round_id}",data=dict(
            token=self.token,round_id=str(self.round_id),revision="0",action="submit",
            **{f"pair_{i}":choice for i,choice in enumerate(choices)}))
        self.assertEqual(response.status_code,303,response.data[-500:])

    def test_real_district_catalog_and_empty_actor_assessments(self):
        data=self.map()
        affected=[feature["properties"] for feature in data["features"] if feature["properties"]["is_affected"]]
        self.assertEqual({row["name"] for row in affected},{"Gedangan","Sumbermanjing Wetan","Dampit","Tirtoyudo"})
        self.assertEqual(len(data["features"]),41)
        self.assertTrue(data["is_simulation"])
        self.assertEqual(data["round"]["submitted_count"],0)
        self.assertTrue(all(row["status"]=="VERIFIED" and len(row["criterion_values"])==6 and row["group_rank"] is None for row in affected))
        self.assertEqual(sum(row["criterion_values"][0] for row in affected),6750)
        page=self.client.get("/dashboard")
        self.assertIn(b"4 kecamatan tercatat terdampak",page.data)
        self.assertIn(b"0/3 aktor",page.data)
        self.assertIn(b'option value="priority" disabled',page.data)
        for role in ("bpbd","lapangan","sosial"):
            login(self.client,role)
            page=self.client.get(f"/penilaian/{role}")
            self.assertEqual(page.status_code,200)
            self.assertIn(b"4 kecamatan",page.data)
            self.assertIn(f'name="round_id" value="{self.round_id}"'.encode(),page.data)
            self.assertEqual(page.data.count(b'<select name="pair_'),15)
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM round_assessments WHERE round_id=?",(self.round_id,)).fetchone()[0],0)

    def test_three_actor_assessments_produce_map_priorities_and_idempotent_seed(self):
        self.submit("bpbd",[1,3,1,1,1,1])
        self.assertEqual(self.map()["round"]["submitted_count"],1)
        self.assertTrue(all(f["properties"]["group_rank"] is None for f in self.map()["features"]))
        result=self.app.test_cli_runner().invoke(args=["seed-malang-simulation"])
        self.assertEqual(result.exit_code,0,result.output)
        self.assertEqual(self.map()["round"]["submitted_count"],1)
        self.submit("lapangan",[1,1,1,2,1,2])
        self.assertEqual(self.map()["round"]["submitted_count"],2)
        self.submit("sosial",[2,1,2,1,1,1])
        data=self.map()
        affected=[f["properties"] for f in data["features"] if f["properties"]["is_affected"]]
        self.assertEqual(data["round"]["submitted_count"],3)
        self.assertEqual({row["group_rank"] for row in affected},{1,2,3,4})
        self.assertEqual(sum(row["group_points"] for row in affected),30)
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM disaster_cases").fetchone()[0],1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM field_reports").fetchone()[0],4)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM assessment").fetchone()[0],0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM round_assessments WHERE round_id=?",(self.round_id,)).fetchone()[0],3)

    def test_locked_round_preserves_reports_and_new_round_requires_verification(self):
        for role in ("bpbd","lapangan","sosial"):
            self.submit(role,[1,1,1,1,1,1])
        self.token=login(self.client,"bpbd")
        self.assertEqual(self.client.post("/penilaian/bpbd/finalisasi",data=dict(token=self.token,round_id=self.round_id)).status_code,303)
        with closing(sqlite3.connect(self.database)) as db:
            frozen=db.execute("SELECT snapshot,group_result FROM decision_rounds WHERE id=?",(self.round_id,)).fetchone()
            assignment_id=db.execute("SELECT a.id FROM assignments a JOIN districts d ON d.id=a.district_id "
                "WHERE d.case_id=? AND d.district_code='35.07.29'",(self.case_id,)).fetchone()[0]
            report_id=db.execute("SELECT id FROM field_reports WHERE assignment_id=?",(assignment_id,)).fetchone()[0]
        self.token=login(self.client,"lapangan")
        raw=next(row for row in simulation_data()["districts"] if row["name"]=="Gedangan")
        data={key:value for key,value in raw.items() if key not in {"code","name"}}
        data.update(evacuees=2000,token=self.token,stamp=f"{report_id}:1",action="submit",
                    observed_at="2026-11-20T15:00+07:00",source_note="Revisi SIMULASI")
        self.assertEqual(self.client.post(f"/pendataan/tugas/{assignment_id}",data=data).status_code,303)
        self.token=login(self.client,"bpbd")
        self.assertEqual(self.client.post(f"/pendataan/kejadian/{self.case_id}",data=dict(token=self.token,action="open_round")).status_code,422)
        with closing(sqlite3.connect(self.database)) as db:
            new_report=db.execute("SELECT id FROM field_reports WHERE assignment_id=? ORDER BY version DESC",(assignment_id,)).fetchone()[0]
            self.assertEqual(db.execute("SELECT snapshot,group_result FROM decision_rounds WHERE id=?",(self.round_id,)).fetchone(),frozen)
        self.assertEqual(self.client.post(f"/pendataan/laporan/{new_report}",data=dict(token=self.token,outcome="VERIFIED")).status_code,303)
        self.assertEqual(self.client.post(f"/pendataan/kejadian/{self.case_id}",data=dict(token=self.token,action="open_round")).status_code,303)
        self.assertEqual(self.map()["round"]["submitted_count"],0)
        with closing(sqlite3.connect(self.database)) as db:
            latest=json.loads(db.execute("SELECT snapshot FROM decision_rounds WHERE case_id=? ORDER BY id DESC",(self.case_id,)).fetchone()[0])
            self.assertEqual(next(d["values"][0] for d in latest["districts"] if d["name"]=="Gedangan"),2000)
            self.assertEqual(db.execute("SELECT snapshot,group_result FROM decision_rounds WHERE id=?",(self.round_id,)).fetchone(),frozen)

    def test_round_form_identity_and_history_access(self):
        self.assertEqual(self.client.post("/penilaian/bpbd",data=dict(token=self.token,action="draft",revision="0")).status_code,409)
        self.assertEqual(self.client.post(f"/penilaian/bpbd?round_id={self.round_id}",data=dict(token=self.token,round_id="1",action="draft",revision="0")).status_code,409)
        self.assertEqual(self.client.get("/penilaian/bpbd?round_id=9999").status_code,404)
        self.assertEqual(self.client.get("/penilaian/bpbd?round_id=bad").status_code,400)
        self.assertEqual(self.client.get("/penilaian/bpbd?round_id=1").status_code,200)

    def test_legacy_round_and_assessments_are_copied_without_mutation(self):
        path=self.database.with_name("legacy-v4.sqlite3")
        snapshot=json.dumps(demo_snapshot(json.loads((ROOT/"examples"/"seed_case.json").read_text())))
        with closing(sqlite3.connect(path)) as db,db:
            db.executescript(SCHEMA)
            for name in ("002_fieldwork.sql","003_auth.sql","004_accounts.sql"):
                db.executescript((ROOT/"migrations"/name).read_text())
            db.execute("PRAGMA user_version=4")
            db.execute("INSERT INTO assessment_round VALUES (1,?,'original',?,'[]','final')",(snapshot,VERSION))
            db.execute("INSERT INTO assessment VALUES ('bpbd','[]',3,'sent','{}')")
        create_app(path)
        with closing(sqlite3.connect(path)) as db:
            self.assertEqual(db.execute("SELECT snapshot,locked_at,finalized_at FROM decision_rounds").fetchone(),(snapshot,"original","final"))
            self.assertEqual(db.execute("SELECT role,choices,revision,submitted_at,result FROM round_assessments").fetchone(),("bpbd","[]",3,"sent","{}"))
            self.assertEqual(db.execute("SELECT snapshot FROM assessment_round").fetchone()[0],snapshot)
