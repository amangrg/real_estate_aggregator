from __future__ import annotations

from typing import Any

from .models import NormalizedPermit, NormalizedSourceRecord
from .utils import slugify_address


IMPORTANT_FIELDS = [
    "property_type",
    "beds",
    "baths",
    "sqft",
    "lot_size_sqft",
    "year_built",
    "list_price",
    "annual_tax",
    "last_sale_date",
    "last_sale_price",
]

OPEN_PERMIT_STATUSES = {"open", "pending", "incomplete"}
NOTEWORTHY_RISK_LEVELS = {"moderate", "high", "very high", "severe"}


def _fact_value(
    normalized_sources: dict[str, NormalizedSourceRecord],
    source_name: str,
    field_name: str,
) -> Any:
    record = normalized_sources.get(source_name)
    if record is None:
        return None
    return getattr(record.facts, field_name)


def _build_resolved_fact(
    *,
    value: Any,
    confidence: str,
    sources: list[str],
    resolution_reason: str,
    conflict: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved = {
        "value": value,
        "confidence": confidence,
        "sources": sources,
        "resolution_reason": resolution_reason,
    }
    if conflict:
        resolved["conflict"] = conflict
    return resolved


def _resolve_property_type(
    normalized_sources: dict[str, NormalizedSourceRecord],
) -> dict[str, Any] | None:
    listing_value = _fact_value(normalized_sources, "listing", "property_type")
    if listing_value is not None:
        return _build_resolved_fact(
            value=listing_value,
            confidence="Medium",
            sources=["listing"],
            resolution_reason="Used listing property type as the preferred source.",
        )

    for source_name, record in normalized_sources.items():
        value = record.facts.property_type
        if value is not None:
            return _build_resolved_fact(
                value=value,
                confidence="Low",
                sources=[source_name],
                resolution_reason="Used the first available property type because listing data was missing.",
            )
    return None


def _resolve_listing_tax_field(
    normalized_sources: dict[str, NormalizedSourceRecord],
    *,
    field_name: str,
    label: str,
    prefer_source: str,
    same_confidence: str,
    single_source_confidence: str,
    conflict_confidence: str,
    same_reason: str,
    preferred_reason: str,
    conflict_reason: str,
) -> dict[str, Any] | None:
    listing_value = _fact_value(normalized_sources, "listing", field_name)
    tax_value = _fact_value(normalized_sources, "tax_record", field_name)
    available_sources = [
        source_name
        for source_name, value in (("listing", listing_value), ("tax_record", tax_value))
        if value is not None
    ]
    if not available_sources:
        return None
    if listing_value is not None and tax_value is not None:
        if listing_value == tax_value:
            return _build_resolved_fact(
                value=listing_value,
                confidence=same_confidence,
                sources=available_sources,
                resolution_reason=same_reason,
            )

        chosen_value = listing_value if prefer_source == "listing" else tax_value
        return _build_resolved_fact(
            value=chosen_value,
            confidence=conflict_confidence,
            sources=available_sources,
            conflict={"listing": listing_value, "tax_record": tax_value},
            resolution_reason=conflict_reason.format(label=label.lower()),
        )

    chosen_source = available_sources[0]
    chosen_value = listing_value if listing_value is not None else tax_value
    reason = preferred_reason if chosen_source == prefer_source else (
        f"Used {chosen_source.replace('_', ' ')} {label.lower()} because it was the only available source."
    )
    return _build_resolved_fact(
        value=chosen_value,
        confidence=single_source_confidence,
        sources=available_sources,
        resolution_reason=reason,
    )


def _resolve_sqft(normalized_sources: dict[str, NormalizedSourceRecord]) -> dict[str, Any] | None:
    listing_value = _fact_value(normalized_sources, "listing", "sqft")
    tax_value = _fact_value(normalized_sources, "tax_record", "sqft")
    available_sources = [
        source_name
        for source_name, value in (("listing", listing_value), ("tax_record", tax_value))
        if value is not None
    ]
    if not available_sources:
        return None
    if listing_value is None or tax_value is None:
        chosen_value = listing_value if listing_value is not None else tax_value
        chosen_source = available_sources[0]
        return _build_resolved_fact(
            value=chosen_value,
            confidence="Medium",
            sources=available_sources,
            resolution_reason=f"Used {chosen_source.replace('_', ' ')} square footage because it was the only available source.",
        )
    if listing_value == tax_value:
        return _build_resolved_fact(
            value=listing_value,
            confidence="High",
            sources=available_sources,
            resolution_reason="Used listing square footage because listing and tax record agree.",
        )

    difference = abs(listing_value - tax_value)
    confidence = "Medium" if difference <= 100 else "Low"
    size_label = "small" if difference <= 100 else "major"
    return _build_resolved_fact(
        value=listing_value,
        confidence=confidence,
        sources=available_sources,
        conflict={"listing": listing_value, "tax_record": tax_value},
        resolution_reason=f"Used listing square footage because it is the preferred source and the conflict is {size_label}.",
    )


def _resolve_last_sale_field(
    normalized_sources: dict[str, NormalizedSourceRecord],
    field_name: str,
) -> dict[str, Any] | None:
    sale_history_value = _fact_value(normalized_sources, "sale_history", field_name)
    tax_value = _fact_value(normalized_sources, "tax_record", field_name)
    available_sources = [
        source_name
        for source_name, value in (("sale_history", sale_history_value), ("tax_record", tax_value))
        if value is not None
    ]
    if not available_sources:
        return None
    if sale_history_value is not None and tax_value is not None:
        if sale_history_value == tax_value:
            return _build_resolved_fact(
                value=sale_history_value,
                confidence="High",
                sources=available_sources,
                resolution_reason=f"Used sale history {field_name.replace('_', ' ')} because sale history and tax record agree.",
            )
        return _build_resolved_fact(
            value=sale_history_value,
            confidence="Medium",
            sources=available_sources,
            conflict={"sale_history": sale_history_value, "tax_record": tax_value},
            resolution_reason=f"Used sale history {field_name.replace('_', ' ')} because sale history is the preferred source.",
        )

    chosen_value = sale_history_value if sale_history_value is not None else tax_value
    chosen_source = available_sources[0]
    return _build_resolved_fact(
        value=chosen_value,
        confidence="Medium",
        sources=available_sources,
        resolution_reason=f"Used {chosen_source.replace('_', ' ')} {field_name.replace('_', ' ')} because it was the only available source.",
    )


def _summarize_permits(permits: list[NormalizedPermit]) -> dict[str, Any]:
    permit_history = []
    open_permits = []
    for permit in permits:
        summary = (
            f"{permit.issue_date}: {permit.permit_type} "
            f"({permit.status}) - {permit.description}"
        )
        permit_history.append(summary)
        if (permit.status or "").lower() in OPEN_PERMIT_STATUSES:
            open_permits.append(summary)

    return {
        "total_permits": len(permits),
        "permit_history": permit_history,
        "open_permits": open_permits,
    }


def _summarize_hazards(normalized_sources: dict[str, NormalizedSourceRecord]) -> dict[str, Any]:
    hazard_record = normalized_sources.get("hazard")
    if hazard_record is None:
        return {}
    return {
        "flood_zone": hazard_record.hazards.flood_zone,
        "flood_risk": hazard_record.hazards.flood_risk_level,
        "flood_insurance_required": hazard_record.hazards.flood_insurance_required,
        "wildfire_risk": hazard_record.hazards.wildfire_risk_level,
        "heat_risk": hazard_record.hazards.heat_risk_level,
        "air_quality_risk": hazard_record.hazards.air_quality_risk_level,
        "insurance_note": hazard_record.raw_context.get("insurance_note"),
    }


def _build_flags(
    resolved_facts: dict[str, dict[str, Any]],
    permits_summary: dict[str, Any],
    hazards_summary: dict[str, Any],
) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []

    conflict_messages = {
        "beds": "Bedroom count differs between listing and tax record.",
        "baths": "Bathroom count differs between listing and tax record.",
        "sqft": "Square footage differs between listing and tax record.",
        "lot_size_sqft": "Lot size differs between listing and tax record.",
        "year_built": "Year built differs between listing and tax record.",
        "last_sale_date": "Last sale date differs between sale history and tax record.",
        "last_sale_price": "Last sale price differs between sale history and tax record.",
    }
    for field_name, message in conflict_messages.items():
        resolved = resolved_facts.get(field_name)
        if resolved and "conflict" in resolved:
            flags.append({"type": "conflict", "message": message})

    for permit_summary in permits_summary.get("open_permits", []):
        flags.append(
            {
                "type": "attention",
                "message": f"Open permit requires follow-up: {permit_summary}",
            }
        )

    hazard_messages = {
        "flood_risk": "Flood risk level may warrant additional review.",
        "wildfire_risk": "Wildfire risk level may warrant additional review.",
        "heat_risk": "Heat risk level may warrant additional review.",
        "air_quality_risk": "Air quality risk level may warrant additional review.",
    }
    for field_name, message in hazard_messages.items():
        risk_level = hazards_summary.get(field_name)
        if isinstance(risk_level, str) and risk_level.lower() in NOTEWORTHY_RISK_LEVELS:
            flags.append({"type": "risk", "message": message})

    if hazards_summary.get("insurance_note"):
        flags.append(
            {
                "type": "risk",
                "message": "Insurance costs may be elevated based on the hazard provider note.",
            }
        )

    for field_name in IMPORTANT_FIELDS:
        if field_name not in resolved_facts:
            flags.append(
                {
                    "type": "missing",
                    "message": f"Missing resolved value for {field_name.replace('_', ' ')}.",
                }
            )

    return flags


def resolve_property(
    normalized_sources: dict[str, NormalizedSourceRecord],
) -> dict[str, Any]:
    canonical_address = next(
        (
            record.address.canonical_line
            for record in normalized_sources.values()
            if record.address.canonical_line
        ),
        None,
    )
    permits = normalized_sources.get("permit_record").permits if "permit_record" in normalized_sources else []

    resolved_facts: dict[str, dict[str, Any]] = {}

    property_type = _resolve_property_type(normalized_sources)
    if property_type:
        resolved_facts["property_type"] = property_type

    simple_rules = {
        "beds": {
            "label": "Bedrooms",
            "prefer_source": "listing",
            "same_confidence": "High",
            "single_source_confidence": "Medium",
            "conflict_confidence": "Medium",
            "same_reason": "Used listing bedroom count because listing and tax record agree.",
            "preferred_reason": "Used listing bedroom count because listing is the preferred source.",
            "conflict_reason": "Used listing {label} because listing is preferred when the sources disagree.",
        },
        "baths": {
            "label": "Bathrooms",
            "prefer_source": "listing",
            "same_confidence": "High",
            "single_source_confidence": "Medium",
            "conflict_confidence": "Medium",
            "same_reason": "Used listing bathroom count because listing and tax record agree.",
            "preferred_reason": "Used listing bathroom count because listing is the preferred source.",
            "conflict_reason": "Used listing {label} because listing is preferred when the sources disagree.",
        },
        "lot_size_sqft": {
            "label": "Lot size",
            "prefer_source": "listing",
            "same_confidence": "High",
            "single_source_confidence": "Medium",
            "conflict_confidence": "Low",
            "same_reason": "Used listing lot size because listing and tax record agree.",
            "preferred_reason": "Used listing lot size because listing is the preferred source.",
            "conflict_reason": "Used listing {label} because listing is preferred even though the sources disagree.",
        },
        "year_built": {
            "label": "Year built",
            "prefer_source": "tax_record",
            "same_confidence": "High",
            "single_source_confidence": "High",
            "conflict_confidence": "Medium",
            "same_reason": "Used tax record year built because listing and tax record agree.",
            "preferred_reason": "Used tax record year built because tax record is the preferred source.",
            "conflict_reason": "Used tax record {label} because tax record is preferred when the sources disagree.",
        },
    }
    for field_name, rule in simple_rules.items():
        resolved = _resolve_listing_tax_field(
            normalized_sources,
            field_name=field_name,
            **rule,
        )
        if resolved:
            resolved_facts[field_name] = resolved

    sqft = _resolve_sqft(normalized_sources)
    if sqft:
        resolved_facts["sqft"] = sqft

    list_price = _fact_value(normalized_sources, "listing", "list_price")
    if list_price is not None:
        resolved_facts["list_price"] = _build_resolved_fact(
            value=list_price,
            confidence="High",
            sources=["listing"],
            resolution_reason="Used listing price because listing is the authoritative source for current asking price.",
        )

    annual_tax = _fact_value(normalized_sources, "tax_record", "annual_tax")
    if annual_tax is not None:
        resolved_facts["annual_tax"] = _build_resolved_fact(
            value=annual_tax,
            confidence="High",
            sources=["tax_record"],
            resolution_reason="Used annual tax from the tax record because it is the authoritative source.",
        )

    assessed_value = _fact_value(normalized_sources, "tax_record", "assessed_value")
    if assessed_value is not None:
        resolved_facts["assessed_value"] = _build_resolved_fact(
            value=assessed_value,
            confidence="High",
            sources=["tax_record"],
            resolution_reason="Used assessed value from the tax record.",
        )

    hoa_monthly = _fact_value(normalized_sources, "listing", "hoa_monthly")
    if hoa_monthly is not None:
        resolved_facts["hoa_monthly"] = _build_resolved_fact(
            value=hoa_monthly,
            confidence="Medium",
            sources=["listing"],
            resolution_reason="Used HOA dues from the listing because no secondary source is available.",
        )

    for field_name in ("last_sale_date", "last_sale_price"):
        resolved = _resolve_last_sale_field(normalized_sources, field_name)
        if resolved:
            resolved_facts[field_name] = resolved

    permits_summary = _summarize_permits(permits)
    hazards_summary = _summarize_hazards(normalized_sources)
    flags = _build_flags(resolved_facts, permits_summary, hazards_summary)

    return {
        "property_id": slugify_address(canonical_address),
        "canonical_address": canonical_address,
        "resolved_facts": resolved_facts,
        "permits_summary": permits_summary,
        "hazards_summary": hazards_summary,
        "flags": flags,
    }
