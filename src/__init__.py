"""Property brief prototype package."""

from .ingest import load_sources
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
from .normalize import (
    normalize_disclosure,
    normalize_hazard,
    normalize_listing,
    normalize_permit_record,
    normalize_sale_history,
    normalize_sources,
    normalize_tax_record,
)
from .resolve import resolve_property
from .summarize import generate_markdown_brief

__all__ = [
    "load_sources",
    "NormalizedAddress",
    "NormalizedDisclosure",
    "NormalizedHazards",
    "NormalizedPermit",
    "NormalizedPropertyFacts",
    "NormalizedSaleEvent",
    "NormalizedSourceRecord",
    "SourceMetadata",
    "normalize_disclosure",
    "normalize_hazard",
    "normalize_listing",
    "normalize_permit_record",
    "normalize_sale_history",
    "normalize_sources",
    "normalize_tax_record",
    "resolve_property",
    "generate_markdown_brief",
]
