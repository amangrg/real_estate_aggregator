from __future__ import annotations

from typing import Any

from .models import (
    NormalizedAddress,
    NormalizedDisclosure,
    NormalizedHazards,
    NormalizedPermit,
    NormalizedPropertyFacts,
    NormalizedSaleEvent,
    NormalizedSourceRecord,
    SourceMetadata,
)
from .utils import canonicalize_address


def _build_metadata(raw: dict[str, Any]) -> SourceMetadata:
    return SourceMetadata(
        source=raw["source"],
        source_id=raw.get("source_id"),
        fetched_at=raw.get("fetched_at"),
    )


def _normalize_address(raw_address: dict[str, Any] | None) -> NormalizedAddress:
    raw_address = raw_address or {}
    return canonicalize_address(
        street=raw_address.get("street"),
        city=raw_address.get("city"),
        state=raw_address.get("state"),
        zip_code=raw_address.get("zip"),
    )


def normalize_listing(raw: dict[str, Any]) -> NormalizedSourceRecord:
    return NormalizedSourceRecord(
        metadata=_build_metadata(raw),
        address=_normalize_address(raw.get("address")),
        facts=NormalizedPropertyFacts(
            property_type=raw.get("property_type"),
            beds=raw.get("beds"),
            baths=raw.get("baths"),
            sqft=raw.get("sqft"),
            lot_size_sqft=raw.get("lot_size_sqft"),
            year_built=raw.get("year_built"),
            list_price=raw.get("list_price"),
            hoa_monthly=raw.get("hoa_monthly"),
        ),
        raw_context={
            "status": raw.get("status"),
            "days_on_market": raw.get("days_on_market"),
            "description": raw.get("description"),
            "features": raw.get("features", []),
            "schools": raw.get("schools", {}),
        },
    )


def normalize_tax_record(raw: dict[str, Any]) -> NormalizedSourceRecord:
    return NormalizedSourceRecord(
        metadata=_build_metadata(raw),
        address=_normalize_address(raw.get("address")),
        facts=NormalizedPropertyFacts(
            beds=raw.get("beds"),
            baths=raw.get("baths"),
            sqft=raw.get("sqft"),
            lot_size_sqft=raw.get("lot_size_sqft"),
            year_built=raw.get("year_built"),
            annual_tax=raw.get("annual_tax"),
            assessed_value=raw.get("assessed_value"),
            last_sale_date=raw.get("last_sale_date"),
            last_sale_price=raw.get("last_sale_price"),
        ),
        raw_context={
            "parcel_id": raw.get("parcel_id"),
            "owner_name": raw.get("owner_name"),
            "value_breakdown": {
                "land_value": raw.get("land_value"),
                "improvement_value": raw.get("improvement_value"),
            },
            "homestead_exemption": raw.get("homestead_exemption"),
        },
    )


def normalize_permit_record(raw: dict[str, Any]) -> NormalizedSourceRecord:
    permits = [
        NormalizedPermit(
            permit_id=permit.get("permit_id"),
            issue_date=permit.get("issue_date"),
            permit_type=permit.get("permit_type"),
            status=permit.get("status"),
            description=permit.get("description"),
        )
        for permit in raw.get("permits", [])
    ]
    return NormalizedSourceRecord(
        metadata=_build_metadata(raw),
        address=_normalize_address(raw.get("address")),
        permits=permits,
    )


def normalize_hazard(raw: dict[str, Any]) -> NormalizedSourceRecord:
    flood = raw.get("flood", {})
    wildfire = raw.get("wildfire", {})
    heat = raw.get("heat", {})
    air_quality = raw.get("air_quality", {})
    return NormalizedSourceRecord(
        metadata=_build_metadata(raw),
        address=_normalize_address(raw.get("address")),
        hazards=NormalizedHazards(
            flood_zone=flood.get("zone"),
            flood_risk_level=flood.get("risk_level"),
            flood_insurance_required=flood.get("fema_required_insurance"),
            wildfire_risk_level=wildfire.get("risk_level"),
            heat_risk_level=heat.get("risk_level"),
            air_quality_risk_level=air_quality.get("risk_level"),
        ),
        raw_context={"insurance_note": raw.get("insurance_note")},
    )


def normalize_sale_history(raw: dict[str, Any]) -> NormalizedSourceRecord:
    sales = [
        NormalizedSaleEvent(
            date=sale.get("date"),
            price=sale.get("price"),
            buyer=sale.get("buyer"),
            seller=sale.get("seller"),
        )
        for sale in raw.get("sales", [])
    ]
    return NormalizedSourceRecord(
        metadata=_build_metadata(raw),
        address=_normalize_address(raw.get("address")),
        sales=sales,
        facts=NormalizedPropertyFacts(
            last_sale_date=sales[0].date if sales else None,
            last_sale_price=sales[0].price if sales else None,
        ),
    )


def normalize_disclosure(raw: dict[str, Any]) -> NormalizedSourceRecord:
    return NormalizedSourceRecord(
        metadata=_build_metadata(raw),
        address=_normalize_address(raw.get("address")),
        disclosure=NormalizedDisclosure(
            known_issues=list(raw.get("known_issues", [])),
            systems=dict(raw.get("systems", {})),
        ),
        raw_context={"notes": raw.get("notes")},
    )


def normalize_sources(
    raw_sources: dict[str, dict[str, Any]],
) -> dict[str, NormalizedSourceRecord]:
    normalizers = {
        "listing": normalize_listing,
        "tax_record": normalize_tax_record,
        "permit_record": normalize_permit_record,
        "hazard": normalize_hazard,
        "sale_history": normalize_sale_history,
        "disclosure": normalize_disclosure,
    }
    return {
        source_name: normalizers[source_name](payload)
        for source_name, payload in raw_sources.items()
        if source_name in normalizers
    }
