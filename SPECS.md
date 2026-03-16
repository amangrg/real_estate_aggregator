# SPECS.md

## Goal

Build a small, runnable prototype that takes multiple records for the same real-estate property, reconciles them, and produces a concise buyer-facing property brief.

This is a single-property vertical slice, not a production platform.

The agent should prioritize:
1. correctness
2. clarity
3. explainability
4. local runnability
5. simple tests

Do not over-engineer.

---

## Product Behavior

The system should:

1. Read multiple JSON files representing different sources for one property
2. Normalize them into a common schema
3. Resolve overlapping or conflicting fields using simple deterministic rules
4. Generate:
   - a machine-readable resolved JSON record
   - a human-readable markdown brief

The output should make uncertainty visible rather than hiding it.

---

## Inputs

Expected input files live under `data/`.

Required files:
- `listing.json`
- `tax_record.json`
- `permit_record.json`
- `hazard.json`

Optional files:
- `sale_history.json`
- `disclosure.json`

Assume all provided files refer to the same property, but the code should still normalize addresses into a canonical format.

---

## Outputs

Write outputs to `output/`.

Required output files:
- `output/resolved_property.json`
- `output/property_brief.md`

---

## Required Project Structure

```text
property-brief/
├── README.md
├── SPECS.md
├── requirements.txt
├── main.py
├── src/
│   ├── ingest.py
│   ├── normalize.py
│   ├── resolve.py
│   ├── summarize.py
│   ├── models.py
│   └── utils.py
├── data/
├── output/
└── tests/
```

If a slightly different structure is more practical, keep it minimal and easy to understand.

---

## Functional Requirements

### 1. Ingestion
Implement a simple ingestion layer that:
- reads JSON files from `data/`
- returns raw Python dictionaries
- gracefully handles optional missing files
- raises clear errors for malformed required files

### 2. Normalization
Implement normalization functions for each source type.

Each source should be mapped into a common internal representation where relevant.

At minimum, normalize these fields if available:
- address
- property_type
- beds
- baths
- sqft
- lot_size_sqft
- year_built
- list_price
- annual_tax
- assessed_value
- last_sale_date
- last_sale_price
- hoa_monthly
- permits
- hazard signals
- disclosure notes / known issues

Normalization should:
- standardize address formatting
- preserve source name
- preserve fetch timestamp if present
- preserve raw values if useful for debugging

### 3. Resolution
Implement deterministic field-level conflict resolution.

The resolver must:
- choose a resolved value for important overlapping fields
- preserve conflicts when they exist
- assign a confidence level
- provide a short `resolution_reason`

At minimum, resolve:
- property_type
- beds
- baths
- sqft
- lot_size_sqft
- year_built
- list_price
- annual_tax
- last_sale_date
- last_sale_price

### 4. Brief generation
Generate a markdown brief with the following sections:

1. Title
2. Executive Summary
3. Key Facts
4. Renovation and Permit History
5. Risks / Open Questions
6. Confidence Notes

Keep the brief concise and structured.

### 5. Flags
Generate a list of flags for:
- source conflicts
- open permits
- missing important data
- noteworthy hazard conditions

These flags should appear in:
- `resolved_property.json`
- `property_brief.md`

---

## Resolution Rules

Use simple, explainable heuristics.

### General
- If multiple sources agree exactly, confidence is higher
- If only one source provides a field, confidence is lower unless the source is especially authoritative
- If sources disagree, keep the chosen value and record the alternatives

### Suggested field rules

#### `property_type`
- prefer listing
- else take first available

#### `beds`
- if listing and tax match, use that value with High confidence
- if mismatch, prefer listing and record conflict with Medium confidence

#### `baths`
- same logic as beds

#### `sqft`
- prefer listing if present
- if tax differs, record conflict
- confidence:
  - High if same
  - Medium if small conflict
  - Low if major conflict

A "small conflict" can be defined as an absolute difference <= 100 sqft.

#### `lot_size_sqft`
- prefer listing if present
- record conflict if tax differs
- confidence Low if values differ

#### `year_built`
- prefer tax record
- if listing differs, record conflict
- confidence Medium on disagreement

#### `list_price`
- prefer listing
- High confidence if present

#### `annual_tax`
- prefer tax record
- High confidence if present

#### `last_sale_date` and `last_sale_price`
- prefer sale history if present
- fall back to tax record
- High confidence if sale history and tax agree
- Medium if only one source exists
- Medium if disagreement and one is clearly preferred

### Permits
Summarize permits into human-readable strings.
Flag any permit with status such as:
- `Open`
- `Pending`
- `Incomplete`

### Hazards
At minimum, surface:
- flood risk
- wildfire risk
- any insurance note

If hazard values are missing, omit them cleanly.

---

## Output Schema Expectations

### `resolved_property.json`
Must contain at least:

```json
{
  "property_id": "string",
  "canonical_address": "string",
  "resolved_facts": {},
  "permits_summary": {},
  "hazards_summary": {},
  "flags": []
}
```

### `resolved_facts`
Each resolved fact should look roughly like:

```json
{
  "value": 1842,
  "confidence": "Medium",
  "sources": ["listing", "tax_record"],
  "conflict": {
    "listing": 1842,
    "tax_record": 1836
  },
  "resolution_reason": "Used listing sqft because difference is small and listing is more recent."
}
```

Not every field needs a `conflict` block if no conflict exists.

### `flags`
Each flag should look like:

```json
{
  "type": "conflict",
  "message": "Square footage differs between listing and tax record."
}
```

Allowed flag types:
- `conflict`
- `attention`
- `missing`
- `risk`

---

## Markdown Brief Expectations

The markdown brief should be readable and concise.

### Required format

```md
# Property Brief: <address>

## Executive Summary
...

## Key Facts
- ...
- ...

## Renovation and Permit History
- ...
- ...

## Risks / Open Questions
- ...
- ...

## Confidence Notes
- ...
- ...
```

### Content guidance
The brief should:
- summarize the property clearly
- mention major recent permits
- mention notable conflicts
- mention at least one buyer next-step if applicable
- avoid exaggerated certainty

Do not fabricate facts not present in the inputs.

---

## Non-Functional Requirements

### Code quality
- keep modules small
- use type hints where practical
- prefer simple dataclasses or typed dicts
- avoid unnecessary dependencies

### Runtime
- must run locally with a simple `python main.py`

### Dependencies
Use only lightweight dependencies.
Preferred:
- standard library
- optionally `pydantic` or `dataclasses`
- `pytest` for tests

Do not depend on:
- external APIs
- web scraping
- databases
- cloud services
- LLM APIs

### Robustness
- code should not crash if optional files are missing
- required file errors should be explicit
- summary generation should degrade gracefully when some fields are absent

---

## Suggested Implementation Plan

### `src/ingest.py`
Responsibilities:
- load JSON files
- expose a function like `load_sources(data_dir: str) -> dict`

### `src/normalize.py`
Responsibilities:
- normalize each source independently
- expose functions like:
  - `normalize_listing(raw)`
  - `normalize_tax_record(raw)`
  - `normalize_permit_record(raw)`
  - `normalize_hazard(raw)`
  - `normalize_sale_history(raw)`
  - `normalize_disclosure(raw)`

### `src/resolve.py`
Responsibilities:
- merge normalized sources
- resolve fields
- generate flags
- return resolved property object

Expose something like:
- `resolve_property(normalized_sources: dict) -> dict`

### `src/summarize.py`
Responsibilities:
- convert resolved object into markdown brief

Expose something like:
- `generate_markdown_brief(resolved: dict) -> str`

### `src/models.py`
Responsibilities:
- shared data structures or type definitions

### `src/utils.py`
Responsibilities:
- address normalization
- confidence helpers
- small formatting helpers

### `main.py`
Responsibilities:
- orchestrate full pipeline
- read from `data/`
- write outputs to `output/`

---

## Address Normalization

Implement a very simple canonicalizer.

It should:
- trim whitespace
- normalize common suffixes when practical:
  - `Drive` -> `Dr`
  - `Street` -> `St`
  - `Road` -> `Rd`
  - `Avenue` -> `Ave`
- build a canonical single-line address

Do not spend too much time on this. It just needs to be good enough for the provided fixtures.

---

## Property ID

Generate a stable property ID from canonical address.

Example:
- lowercase
- replace spaces and punctuation with hyphens

Example:
- `1428-maple-creek-dr-austin-tx-78748`

---

## Testing Requirements

Add a few focused tests.

### Minimum tests
1. normalization test for listing
2. normalization test for tax record
3. resolution test for `year_built`
4. resolution test for `sqft` conflict handling
5. summary generation test ensures required markdown headings exist

Do not overbuild the test suite.

---

## Acceptance Criteria

The solution is acceptable if:

1. `python main.py` runs without extra setup beyond installing requirements
2. output JSON and markdown files are created successfully
3. the JSON clearly shows resolved values, confidence, and conflicts
4. the markdown brief is readable and contains all required sections
5. open permits and field conflicts appear as flags
6. the repo is understandable to a reviewer in a few minutes

---

## Nice-to-Haves

Only do these if core functionality is already done.

- include a `raw_sources` section in output for debugging
- include `missing_fields` tracking
- include a tiny CLI argument for custom data/output directories
- include better confidence scoring based on source agreement count
- include seller disclosure notes in the executive summary

---

## Explicitly Out of Scope

Do not spend time on:
- frontend UI
- live MLS integration
- production database
- authentication
- vector search
- LLM API integration
- OCR / PDF parsing
- web scraping
- scaling to many properties

This should remain a small, polished prototype.

---

## Implementation Philosophy

Prefer a complete, explainable solution over an ambitious but unfinished one.

A reviewer should be able to see:
- how data enters the system
- how fields are normalized
- how conflicts are resolved
- how the final brief is generated

The prototype should feel like the foundation of a trustworthy property intelligence product.
