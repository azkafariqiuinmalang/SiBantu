import json
import re
import tempfile
import unittest
import sqlite3
from html.parser import HTMLParser
from contextlib import closing
from pathlib import Path

from app import ROOT, create_app
from decision_engine import PAIRS, SCALE, ahp, borda, topsis
from support import login, seed_users


class DecisionEngineTest(unittest.TestCase):
    def test_ahp_consistency_and_reciprocal(self):
        fixture = json.loads((ROOT / "examples" / "ahp_consistent_matrix.json").read_text())
        result = ahp([str(fixture["matrix"][i][j]) for i, j in PAIRS])
        for actual, expected in zip(result["weights"], fixture["expected_weights"]):
            self.assertAlmostEqual(actual, expected)
        self.assertAlmostEqual(result["lambda_max"], fixture["expected_lambda_max"])
        self.assertAlmostEqual(result["cr"], fixture["expected_CR"])
        ratios = ahp(["2"] * 5 + ["1"] * 10)
        self.assertAlmostEqual(ratios["weights"][0], 2 / 7)
        self.assertAlmostEqual(ratios["matrix"][1][0], 0.5)
        self.assertFalse(ahp(["9", "1/9"] + ["1"] * 13)["valid"])

    def test_topsis_cost_zero_columns_and_identical_scores(self):
        districts = [
            dict(code="B", name="B", values=[0, 0, 0, 0, 40, 0]),
            dict(code="A", name="A", values=[0, 0, 0, 0, 15, 0]),
        ]
        weights = [1 / 6] * 6
        result = topsis(districts, weights)
        self.assertEqual(result["zero_columns"], ["C1", "C2", "C3", "C4", "C6"])
        self.assertEqual([(row["code"], row["score"]) for row in result["rows"]],
                         [("A", 1), ("B", 0)])
        districts[0]["values"][4] = 15
        result = topsis(districts, weights)
        self.assertTrue(result["identical"])
        self.assertEqual([(row["code"], row["score"], row["tied"]) for row in result["rows"]],
                         [("A", 0.5, True), ("B", 0.5, True)])

    def test_borda_tie_uses_head_rank(self):
        districts = [dict(code=code, name=code) for code in "ABC"]
        rows = borda(districts, ["BCA", "ABC", "CAB"])
        self.assertEqual([(row["code"], row["total"], row["tied"]) for row in rows],
                         [("B", 6, True), ("C", 6, True), ("A", 6, True)])
        with self.assertRaises(ValueError):
            borda(districts, ["BCA", "ABC"])


class AssessmentTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "assessment.sqlite3"
        self.client = create_app(self.database).test_client()
        seed_users(self.database)
        self.token = login(self.client, "bpbd")
        page = self.client.get("/penilaian/bpbd")
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.data.count(b'<select name="pair_'), 15)
        self.token = re.search(rb'name="token" value="([^"]+)"', page.data)[1].decode()
        with self.client.get("/static/assessment.css") as stylesheet:
            self.assertEqual(stylesheet.status_code, 200)

    def post(self, role, action, choices=(), revision="0", follow=False):
        data = {f"pair_{index}": value for index, value in enumerate(choices)}
        data.update(token=self.token, revision=revision, action=action,round_id="1")
        return self.client.post(f"/penilaian/{role}", data=data, follow_redirects=follow)

    def test_guided_form_has_accessible_fallback_and_all_saaty_values(self):
        class SelectParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.selects = {}
                self.current = None

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "select":
                    self.current = attrs.get("name")
                    if self.current and self.current.startswith("pair_"):
                        self.selects[self.current] = []
                if tag == "option" and self.current in self.selects:
                    self.selects[self.current].append(attrs.get("value"))

            def handle_endtag(self, tag):
                if tag == "select":
                    self.current = None

        page = self.client.get("/penilaian/bpbd").get_data(as_text=True)
        parser = SelectParser()
        parser.feed(page)
        self.assertEqual(len(parser.selects), 15)
        for options in parser.selects.values():
            self.assertEqual(set(options), {"", *SCALE})
            self.assertEqual(len(options), 18)
        self.assertIn('data-left="Jumlah pengungsi"', page)
        self.assertIn('data-right="Jarak posko induk ke titik gempa"', page)
        self.assertIn("Lebih penting secara kuat (5)", page)
        for asset in ("ahp-form.js", "ahp-form.css"):
            self.assertIn(f"/static/{asset}", page)
            with self.client.get(f"/static/{asset}") as response:
                self.assertEqual(response.status_code, 200)

    def test_every_guided_choice_persists_without_filling_other_pairs(self):
        for revision, value in enumerate(SCALE):
            response = self.post("bpbd", "draft", [value], str(revision), follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(f'value="{value}" selected', response.get_data(as_text=True))
            with closing(sqlite3.connect(self.database)) as db:
                saved = db.execute("SELECT choices FROM round_assessments WHERE round_id=1 AND role='bpbd'").fetchone()
            self.assertEqual(json.loads(saved[0]), [value] + [""] * 14)
        self.assertEqual(self.post("bpbd", "submit", ["1/5"], str(len(SCALE))).status_code, 422)

    def test_workflow_and_persistence(self):
        valid = ["1"] * 15
        self.assertEqual(self.client.post("/penilaian/bpbd/finalisasi",
                                         data={"token": self.token,"round_id":"1"}).status_code, 409)
        self.assertEqual(self.post("bpbd", "submit", valid[:-1]).status_code, 422)
        invalid = self.post("bpbd", "submit", ["9", "1/9"] + ["1"] * 13)
        self.assertEqual(invalid.status_code, 422)
        self.assertIn(b"CR melebihi", invalid.data)
        draft = self.post("bpbd", "draft", valid[:1], follow=True)
        self.assertIn(b'name="revision" value="1"', draft.data)
        self.assertIn(b'value="1" selected', draft.data)
        preview = self.post("bpbd", "preview", valid)
        self.assertIn(b"Konsisten", preview.data)
        self.assertIn(b'name="revision" value="0"', preview.data)
        self.assertEqual(self.post("bpbd", "submit", valid).status_code, 409)
        submissions = [
            ("bpbd", "1", valid),
            ("lapangan", "0", ["2"] * 5 + ["1"] * 10),
            ("sosial", "0", ["1"] * 4 + ["1/3"] + ["1"] * 3
             + ["1/3"] + ["1"] * 2 + ["1/3", "1", "1/3", "1/3"]),
        ]
        for role, revision, choices in submissions:
            self.token = login(self.client, role)
            if role == "sosial":
                self.assertNotIn(b"Sahkan sebagai Kepala BPBD", self.client.get("/hasil").data)
            result = self.post(role, "submit", choices, revision, follow=True)
            self.assertEqual(result.status_code, 200)
            self.assertIn(b"TOPSIS", result.data)
            self.assertEqual(self.post(role, "draft", valid, revision).status_code, 409)
        self.token = login(self.client, "bpbd")
        group = self.client.get("/hasil")
        self.assertIn(b"Sahkan sebagai Kepala BPBD", group.data)
        final = self.client.post("/penilaian/bpbd/finalisasi", data={"token": self.token,"round_id":"1"},
                                 follow_redirects=True)
        self.assertEqual(final.status_code, 200)
        self.assertIn(b"Disahkan sebagai Kepala BPBD pada", final.data)
        restarted = create_app(self.database).test_client()
        login(restarted, "bpbd")
        reopened = restarted.get("/hasil")
        self.assertIn(b"Disahkan sebagai Kepala BPBD pada", reopened.data)
