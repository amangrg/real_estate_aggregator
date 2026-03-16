# Property Brief Prototype

A lightweight prototype that turns scattered, inconsistent property data into a structured buyer-facing brief.

## Problem

Information about a real estate property is often spread across listings, tax records, permit systems, hazard datasets, and disclosures. These sources are incomplete, inconsistent, and sometimes contradictory. Buyers should not have to manually reconcile all of this before deciding whether a home is worth pursuing.

This prototype demonstrates the core workflow:

1. Ingest property data from multiple sources
2. Normalize it into a common schema
3. Resolve conflicts using explicit rules
4. Generate a concise property brief with confidence labels, risks, and unresolved questions

## Scope

This is a time-boxed prototype, optimized for clarity and end-to-end functionality rather than breadth.

It uses sample JSON fixtures representing common data sources for a single property:

- listing data
- tax record
- permit history
- hazard/risk data
- sale history
- seller disclosure

The goal is to show the core product logic, not production-scale integrations.

## Repository Structure

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
│   ├── listing.json
│   ├── tax_record.json
│   ├── permit_record.json
│   ├── hazard.json
│   ├── sale_history.json
│   └── disclosure.json
├── output/
│   ├── resolved_property.json
│   └── property_brief.md
└── tests/
    ├── test_normalize.py
    ├── test_resolve.py
    └── test_summarize.py
```

## How It Works

### 1. Ingest
The system reads raw source files for the same property from the `data/` directory.

### 2. Normalize
Each source is converted into a common internal representation so downstream logic can work with consistent field names and types.

Examples:
- `sqft`
- `beds`
- `baths`
- `year_built`
- `annual_tax`
- `permits`
- `hazards`

### 3. Resolve
When sources disagree, the system applies simple, explainable rules.

Examples:
- prefer tax record for `year_built`
- prefer listing for `list_price`
- if two sources disagree on `sqft`, choose a preferred source but preserve the conflict
- attach a confidence level and resolution reason

### 4. Summarize
The system generates:
- a resolved property JSON
- a buyer-facing markdown brief

The brief includes:
- executive summary
- key facts
- permit and renovation summary
- risks / open questions
- confidence notes

## Why This Approach

Given the short time-box, I focused on the highest-value vertical slice:

- clear multi-source ingestion
- explicit normalization
- conflict handling
- trust-aware summary generation

I intentionally did not spend time on:
- live MLS integrations
- production databases
- auth
- frontend polish
- LLM orchestration
- large-scale crawling or scraping

Those would be the next steps in a real product, but they would distract from demonstrating the core decision-support logic here.

## Data Strategy

For this prototype, I used representative sample data files rather than live data integrations.

This was intentional:
- it keeps the submission runnable and deterministic
- it avoids API setup and licensing constraints
- it allows the core reasoning pipeline to be evaluated directly

In a real implementation, likely data sources would include:
- county assessor / tax records
- deed / ownership history
- permit portals
- hazard and geospatial datasets
- MLS or licensed listing feeds
- seller disclosures and inspection documents

## Trade-offs

### What I optimized for
- end-to-end completeness
- explainability
- readability
- easy local execution
- explicit handling of uncertainty

### What I traded away
- coverage across many property types
- sophisticated entity resolution
- probabilistic confidence modeling
- UI polish
- real-time updates
- production-grade source reliability logic

## Example Output

### Example resolved fact
- Listing sqft: 1842
- Tax record sqft: 1836
- Resolved value: 1842
- Confidence: Medium
- Resolution note: listing used because it is the more recent source, but conflict preserved

### Example risk flag
- Electrical permit from 2021 remains open

### Example buyer action item
- Verify whether the 2021 electrical permit has been finalized

## How to Run

### Install
```bash
pip install -r requirements.txt
```

### Execute
```bash
python main.py
```

### Expected outputs
The script should produce:
- `output/resolved_property.json`
- `output/property_brief.md`

## Tests

Run:
```bash
pytest
```

Suggested tests:
- field normalization works for each source
- conflict resolution rules behave as expected
- summary generation includes required sections
- missing data does not crash the pipeline

## What I Would Do With More Time

If I had more time, I would extend this in the following order:

### 1. Stronger entity resolution
Match records using normalized address, parcel ID, and geospatial signals.

### 2. Better confidence scoring
Use source reliability, agreement count, and recency to compute field-level confidence more systematically.

### 3. Document parsing
Extract key claims from disclosures, inspection reports, and permit PDFs.

### 4. Source provenance in the brief
Allow users to click into each claim and see exactly which source supported it.

### 5. Lightweight frontend
A simple web UI where a user selects a property and views the generated brief.

### 6. Real data connectors
Integrate with public county records and permit portals for a single jurisdiction as a first live slice.

## Design Notes

The core product principle behind this prototype is:

> do not hide uncertainty; make it visible and useful.

For a homebuyer, a trustworthy brief is not one that sounds certain. It is one that clearly distinguishes:
- verified facts
- likely facts
- conflicting facts
- missing facts
- next things to verify

That is the foundation this prototype is designed to demonstrate.

## Suggested Commit History

A good commit sequence for this project would look like:

- `init repo and scaffold project structure`
- `add sample multi-source property fixtures`
- `implement normalized property schema`
- `add source ingestion and normalization`
- `implement field conflict resolution rules`
- `generate markdown property brief`
- `add tests for normalize and resolve modules`
- `improve README and design notes`

## Notes

This repository is intended as a prototype submission for a time-boxed exercise. The main value is in the structure of the solution and the product reasoning behind it, not in broad real-estate data coverage.
