from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class NormalizedAddress:
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    canonical_line: str | None = None


@dataclass(slots=True)
class SourceMetadata:
    source: str
    source_id: str | None = None
    fetched_at: str | None = None


@dataclass(slots=True)
class NormalizedPropertyFacts:
    property_type: str | None = None
    beds: int | float | None = None
    baths: int | float | None = None
    sqft: int | None = None
    lot_size_sqft: int | None = None
    year_built: int | None = None
    list_price: int | None = None
    annual_tax: int | None = None
    assessed_value: int | None = None
    last_sale_date: str | None = None
    last_sale_price: int | None = None
    hoa_monthly: int | None = None


@dataclass(slots=True)
class NormalizedPermit:
    permit_id: str | None = None
    issue_date: str | None = None
    permit_type: str | None = None
    status: str | None = None
    description: str | None = None


@dataclass(slots=True)
class NormalizedSaleEvent:
    date: str | None = None
    price: int | None = None
    buyer: str | None = None
    seller: str | None = None


@dataclass(slots=True)
class NormalizedHazards:
    flood_zone: str | None = None
    flood_risk_level: str | None = None
    flood_insurance_required: bool | None = None
    wildfire_risk_level: str | None = None
    heat_risk_level: str | None = None
    air_quality_risk_level: str | None = None


@dataclass(slots=True)
class NormalizedDisclosure:
    known_issues: list[str] = field(default_factory=list)
    systems: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class NormalizedSourceRecord:
    metadata: SourceMetadata
    address: NormalizedAddress = field(default_factory=NormalizedAddress)
    facts: NormalizedPropertyFacts = field(default_factory=NormalizedPropertyFacts)
    permits: list[NormalizedPermit] = field(default_factory=list)
    sales: list[NormalizedSaleEvent] = field(default_factory=list)
    hazards: NormalizedHazards = field(default_factory=NormalizedHazards)
    disclosure: NormalizedDisclosure = field(default_factory=NormalizedDisclosure)
    raw_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
