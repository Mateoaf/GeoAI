from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
AUDIT = ROOT / "reports" / "audit"


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class PipelineOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = csv_rows(PROCESSED / "oxrep_roman_mines_spain_clean.csv")
        cls.commodity = csv_rows(PROCESSED / "oxrep_spain_mine_commodities.csv")
        cls.technique = csv_rows(PROCESSED / "oxrep_spain_mine_techniques.csv")

    def test_expected_record_count_and_unique_ids(self) -> None:
        self.assertEqual(len(self.clean), 930)
        mine_ids = [int(row["mineID"]) for row in self.clean]
        self.assertEqual(len(mine_ids), len(set(mine_ids)))

    def test_lanz_override_is_explicit(self) -> None:
        lanz = [row for row in self.clean if row["mineID"] == "132"]
        self.assertEqual(len(lanz), 1)
        self.assertEqual(lanz[0]["country"], "Navarra")
        self.assertEqual(lanz[0]["flag_country_override"], "True")
        self.assertEqual(lanz[0]["Y_Cu"], "True")
        self.assertEqual(lanz[0]["has_technique_underground"], "True")

    def test_selection_decisions_reconcile(self) -> None:
        decisions = csv_rows(AUDIT / "spain_selection_decisions.csv")
        self.assertEqual(len(decisions), 1399)
        selected = [row for row in decisions if row["include_spain_subset"] == "True"]
        self.assertEqual(len(selected), len(self.clean))

    def test_indicator_long_tables_have_full_cartesian_rows(self) -> None:
        self.assertEqual(len(self.commodity), 930 * 9)
        self.assertEqual(len(self.technique), 930 * 9)
        valid_states = {"present", "absent", "unknown", "missing", "invalid"}
        self.assertTrue({row["status"] for row in self.commodity} <= valid_states)
        self.assertTrue({row["status"] for row in self.technique} <= valid_states)

    def test_core_commodity_counts(self) -> None:
        present = {
            code: sum(
                row["commodity_code"] == code and row["status"] == "present"
                for row in self.commodity
            )
            for code in ["Au", "Ag", "Pb", "Cu", "Sn", "Fe", "Hg", "Zn", "Other"]
        }
        self.assertEqual(
            present,
            {"Au": 598, "Ag": 174, "Pb": 169, "Cu": 169, "Sn": 9, "Fe": 15, "Hg": 5, "Zn": 3, "Other": 0},
        )

    def test_geojson_reconciles_coordinates(self) -> None:
        geojson = json.loads(
            (PROCESSED / "oxrep_roman_mines_spain_clean.geojson").read_text(
                encoding="utf-8"
            )
        )
        complete = sum(
            row["latitude_decimal"] != "" and row["longitude_decimal"] != ""
            for row in self.clean
        )
        self.assertEqual(len(geojson["features"]), complete)
        self.assertEqual(len(geojson["features"]), 923)

    def test_sqlite_reconciles(self) -> None:
        with sqlite3.connect(PROCESSED / "oxrep_roman_mines_spain.sqlite") as connection:
            mine_count = connection.execute("SELECT COUNT(*) FROM roman_mine").fetchone()[0]
            commodity_count = connection.execute(
                "SELECT COUNT(*) FROM mine_commodity"
            ).fetchone()[0]
        self.assertEqual(mine_count, 930)
        self.assertEqual(commodity_count, 8370)

    def test_input_hash_matches_manifest(self) -> None:
        manifest = json.loads((AUDIT / "input_manifest.json").read_text(encoding="utf-8"))
        workbook = ROOT / "data" / "raw" / "oxrep-mines-3.0-20250408.xlsx"
        digest = hashlib.sha256(workbook.read_bytes()).hexdigest()
        workbook_entry = next(
            item for item in manifest["files"] if item["relative_path"].endswith(".xlsx")
        )
        self.assertEqual(digest, workbook_entry["sha256"])
        self.assertEqual(
            digest,
            "802e35d0abef469fb7683b3b82b1638224db059f19919a2e245ce44ec757815a",
        )

    def test_methodological_reference_hash_matches_config_and_manifest(self) -> None:
        config = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))
        manifest = json.loads((AUDIT / "input_manifest.json").read_text(encoding="utf-8"))
        configured = config["methodological_references"][0]
        reference = ROOT / configured["path"]
        digest = hashlib.sha256(reference.read_bytes()).hexdigest()
        manifest_entry = next(
            item
            for item in manifest["files"]
            if item["relative_path"] == configured["path"]
        )
        self.assertEqual(digest, configured["expected_sha256"])
        self.assertEqual(digest, manifest_entry["sha256"])
        self.assertIn("Methodological antecedent", manifest_entry["role"])


if __name__ == "__main__":
    unittest.main()
