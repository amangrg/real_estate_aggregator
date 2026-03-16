from __future__ import annotations

from .models import NormalizedSourceRecord


def normalize_listing(raw: dict) -> NormalizedSourceRecord:
    raise NotImplementedError("Listing normalization is not implemented yet.")


def normalize_tax_record(raw: dict) -> NormalizedSourceRecord:
    raise NotImplementedError("Tax record normalization is not implemented yet.")


def normalize_permit_record(raw: dict) -> NormalizedSourceRecord:
    raise NotImplementedError("Permit record normalization is not implemented yet.")


def normalize_hazard(raw: dict) -> NormalizedSourceRecord:
    raise NotImplementedError("Hazard normalization is not implemented yet.")


def normalize_sale_history(raw: dict) -> NormalizedSourceRecord:
    raise NotImplementedError("Sale history normalization is not implemented yet.")


def normalize_disclosure(raw: dict) -> NormalizedSourceRecord:
    raise NotImplementedError("Disclosure normalization is not implemented yet.")
