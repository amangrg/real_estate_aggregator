from __future__ import annotations

import unittest

from src.ingest import load_sources
from src.normalize import normalize_sources
from src.resolve import resolve_property
from src.summarize import generate_markdown_brief


class TestSummarize(unittest.TestCase):
    def test_generate_markdown_brief_contains_required_headings(self) -> None:
        resolved = resolve_property(normalize_sources(load_sources("data")))

        brief = generate_markdown_brief(resolved)

        self.assertIn("# Property Brief: 1428 Maple Creek Dr, Austin, TX 78748", brief)
        self.assertIn("## Executive Summary", brief)
        self.assertIn("## Key Facts", brief)
        self.assertIn("## Renovation and Permit History", brief)
        self.assertIn("## Risks / Open Questions", brief)
        self.assertIn("## Confidence Notes", brief)

    def test_generate_markdown_brief_surfaces_core_signals(self) -> None:
        resolved = resolve_property(normalize_sources(load_sources("data")))

        brief = generate_markdown_brief(resolved)

        self.assertIn("listed at $489,000", brief)
        self.assertIn("Open permit:", brief)
        self.assertIn("Square footage differs between listing and tax record.", brief)
        self.assertIn("Heat risk level may warrant additional review.", brief)
        self.assertIn("Next step: verify flagged conflicts, permits, and hazard items during diligence.", brief)

    def test_generate_markdown_brief_degrades_gracefully_with_sparse_input(self) -> None:
        brief = generate_markdown_brief(
            {
                "canonical_address": None,
                "resolved_facts": {},
                "permits_summary": {},
                "hazards_summary": {},
                "flags": [],
            }
        )

        self.assertIn("# Property Brief: Unknown address", brief)
        self.assertIn("- Limited key facts available.", brief)
        self.assertIn("- No permit history was available.", brief)
        self.assertIn(
            "- No major risks or open questions were identified from the available data.",
            brief,
        )
        self.assertIn(
            "- Confidence notes are unavailable because no facts were resolved.",
            brief,
        )


if __name__ == "__main__":
    unittest.main()
