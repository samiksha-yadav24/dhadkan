# ADR 0006: NFHS-6 data scope and checks

**Status:** Accepted
**Date:** 2026-11-12

## Context
NFHS-6 fact sheets are PDFs. Numbers copied or extracted by hand or code can
be wrong, and a wrong number on a health chart misleads people.

## Decision
- NFHS-6 is the only survey in v1. Indicators: blood pressure and blood sugar.
- The raw PDF is not committed; its URL, access date and SHA-256 are recorded.
- Every extracted table must pass consistency checks (range, total between
  urban and rural, parts not exceeding whole, completeness).
- Maharashtra, checked by hand against the PDF, is the answer key that the
  extractor must reproduce exactly.

## Alternatives considered
- NFHS-5 as well: indicators and sampling differ; adds caveats for no gain.
- Third-party CSVs: unofficial and only a few states.

## Consequences
Smaller scope, but every number can be traced and tested. Mistakes like a
mis-copied cell are caught automatically.
