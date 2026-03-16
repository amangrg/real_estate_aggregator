from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_SOURCE_FILES = {
    "listing": "listing.json",
    "tax_record": "tax_record.json",
    "permit_record": "permit_record.json",
    "hazard": "hazard.json",
}

OPTIONAL_SOURCE_FILES = {
    "sale_history": "sale_history.json",
    "disclosure": "disclosure.json",
}


def _load_json_file(path: Path, *, required: bool) -> dict[str, Any] | None:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Required source file not found: {path}")
        return None

    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in source file: {path}") from exc


def load_sources(data_dir: str | Path) -> dict[str, dict[str, Any]]:
    base_path = Path(data_dir)
    sources: dict[str, dict[str, Any]] = {}

    for source_name, filename in REQUIRED_SOURCE_FILES.items():
        payload = _load_json_file(base_path / filename, required=True)
        sources[source_name] = payload

    for source_name, filename in OPTIONAL_SOURCE_FILES.items():
        payload = _load_json_file(base_path / filename, required=False)
        if payload is not None:
            sources[source_name] = payload

    return sources
