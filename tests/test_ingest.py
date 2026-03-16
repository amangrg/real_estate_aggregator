from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from src.ingest import load_sources


class TestIngest(unittest.TestCase):
    def test_load_sources_reads_required_and_optional_files(self) -> None:
        sources = load_sources(Path(__file__).resolve().parents[1] / "data")

        self.assertEqual(set(sources), {
            "listing",
            "tax_record",
            "permit_record",
            "hazard",
            "sale_history",
            "disclosure",
        })
        self.assertEqual(sources["listing"]["source"], "listing")
        self.assertEqual(sources["tax_record"]["source"], "tax_record")

    def test_load_sources_omits_missing_optional_files(self) -> None:
        side_effect = [
            {"source": "listing"},
            {"source": "tax_record"},
            {"source": "permit_portal"},
            {"source": "hazard_service"},
            None,
            None,
        ]

        with patch("src.ingest._load_json_file", side_effect=side_effect):
            sources = load_sources("ignored-data-dir")

        self.assertEqual(set(sources), {
            "listing",
            "tax_record",
            "permit_record",
            "hazard",
        })

    def test_load_sources_raises_for_missing_required_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_sources(Path(__file__).resolve().parents[1])

    def test_load_sources_raises_for_malformed_required_json(self) -> None:
        side_effect = [
            {"source": "listing"},
            {"source": "tax_record"},
            {"source": "permit_portal"},
            ValueError("Malformed JSON in source file: hazard.json"),
        ]

        def fake_loader(*args: object, **kwargs: object) -> dict[str, str] | None:
            result = side_effect.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        with patch("src.ingest._load_json_file", side_effect=fake_loader):
            with self.assertRaises(ValueError):
                load_sources("ignored-data-dir")


if __name__ == "__main__":
    unittest.main()
