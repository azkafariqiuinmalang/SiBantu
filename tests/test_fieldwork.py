import json
import re
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app import ROOT, SCHEMA, create_app
from database import SCHEMA_VERSION
from support import login, seed_users


class FieldworkTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "assessment.sqlite3"
        self.client = create_app(self.database).test_client()
        seed_users(self.database)
        self.token = login(self.client, "sosial")
        page = self.client.get("/pendataan")
        self.assertEqual(page.status_code, 200)
        self.token = re.search(rb'name="token" value="([^"]+)"', page.data)[1].decode()

    def post(self, path, expected=303, **data):
        response = self.client.post("/pendataan" + path, data={"token": self.token, **data})
        self.assertEqual(response.status_code, expected, response.data[-1000:])
        return response

    def as_role(self, role):
        self.token = login(self.client, role)

    def stamp(self, task_id):
        page = self.client.get(f"/pendataan/tugas/{task_id}")
        self.assertEqual(page.status_code, 200)
        return re.search(rb'name="stamp" value="([^"]+)"', page.data)[1].decode()

    def test_calendar_input_is_saved_as_wib_and_displayed_day_first(self):
        self.as_role("bpbd")
        page = self.client.get("/pendataan")
        self.assertIn(b'placeholder="Contoh: GB-001"', page.data)
        self.assertIn(b'type="datetime-local"', page.data)
        self.assertNotIn(b"2026-05-01T08:00+07:00", page.data)
        case = dict(case_code="gb-001",name="Gempa simulasi",incident_at="2025-01-01T00:30",
                    province="Jawa Timur",regency="Malang Raya",information_source="Simulasi",is_simulation="1")
        self.post("/kejadian", **case)
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute("SELECT case_code,incident_at FROM disaster_cases").fetchone(),
                             ("GB-001","2024-12-31T17:30:00+00:00"))
        self.assertIn(b"01/01/2025, 00:30 WIB",self.client.get("/pendataan/kejadian/1").data)
        # Duplicate-code errors retain the selected date in a valid native-input format.
        response = self.post("/kejadian",409,**{**case,"incident_at":"2025-01-01T00:30+07:00"})
        self.assertIn(b'value="2025-01-01T00:30"',response.data)

    def test_calendar_rejects_invalid_and_future_values_without_writing_case(self):
        self.as_role("bpbd")
        case = dict(case_code="GB-002",name="Gempa simulasi",province="Jawa Timur",regency="Malang Raya",
                    information_source="Simulasi",is_simulation="1")
        for value in ("", "2025-02-30T12:00", "2025-01-01", "2999-01-01T00:00"):
            with self.subTest(value=value):
                self.post("/kejadian",422,incident_at=value,**case)
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM disaster_cases").fetchone()[0],0)

    def test_two_districts_reject_revise_verify(self):
        case = dict(case_code="sim-1", name="Gempa X", incident_at="2025-01-01T08:00+07:00",
                    province="Jawa Timur", regency="Kota Malang",
                    information_source="Simulasi UAS", is_simulation="1")
        self.post("/kejadian", 403, **case)
        self.as_role("bpbd")
        self.post("/kejadian", 422, **dict(case, incident_at="2999-01-01T08:00+07:00"))
        self.post("/kejadian", **case)
        self.post("/kejadian", 409, **dict(case, case_code="SIM-1"))
        for number in (1, 2):
            self.post("/kejadian/1", action="district", district_code=f"35.73.0{number}",
                      district_name=f"Kecamatan {number}")
            self.post("/kejadian/1", action="assign", district_id=number)
        self.post("/kejadian/1", 409, action="district", district_code="35.73.01", district_name="Ganda")

        observations = dict(observed_at="2025-01-01T12:00+07:00", source_note="Catatan posko",
                            evacuees=20, vulnerable_people=5, housing_damage_score=3,
                            essential_services_disruption_score=2, available_package_equivalents=10,
                            required_package_equivalents=25, distance_to_epicenter_km=4)
        self.as_role("sosial")
        self.post("/tugas/1", 403, action="submit", stamp="0", **observations)
        self.as_role("lapangan")
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

        self.as_role("bpbd")
        review = self.client.get("/pendataan/laporan/1")
        self.assertIn(b"25.00%", review.data)
        self.assertIn(b"40.00%", review.data)
        self.post("/laporan/1", 422, outcome="REJECTED")
        self.post("/laporan/1", outcome="REJECTED", note="Perbarui catatan stok")
        self.post("/laporan/1", 409, outcome="VERIFIED")
        self.post("/laporan/2", outcome="VERIFIED")

        self.as_role("lapangan")
        self.assertIn(b"Perbarui catatan stok", self.client.get("/pendataan/tugas/1").data)
        self.post("/tugas/1", action="submit", stamp=self.stamp(1),
                  **dict(observations, available_package_equivalents=15))
        self.as_role("bpbd")
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
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
            self.assertEqual(db.execute("SELECT snapshot, locked_at, finalized_at FROM assessment_round").fetchone(),
                             (snapshot, "original", "final"))
            self.assertEqual(db.execute("SELECT revision FROM assessment").fetchone()[0], 4)

    def test_version_two_upgrade_keeps_field_reports(self):
        legacy = self.database.with_name("legacy-v2.sqlite3")
        with closing(sqlite3.connect(legacy)) as db, db:
            db.executescript(SCHEMA)
            db.executescript((ROOT / "migrations" / "002_fieldwork.sql").read_text())
            db.execute("PRAGMA user_version=2")
            db.execute("INSERT INTO disaster_cases VALUES (1,'OLD','Lama','2025-01-01',"
                       "'Jawa Timur','Kota Malang',NULL,'Simulasi',1,'original')")
            db.execute("INSERT INTO districts VALUES (1,1,'OLD','Kecamatan lama')")
            db.execute("INSERT INTO assignments VALUES (1,1,'petugas-1','original')")
            db.execute("INSERT INTO field_reports VALUES (1,1,1,1,1,'VERIFIED','{}','[]','original','sent')")
        create_app(legacy)
        create_app(legacy)
        with closing(sqlite3.connect(legacy)) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
            self.assertEqual(db.execute("SELECT status,created_at FROM field_reports").fetchone(),
                             ("VERIFIED", "original"))
            self.assertEqual(db.execute("SELECT verification_status FROM districts").fetchone()[0], "APPROVED")
            self.assertEqual(db.execute("SELECT officer_id FROM assignments").fetchone()[0], "petugas-1")
