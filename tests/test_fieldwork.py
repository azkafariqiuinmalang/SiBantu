import json
import re
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app import ROOT, SCHEMA, create_app


class FieldworkTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "assessment.sqlite3"
        self.client = create_app(self.database).test_client()
        page = self.client.get("/pendataan")
        self.assertEqual(page.status_code, 200)
        self.token = re.search(rb'name="token" value="([^"]+)"', page.data)[1].decode()

    def post(self, path, expected=303, **data):
        response = self.client.post("/pendataan" + path, data={"token": self.token, **data})
        self.assertEqual(response.status_code, expected, response.data[-1000:])
        return response

    def as_role(self, role):
        self.post("/peran", actor=role)

    def stamp(self, task_id):
        page = self.client.get(f"/pendataan/tugas/{task_id}")
        self.assertEqual(page.status_code, 200)
        return re.search(rb'name="stamp" value="([^"]+)"', page.data)[1].decode()

    def test_two_districts_reject_revise_verify(self):
        case = dict(case_code="sim-1", name="Gempa X", incident_at="2025-01-01T08:00+07:00",
                    province="Jawa Timur", regency="Kabupaten X",
                    information_source="Simulasi UAS", is_simulation="1")
        self.post("/kejadian", 403, **case)
        self.as_role("admin")
        self.post("/kejadian", 422, **dict(case, incident_at="2999-01-01T08:00+07:00"))
        self.post("/kejadian", **case)
        self.post("/kejadian", 409, **dict(case, case_code="SIM-1"))
        for number in (1, 2):
            self.post("/kejadian/1", action="district", district_code=f"A{number}",
                      district_name=f"Kecamatan {number}")
            self.post("/kejadian/1", action="assign", district_id=number, officer_id="petugas-1")
        self.post("/kejadian/1", 409, action="district", district_code="a1", district_name="Ganda")

        observations = dict(observed_at="2025-01-01T12:00+07:00", source_note="Catatan posko",
                            evacuees=20, vulnerable_people=5, housing_damage_score=3,
                            essential_services_disruption_score=2, available_package_equivalents=10,
                            required_package_equivalents=25, hours_since_last_delivery=4)
        self.as_role("petugas-2")
        self.post("/tugas/1", 403, action="submit", stamp="0", **observations)
        self.as_role("petugas-1")
        self.post("/tugas/1", action="draft", stamp="0", source_note="Catatan awal")
        stamp = self.stamp(1)
        self.post("/tugas/1", 409, action="submit", stamp="0", **observations)
        self.post("/tugas/1", 422, action="submit", stamp=stamp,
                  **dict(observations, vulnerable_people=50))
        self.post("/tugas/1", 422, action="submit", stamp=stamp,
                  **dict(observations, required_package_equivalents=0))
        self.post("/tugas/1", action="submit", stamp=stamp, **observations)
        self.post("/tugas/2", action="submit", stamp="0", **observations)
        self.post("/laporan/1", 403, outcome="VERIFIED")

        self.as_role("admin")
        review = self.client.get("/pendataan/laporan/1")
        self.assertIn(b"25.00%", review.data)
        self.assertIn(b"40.00%", review.data)
        self.post("/laporan/1", 422, outcome="REJECTED")
        self.post("/laporan/1", outcome="REJECTED", note="Perbarui catatan stok")
        self.post("/laporan/1", 409, outcome="VERIFIED")
        self.post("/laporan/2", outcome="VERIFIED")

        self.as_role("petugas-1")
        self.assertIn(b"Perbarui catatan stok", self.client.get("/pendataan/tugas/1").data)
        self.post("/tugas/1", action="submit", stamp=self.stamp(1),
                  **dict(observations, available_package_equivalents=15))
        self.as_role("admin")
        self.post("/laporan/3", outcome="VERIFIED")
        self.assertIn(b"2 dari 2 kecamatan terverifikasi", self.client.get("/pendataan/kejadian/1").data)
        with closing(sqlite3.connect(self.database)) as db:
            rows = db.execute("SELECT version, status, criterion_values FROM field_reports "
                              "WHERE district_id=1 ORDER BY version").fetchall()
            self.assertEqual([(v, s, json.loads(c)[4]) for v, s, c in rows],
                             [(1, "REJECTED", 40), (2, "VERIFIED", 60)])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM field_report_reviews").fetchone()[0], 3)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM fieldwork_audit").fetchone()[0], 12)

    def test_legacy_database_keeps_round(self):
        legacy = self.database.with_name("legacy.sqlite3")
        snapshot = (ROOT / "examples" / "seed_case.json").read_text(encoding="utf-8")
        with closing(sqlite3.connect(legacy)) as db, db:
            db.executescript(SCHEMA)
            db.execute("PRAGMA user_version=1")
            db.execute("INSERT INTO assessment_round VALUES (1, ?, 'original', '1.0', '[]', 'final')", (snapshot,))
            db.execute("INSERT INTO assessment VALUES ('bpbd', '[]', 4, NULL, NULL)")
        create_app(legacy)
        with closing(sqlite3.connect(legacy)) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT snapshot, locked_at, finalized_at FROM assessment_round").fetchone(),
                             (snapshot, "original", "final"))
            self.assertEqual(db.execute("SELECT revision FROM assessment").fetchone()[0], 4)
