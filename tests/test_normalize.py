from __future__ import annotations

import inspect
import json
import unittest
from pathlib import Path
from typing import get_type_hints

from src.models import (
    NormalizedAddress,
    NormalizedDisclosure,
    NormalizedHazards,
    NormalizedPermit,
    NormalizedPropertyFacts,
    NormalizedSaleEvent,
    NormalizedSourceRecord,
    SourceMetadata,
)
from src.normalize import (
    normalize_disclosure,
    normalize_hazard,
    normalize_listing,
    normalize_permit_record,
    normalize_sale_history,
    normalize_tax_record,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_fixture(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


class TestNormalizedSchema(unittest.TestCase):
    def test_minimal_normalized_source_record_has_sane_defaults(self) -> None:
        record = NormalizedSourceRecord(metadata=SourceMetadata(source="listing"))

        self.assertEqual(record.metadata.source, "listing")
        self.assertEqual(record.address, NormalizedAddress())
        self.assertEqual(record.facts, NormalizedPropertyFacts())
        self.assertEqual(record.permits, [])
        self.assertEqual(record.sales, [])
        self.assertEqual(record.hazards, NormalizedHazards())
        self.assertEqual(record.disclosure, NormalizedDisclosure())
        self.assertEqual(record.raw_context, {})


    def test_collection_defaults_are_not_shared_between_instances(self) -> None:
        first = NormalizedSourceRecord(metadata=SourceMetadata(source="listing"))
        second = NormalizedSourceRecord(metadata=SourceMetadata(source="tax_record"))

        first.permits.append(NormalizedPermit(permit_id="PRM-1"))
        first.sales.append(NormalizedSaleEvent(date="2020-01-01"))
        first.disclosure.known_issues.append("Leak repaired")
        first.disclosure.systems["roof"] = "2023"
        first.raw_context["description"] = "Updated kitchen"

        self.assertEqual(second.permits, [])
        self.assertEqual(second.sales, [])
        self.assertEqual(second.disclosure.known_issues, [])
        self.assertEqual(second.disclosure.systems, {})
        self.assertEqual(second.raw_context, {})


    def test_to_dict_serializes_nested_shape(self) -> None:
        record = NormalizedSourceRecord(
            metadata=SourceMetadata(
                source="listing",
                source_id="MLS-123",
                fetched_at="2026-03-16T10:30:00Z",
            ),
            address=NormalizedAddress(
                street="1428 Maple Creek Dr",
                city="Austin",
                state="TX",
                zip="78748",
                canonical_line="1428 Maple Creek Dr, Austin, TX 78748",
            ),
            facts=NormalizedPropertyFacts(
                property_type="Single Family",
                beds=3,
                baths=2.0,
                sqft=1842,
                list_price=489000,
            ),
            permits=[
                NormalizedPermit(
                    permit_id="PRM-2023-009812",
                    issue_date="2023-05-22",
                    permit_type="Roof Replacement",
                    status="Finaled",
                )
            ],
            sales=[NormalizedSaleEvent(date="2019-06-14", price=349000)],
            hazards=NormalizedHazards(
                flood_zone="X",
                flood_risk_level="Low",
                flood_insurance_required=False,
                wildfire_risk_level="Low",
            ),
            disclosure=NormalizedDisclosure(
                known_issues=["Previous minor water intrusion"],
                systems={"roof": "Replaced in 2023"},
            ),
            raw_context={"description": "Updated single-story home"},
        )

        serialized = record.to_dict()

        self.assertEqual(serialized["metadata"]["source_id"], "MLS-123")
        self.assertEqual(
            serialized["address"]["canonical_line"],
            "1428 Maple Creek Dr, Austin, TX 78748",
        )
        self.assertEqual(serialized["facts"]["sqft"], 1842)
        self.assertEqual(serialized["permits"][0]["permit_type"], "Roof Replacement")
        self.assertEqual(serialized["sales"][0]["price"], 349000)
        self.assertEqual(serialized["hazards"]["flood_zone"], "X")
        self.assertEqual(
            serialized["disclosure"]["systems"]["roof"],
            "Replaced in 2023",
        )
        self.assertEqual(
            serialized["raw_context"]["description"],
            "Updated single-story home",
        )


    def test_selective_raw_context_survives_serialization(self) -> None:
        record = NormalizedSourceRecord(
            metadata=SourceMetadata(source="tax_record"),
            raw_context={
                "parcel_id": "0293847712",
                "owner_name": "Maple Creek Holdings LLC",
                "value_breakdown": {
                    "land_value": 175000,
                    "improvement_value": 276200,
                },
            },
        )

        self.assertEqual(
            record.to_dict()["raw_context"]["value_breakdown"]["land_value"],
            175000,
        )


    def test_normalizer_interfaces_return_normalized_source_record_type(self) -> None:
        normalizers = [
            normalize_listing,
            normalize_tax_record,
            normalize_permit_record,
            normalize_hazard,
            normalize_sale_history,
            normalize_disclosure,
        ]

        for normalizer in normalizers:
            hints = get_type_hints(normalizer)
            signature = inspect.signature(normalizer)

            self.assertEqual(list(signature.parameters), ["raw"])
            self.assertIs(hints["return"], NormalizedSourceRecord)


    def test_fixture_based_schema_smoke_shape_for_listing_and_tax(self) -> None:
        listing = load_fixture("listing.json")
        tax_record = load_fixture("tax_record.json")

        listing_record = NormalizedSourceRecord(
            metadata=SourceMetadata(
                source=listing["source"],
                source_id=listing["source_id"],
                fetched_at=listing["fetched_at"],
            ),
            address=NormalizedAddress(
                street=listing["address"]["street"],
                city=listing["address"]["city"],
                state=listing["address"]["state"],
                zip=listing["address"]["zip"],
                canonical_line="1428 Maple Creek Dr, Austin, TX 78748",
            ),
            facts=NormalizedPropertyFacts(
                property_type=listing["property_type"],
                beds=listing["beds"],
                baths=listing["baths"],
                sqft=listing["sqft"],
                lot_size_sqft=listing["lot_size_sqft"],
                year_built=listing["year_built"],
                list_price=listing["list_price"],
                hoa_monthly=listing["hoa_monthly"],
            ),
            raw_context={
                "description": listing["description"],
                "features": listing["features"],
            },
        )
        tax_record_record = NormalizedSourceRecord(
            metadata=SourceMetadata(
                source=tax_record["source"],
                source_id=tax_record["source_id"],
                fetched_at=tax_record["fetched_at"],
            ),
            address=NormalizedAddress(
                street=tax_record["address"]["street"],
                city=tax_record["address"]["city"],
                state=tax_record["address"]["state"],
                zip=tax_record["address"]["zip"],
                canonical_line="1428 Maple Creek Dr, Austin, TX 78748",
            ),
            facts=NormalizedPropertyFacts(
                beds=tax_record["beds"],
                baths=tax_record["baths"],
                sqft=tax_record["sqft"],
                lot_size_sqft=tax_record["lot_size_sqft"],
                year_built=tax_record["year_built"],
                annual_tax=tax_record["annual_tax"],
                assessed_value=tax_record["assessed_value"],
                last_sale_date=tax_record["last_sale_date"],
                last_sale_price=tax_record["last_sale_price"],
            ),
            raw_context={
                "parcel_id": tax_record["parcel_id"],
                "owner_name": tax_record["owner_name"],
                "value_breakdown": {
                    "land_value": tax_record["land_value"],
                    "improvement_value": tax_record["improvement_value"],
                },
            },
        )

        self.assertEqual(listing_record.facts.property_type, "Single Family")
        self.assertEqual(
            listing_record.raw_context["features"],
            ["garage", "fenced yard", "renovated kitchen", "fireplace"],
        )
        self.assertEqual(tax_record_record.facts.annual_tax, 8935)
        self.assertEqual(tax_record_record.raw_context["parcel_id"], "0293847712")


if __name__ == "__main__":
    unittest.main()
