# Property Brief Prototype

A lightweight prototype that turns scattered, inconsistent property data into a structured buyer-facing property brief.

## What It Does

This repository demonstrates a small, explainable real-estate intelligence workflow for a single property:

1. load multiple source records from local JSON fixtures
2. normalize each source into a common internal schema
3. resolve overlapping facts with deterministic conflict rules
4. generate a concise markdown brief that surfaces risks and uncertainty

The emphasis is on trust and clarity rather than coverage or production integrations.

## Current Status

Implemented:

- fixture ingestion from `data/`
- typed normalized source models
- source-specific normalization for listing, tax, permits, hazards, sale history, and disclosure
- field-level conflict resolution with confidence labels and conflict preservation
- permit and hazard flag generation
- markdown brief generation
- a CLI entrypoint that writes resolved JSON and markdown output files
- a local web frontend for browsing the generated property brief and resolved facts
- unit tests for ingest, normalize, resolve, and summarize modules

Not implemented yet:

- live data connectors

## Repository Structure

```text
real_estate_aggregator/
|-- README.md
|-- SPECS.md
|-- frontend/
|   |-- index.html
|   |-- app.js
|   `-- styles.css
|-- data/
|   |-- listing.json
|   |-- tax_record.json
|   |-- permit_record.json
|   |-- hazard.json
|   |-- sale_history.json
|   `-- disclosure.json
|-- src/
|   |-- __init__.py
|   |-- ingest.py
|   |-- models.py
|   |-- normalize.py
|   |-- resolve.py
|   |-- summarize.py
|   `-- utils.py
`-- tests/
    |-- test_ingest.py
    |-- test_main.py
    |-- test_normalize.py
    |-- test_resolve.py
    |-- test_server.py
    `-- test_summarize.py
```

## How The Pipeline Works

### 1. Ingest

`src/ingest.py` loads required and optional JSON fixtures from `data/`.

- required: `listing.json`, `tax_record.json`, `permit_record.json`, `hazard.json`
- optional: `sale_history.json`, `disclosure.json`

The loader raises explicit errors for missing required files and malformed JSON.

### 2. Normalize

`src/normalize.py` converts each source into the same `NormalizedSourceRecord` shape defined in `src/models.py`.

Examples of normalized fields:

- `property_type`
- `beds`
- `baths`
- `sqft`
- `lot_size_sqft`
- `year_built`
- `list_price`
- `annual_tax`
- `last_sale_date`
- `last_sale_price`

Address normalization is intentionally simple and fixture-oriented. For example, `Drive` is canonicalized to `Dr` so the current listing and tax record collapse to the same canonical address.

### 3. Resolve

`src/resolve.py` applies explicit source preference rules and preserves disagreement instead of hiding it.

Examples:

- prefer listing for `list_price`
- prefer tax record for `year_built`
- prefer listing for `sqft`, but keep tax as a conflict source when values differ
- prefer sale history for `last_sale_date` and `last_sale_price`

Each resolved fact includes:

- `value`
- `confidence`
- `sources`
- `resolution_reason`
- `conflict` when applicable

The resolver also produces:

- `permits_summary`
- `hazards_summary`
- `flags` for conflicts, open permits, risk signals, and missing important fields

### 4. Summarize

`src/summarize.py` turns the resolved property object into a reviewer-friendly markdown brief with:

- title
- executive summary
- key facts
- renovation and permit history
- risks / open questions
- confidence notes

### 5. Frontend

`src/server.py` serves a small single-page frontend from `frontend/` and exposes:

- `/api/property` for the resolved JSON payload
- `/api/brief` for the generated markdown brief
- `/resolved_property.json` and `/property_brief.md` for direct downloads

The UI presents:

- a headline property summary
- resolved fact cards with confidence and conflict context
- flags, permits, and hazards
- the rendered buyer brief
- the raw resolved JSON

## Example From The Current Fixtures

The sample property resolves to:

- canonical address: `1428 Maple Creek Dr, Austin, TX 78748`
- property id: `1428-maple-creek-dr-austin-tx-78748`
- 12 resolved facts
- 6 flags

Current notable flags:

- square footage conflict between listing and tax record
- lot size conflict between listing and tax record
- year built conflict between listing and tax record
- one open electrical permit from 2021
- moderate heat risk
- elevated insurance-cost note from the hazard provider

## How To Run

Generate outputs with:

```bash
python main.py
```

By default this writes:

- `output/resolved_property.json`
- `output/property_brief.md`

The CLI also prints the property id, canonical address, and generated file locations.

Optional arguments:

```bash
python main.py --data-dir data --output-dir output
```

Run the frontend locally with:

```bash
python main.py --serve
```

Custom host and port:

```bash
python main.py --serve --host 127.0.0.1 --port 8000
```

If you want to use the lower-level library entrypoints directly:

```python
from src.ingest import load_sources
from src.normalize import normalize_sources
from src.resolve import resolve_property
from src.summarize import generate_markdown_brief

raw_sources = load_sources("data")
normalized_sources = normalize_sources(raw_sources)
resolved = resolve_property(normalized_sources)
brief = generate_markdown_brief(resolved)

print(resolved["property_id"])
print(brief)
```

## Tests

Run the full suite with:

```bash
python -m unittest tests.test_ingest tests.test_normalize tests.test_resolve tests.test_summarize tests.test_main tests.test_server
```

The current suite covers:

- required vs optional file handling
- address canonicalization and source normalization
- conflict resolution rules and flag generation
- markdown brief structure and sparse-data behavior
- CLI output writing
- frontend API and static asset serving

## Design Notes

### Product Principle

The most important design choice in this prototype is simple:

> do not hide uncertainty; make it visible and useful

A buyer-facing property brief should not flatten conflicts into a false sense of certainty. If sources disagree, the system should choose a value explicitly, explain why, and preserve the disagreement for review.

### Why Deterministic Rules

This prototype uses deterministic rules instead of learned scoring because the goal is explainability.

- a reviewer can understand every resolution decision quickly
- test coverage is straightforward
- the pipeline remains stable and reproducible
- future confidence logic can build on a clear baseline instead of replacing hidden heuristics

### Schema Strategy

All source normalizers map into the same `NormalizedSourceRecord` envelope.

That keeps downstream code simple:

- the resolver reads the same field names regardless of source
- source-specific extras remain available in `raw_context`
- future sources can plug into the pipeline without changing the resolver contract

### Trade-offs

Optimized for:

- clarity
- explainability
- local runnability
- deterministic behavior
- reviewer speed

Intentionally not optimized for:

- broad MLS-style schema coverage
- multi-property entity resolution
- probabilistic confidence scoring
- live integrations
- UI polish

### What I Would Build Next

The next practical steps would be:

1. include disclosure signals more directly in the resolved output and brief
2. improve confidence scoring with recency and source-authority inputs
3. support multiple properties and stronger address / parcel matching
4. support multiple properties in the frontend instead of a single fixture-backed property view
5. add packaging or a small installer so the CLI and frontend are easier to launch for non-developers

## Notes

This repository is still a prototype submission, not a production system. The value is in the structure of the reasoning pipeline and the visibility of uncertainty, not in comprehensive real-estate coverage.
