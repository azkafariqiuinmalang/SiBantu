import re
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app import create_app
from dashboard import district_catalog
from support import PASSWORD, login, seed_users


class LoginDashboardTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "database.sqlite3"
        self.app = create_app(self.database)
        self.client = self.app.test_client()
        seed_users(self.database)

    def test_login_protection_role_checks_and_logout(self):
        for path in ("/", "/dashboard", "/api/map", "/pendataan", "/penilaian/bpbd", "/hasil"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.headers["Location"].endswith("/login"))
        self.assertEqual(self.client.post("/login", data={"email": "bpbd@example.test"}).status_code, 400)
        page = self.client.get("/login")
        token = re.search(rb'name="token" value="([^"]+)"', page.data)[1].decode()
        self.assertEqual(self.client.post("/login", data=dict(token=token, email="bpbd@example.test",
                                                            password="wrong")).status_code, 401)
        token = login(self.client, "lapangan")
        self.assertEqual(self.client.get("/penilaian/bpbd").status_code, 403)
        self.assertEqual(self.client.post("/penilaian/bpbd", data=dict(token=token)).status_code, 403)
        self.assertEqual(self.client.post("/penilaian/bpbd/finalisasi", data=dict(token=token)).status_code, 403)
        self.assertEqual(self.client.post("/pendataan/peran", data=dict(token=token, actor="bpbd")).status_code, 404)
        self.assertEqual(self.client.post("/logout", data=dict(token=token)).status_code, 303)
        self.assertEqual(self.client.get("/dashboard").status_code, 302)
        login(self.client, "sosial")
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("UPDATE app_users SET is_active=0 WHERE role='sosial'")
        self.assertEqual(self.client.get("/dashboard").status_code, 302)

    def test_map_coverage_and_persisted_proposal_status(self):
        token = login(self.client, "bpbd")
        self.assertEqual(self.client.get("/dashboard").status_code, 200)
        data = self.client.get("/api/map").json
        self.assertEqual(len(data["features"]), 41)
        self.assertEqual({f["properties"]["status"] for f in data["features"]}, {"UNREGISTERED"})
        self.assertEqual(len({f["properties"]["code"] for f in data["features"]}), 41)
        counts = {region: sum(row["regency_code"] == region for row in district_catalog())
                  for region in ("35.07", "35.73", "35.79")}
        self.assertEqual(counts, {"35.07": 33, "35.73": 5, "35.79": 3})
        for feature in data["features"]:
            self.assertIn(feature["geometry"]["type"], {"Polygon", "MultiPolygon"})
        case = dict(token=token, case_code="MALANG-1", name="Gempa simulasi Malang",
                    incident_at="2025-01-01T08:00+07:00", province="Jawa Timur", regency="Malang Raya",
                    information_source="Simulasi", is_simulation="1")
        self.assertEqual(self.client.post("/pendataan/kejadian", data=case).status_code, 303)
        token = login(self.client, "lapangan")
        self.assertEqual(self.client.post("/pendataan/kejadian/1",
                         data=dict(token=token, action="district", district_code="35.73.01")).status_code, 303)
        self.assertEqual(self.client.get("/pendataan/kejadian/1").status_code, 200)
        data = self.client.get("/api/map?case_id=1").json
        properties = next(f["properties"] for f in data["features"] if f["properties"]["code"] == "35.73.01")
        self.assertEqual(properties["status"], "PENDING")
        self.assertIn(b"Blimbing", self.client.get("/pendataan").data)
        self.assertEqual(self.client.post("/pendataan/kejadian/1",
                         data=dict(token=token, action="approve_district", district_id=1)).status_code, 403)
        token = login(self.client, "bpbd")
        self.assertEqual(self.client.post("/pendataan/kejadian/1",
                         data=dict(token=token, action="approve_district", district_id=1)).status_code, 303)
        data = self.client.get("/api/map?case_id=1").json
        properties = next(f["properties"] for f in data["features"] if f["properties"]["code"] == "35.73.01")
        self.assertEqual(properties["status"], "ASSIGNED")
        token = login(self.client, "sosial")
        page = self.client.get("/pendataan/kejadian/1")
        self.assertEqual(page.status_code, 200)
        self.assertNotIn(b'value="assign"', page.data)
        self.assertEqual(self.client.post("/pendataan/kejadian/1",
                         data=dict(token=token, action="district", district_code="35.73.02")).status_code, 403)
        self.assertEqual(self.client.get("/api/map?case_id=99999").status_code, 404)
        self.assertEqual(self.client.get("/api/map?case_id=bad").status_code, 400)

    def test_login_rate_limit_and_restart(self):
        page = self.client.get("/login")
        token = re.search(rb'name="token" value="([^"]+)"', page.data)[1].decode()
        for _ in range(8):
            self.assertEqual(self.client.post("/login", data=dict(token=token,
                email="bpbd@example.test", password="wrong")).status_code, 401)
        self.assertEqual(self.client.post("/login", data=dict(token=token,
            email="bpbd@example.test", password=PASSWORD)).status_code, 429)
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("UPDATE login_attempts SET attempted_at=0")
        token = login(self.client, "bpbd")
        self.assertEqual(self.client.post("/logout", data={}).status_code, 400)
        restarted = create_app(self.database)
        restarted_client = restarted.test_client()
        cookie = self.client.get_cookie("session")
        restarted_client.set_cookie("session", cookie.value)
        response = restarted_client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response.headers["Cache-Control"])
        status = restarted.test_cli_runner().invoke(args=["database-status"])
        self.assertEqual(status.exit_code, 0, status.output)
        self.assertIn("sqlite", status.output)
