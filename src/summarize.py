from __future__ import annotations

from typing import Any


def _resolved_value(resolved: dict[str, Any], field_name: str) -> Any:
    field = resolved.get("resolved_facts", {}).get(field_name)
    if not field:
        return None
    return field.get("value")


def _format_currency(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return f"${value:,.0f}"
    return str(value)


def _format_key_facts(resolved: dict[str, Any]) -> list[str]:
    facts = []
    property_type = _resolved_value(resolved, "property_type")
    beds = _resolved_value(resolved, "beds")
    baths = _resolved_value(resolved, "baths")
    sqft = _resolved_value(resolved, "sqft")
    lot_size = _resolved_value(resolved, "lot_size_sqft")
    year_built = _resolved_value(resolved, "year_built")
    list_price = _resolved_value(resolved, "list_price")
    annual_tax = _resolved_value(resolved, "annual_tax")
    last_sale_date = _resolved_value(resolved, "last_sale_date")
    last_sale_price = _resolved_value(resolved, "last_sale_price")
    hoa_monthly = _resolved_value(resolved, "hoa_monthly")

    if property_type:
        facts.append(f"Property type: {property_type}")
    if beds is not None and baths is not None:
        facts.append(f"Bedrooms / bathrooms: {beds} / {baths}")
    elif beds is not None:
        facts.append(f"Bedrooms: {beds}")
    elif baths is not None:
        facts.append(f"Bathrooms: {baths}")
    if sqft is not None:
        facts.append(f"Interior size: {sqft:,} sqft")
    if lot_size is not None:
        facts.append(f"Lot size: {lot_size:,} sqft")
    if year_built is not None:
        facts.append(f"Year built: {year_built}")
    if list_price is not None:
        facts.append(f"List price: {_format_currency(list_price)}")
    if annual_tax is not None:
        facts.append(f"Annual tax: {_format_currency(annual_tax)}")
    if last_sale_date is not None or last_sale_price is not None:
        sale_bits = []
        if last_sale_date is not None:
            sale_bits.append(str(last_sale_date))
        if last_sale_price is not None:
            sale_bits.append(_format_currency(last_sale_price))
        facts.append(f"Last recorded sale: {' for '.join(sale_bits)}")
    if hoa_monthly is not None:
        facts.append(f"HOA dues: {_format_currency(hoa_monthly)} / month")
    return facts


def _executive_summary(resolved: dict[str, Any]) -> str:
    summary_parts = []
    property_type = _resolved_value(resolved, "property_type")
    beds = _resolved_value(resolved, "beds")
    baths = _resolved_value(resolved, "baths")
    sqft = _resolved_value(resolved, "sqft")
    list_price = _resolved_value(resolved, "list_price")

    if property_type:
        summary_parts.append(property_type)
    if beds is not None and baths is not None:
        summary_parts.append(f"{beds}-bed / {baths}-bath")
    if sqft is not None:
        summary_parts.append(f"{sqft:,} sqft")
    if list_price is not None:
        summary_parts.append(f"listed at {_format_currency(list_price)}")

    sentence = "This property"
    if summary_parts:
        sentence += " is a " + ", ".join(str(part) for part in summary_parts[:-1])
        if len(summary_parts) > 1:
            sentence += f", {summary_parts[-1]}"
        else:
            sentence = f"This property is a {summary_parts[0]}"
        sentence += "."
    else:
        sentence += " has limited resolved fact coverage."

    flags = resolved.get("flags", [])
    open_permit_flags = [flag for flag in flags if flag.get("type") == "attention"]
    conflict_flags = [flag for flag in flags if flag.get("type") == "conflict"]
    risk_flags = [flag for flag in flags if flag.get("type") == "risk"]

    notes = []
    if open_permit_flags:
        notes.append("There is at least one open permit that should be verified.")
    if conflict_flags:
        notes.append("Some core facts still conflict across sources.")
    if risk_flags:
        notes.append("Hazard and insurance signals warrant review before making an offer.")

    if notes:
        sentence += " " + " ".join(notes)
    return sentence


def _renovation_and_permits(resolved: dict[str, Any]) -> list[str]:
    permits_summary = resolved.get("permits_summary", {})
    permit_history = permits_summary.get("permit_history", [])
    open_permits = set(permits_summary.get("open_permits", []))

    items = []
    if permit_history:
        for permit in permit_history:
            prefix = "Open permit" if permit in open_permits else "Permit"
            items.append(f"{prefix}: {permit}")
    else:
        items.append("No permit history was available.")
    return items


def _risks_and_questions(resolved: dict[str, Any]) -> list[str]:
    items = []
    for flag in resolved.get("flags", []):
        if flag.get("type") in {"conflict", "attention", "risk", "missing"}:
            items.append(flag["message"])

    if not items:
        items.append("No major risks or open questions were identified from the available data.")
    else:
        items.append("Next step: verify flagged conflicts, permits, and hazard items during diligence.")
    return items


def _confidence_notes(resolved: dict[str, Any]) -> list[str]:
    notes = []
    for field_name, field in resolved.get("resolved_facts", {}).items():
        confidence = field.get("confidence")
        reason = field.get("resolution_reason")
        notes.append(
            f"{field_name.replace('_', ' ').title()}: {confidence} confidence. {reason}"
        )

    if not notes:
        notes.append("Confidence notes are unavailable because no facts were resolved.")
    return notes


def generate_markdown_brief(resolved: dict[str, Any]) -> str:
    canonical_address = resolved.get("canonical_address") or "Unknown address"
    sections = [
        f"# Property Brief: {canonical_address}",
        "",
        "## Executive Summary",
        _executive_summary(resolved),
        "",
        "## Key Facts",
    ]

    sections.extend(f"- {item}" for item in _format_key_facts(resolved) or ["Limited key facts available."])
    sections.extend(
        [
            "",
            "## Renovation and Permit History",
        ]
    )
    sections.extend(f"- {item}" for item in _renovation_and_permits(resolved))
    sections.extend(
        [
            "",
            "## Risks / Open Questions",
        ]
    )
    sections.extend(f"- {item}" for item in _risks_and_questions(resolved))
    sections.extend(
        [
            "",
            "## Confidence Notes",
        ]
    )
    sections.extend(f"- {item}" for item in _confidence_notes(resolved))
    return "\n".join(sections) + "\n"
