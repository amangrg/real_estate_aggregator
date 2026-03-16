from __future__ import annotations

import unittest

from src.ingest import load_sources
from src.models import NormalizedSourceRecord, SourceMetadata
from src.normalize import normalize_sources
from src.resolve import resolve_property


class TestResolve(unittest.TestCase):
    def test_resolve_property_applies_fixture_rules(self) -> None:
        normalized = normalize_sources(load_sources("data"))

        resolved = resolve_property(normalized)

        self.assertEqual(resolved["property_id"], "1428-maple-creek-dr-austin-tx-78748")
        self.assertEqual(
            resolved["canonical_address"],
            "1428 Maple Creek Dr, Austin, TX 78748",
        )
        self.assertEqual(resolved["resolved_facts"]["beds"]["confidence"], "High")
        self.assertEqual(resolved["resolved_facts"]["year_built"]["value"], 1988)
        self.assertEqual(resolved["resolved_facts"]["year_built"]["confidence"], "Medium")
        self.assertEqual(resolved["resolved_facts"]["sqft"]["value"], 1842)
        self.assertEqual(resolved["resolved_facts"]["sqft"]["confidence"], "Medium")
        self.assertEqual(
            resolved["resolved_facts"]["sqft"]["conflict"],
            {"listing": 1842, "tax_record": 1836},
        )
        self.assertEqual(resolved["resolved_facts"]["last_sale_price"]["confidence"], "High")

    def test_resolve_property_builds_permit_and_hazard_flags(self) -> None:
        normalized = normalize_sources(load_sources("data"))

        resolved = resolve_property(normalized)
        messages = [flag["message"] for flag in resolved["flags"]]
        flag_types = [flag["type"] for flag in resolved["flags"]]

        self.assertEqual(resolved["permits_summary"]["total_permits"], 3)
        self.assertEqual(len(resolved["permits_summary"]["open_permits"]), 1)
        self.assertTrue(
            any(message.startswith("Open permit requires follow-up") for message in messages)
        )
        self.assertIn("Heat risk level may warrant additional review.", messages)
        self.assertIn("Insurance costs may be elevated based on the hazard provider note.", messages)
        self.assertIn("attention", flag_types)
        self.assertIn("risk", flag_types)

    def test_resolve_property_adds_missing_flags_for_unresolved_fields(self) -> None:
        normalized = {
            "listing": NormalizedSourceRecord(metadata=SourceMetadata(source="listing")),
        }

        resolved = resolve_property(normalized)
        missing_messages = [
            flag["message"]
            for flag in resolved["flags"]
            if flag["type"] == "missing"
        ]

        self.assertIn("Missing resolved value for beds.", missing_messages)
        self.assertIn("Missing resolved value for annual tax.", missing_messages)


if __name__ == "__main__":
    unittest.main()
