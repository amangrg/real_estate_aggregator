from __future__ import annotations

import re

from .models import NormalizedAddress


_SUFFIX_REPLACEMENTS = {
    "drive": "Dr",
    "street": "St",
    "road": "Rd",
    "avenue": "Ave",
}


def _normalize_street_suffix(street: str | None) -> str | None:
    if not street:
        return None

    parts = street.strip().split()
    if not parts:
        return None

    suffix_key = parts[-1].lower().rstrip(".")
    if suffix_key in _SUFFIX_REPLACEMENTS:
        parts[-1] = _SUFFIX_REPLACEMENTS[suffix_key]
    return " ".join(parts)


def canonicalize_address(
    *,
    street: str | None,
    city: str | None,
    state: str | None,
    zip_code: str | None,
) -> NormalizedAddress:
    normalized_street = _normalize_street_suffix(street)
    normalized_city = city.strip() if city else None
    normalized_state = state.strip().upper() if state else None
    normalized_zip = zip_code.strip() if zip_code else None

    parts = [
        part
        for part in (normalized_street, normalized_city, normalized_state, normalized_zip)
        if part
    ]
    canonical_line = ", ".join(parts[:3])
    if normalized_zip:
        canonical_line = f"{', '.join(parts[:3])} {normalized_zip}".strip()
    canonical_line = canonical_line or None

    return NormalizedAddress(
        street=normalized_street,
        city=normalized_city,
        state=normalized_state,
        zip=normalized_zip,
        canonical_line=canonical_line,
    )


def slugify_address(canonical_line: str | None) -> str | None:
    if not canonical_line:
        return None
    slug = re.sub(r"[^a-z0-9]+", "-", canonical_line.lower()).strip("-")
    return slug or None
