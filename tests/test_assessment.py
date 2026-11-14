import json
import re
import tempfile
import unittest
from pathlib import Path

from app import ROOT, create_app
from decision_engine import PAIRS, ahp, borda, topsis


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
        page = self.client.get("/", follow_redirects=True)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.data.count(b'<select name="pair_'), 15)
        self.token = re.search(rb'name="token" value="([^"]+)"', page.data)[1].decode()
        with self.client.get("/static/assessment.css") as stylesheet:
            self.assertEqual(stylesheet.status_code, 200)

    def post(self, role, action, choices=(), revision="0", follow=False):
        data = {f"pair_{index}": value for index, value in enumerate(choices)}
        data.update(token=self.token, revision=revision, action=action)
        return self.client.post(f"/penilaian/{role}", data=data, follow_redirects=follow)

    def test_workflow_and_persistence(self):
        valid = ["1"] * 15
        self.assertEqual(self.client.post("/penilaian/bpbd/finalisasi",
                                         data={"token": self.token}).status_code, 409)
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
            if role == "sosial":
                self.assertNotIn(b"Sahkan sebagai Kepala BPBD", self.client.get("/hasil").data)
            result = self.post(role, "submit", choices, revision, follow=True)
            self.assertEqual(result.status_code, 200)
            self.assertIn(b"TOPSIS", result.data)
            self.assertEqual(self.post(role, "draft", valid, revision).status_code, 409)
        group = self.client.get("/hasil")
        self.assertIn(b"Sahkan sebagai Kepala BPBD", group.data)
        final = self.client.post("/penilaian/bpbd/finalisasi", data={"token": self.token},
                                 follow_redirects=True)
        self.assertEqual(final.status_code, 200)
        self.assertIn(b"Disahkan sebagai Kepala BPBD pada", final.data)
        reopened = create_app(self.database).test_client().get("/hasil")
        self.assertIn(b"Disahkan sebagai Kepala BPBD pada", reopened.data)
