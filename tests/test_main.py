from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from main import build_outputs


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_OUTPUT_ROOT = REPO_ROOT / "output"


class TestMain(unittest.TestCase):
    def test_build_outputs_writes_json_and_markdown_files(self) -> None:
        output_dir = TEST_OUTPUT_ROOT / "test-build-outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        resolved, brief, json_path, markdown_path = build_outputs("data", output_dir)

        self.assertTrue(json_path.exists())
        self.assertTrue(markdown_path.exists())
        self.assertEqual(resolved["property_id"], "1428-maple-creek-dr-austin-tx-78748")
        self.assertIn("# Property Brief: 1428 Maple Creek Dr, Austin, TX 78748", brief)

        persisted_resolved = json.loads(json_path.read_text(encoding="utf-8"))
        persisted_brief = markdown_path.read_text(encoding="utf-8")

        self.assertEqual(persisted_resolved["canonical_address"], resolved["canonical_address"])
        self.assertEqual(persisted_brief, brief)

    def test_main_cli_prints_output_locations(self) -> None:
        output_dir = TEST_OUTPUT_ROOT / "test-cli-outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            [
                sys.executable,
                "main.py",
                "--data-dir",
                "data",
                "--output-dir",
                str(output_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertIn("Property ID: 1428-maple-creek-dr-austin-tx-78748", result.stdout)
        self.assertIn("Resolved JSON:", result.stdout)
        self.assertIn("Markdown brief:", result.stdout)
        self.assertTrue((output_dir / "resolved_property.json").exists())
        self.assertTrue((output_dir / "property_brief.md").exists())


if __name__ == "__main__":
    unittest.main()
