# ADR 0001: Medical content lives in validated YAML, not code

**Status:** Accepted

**Date:** 2026-10-24

## Context

Dhadkan gives emergency guidance, so every piece of medical content must be
traceable to a published source, reviewable by a clinician who does not read
code, and updatable without changing program logic.

## Decision

All protocols are stored as YAML files in `content/`. Pydantic schemas validate
every file. Each step must reference a source, and each protocol must carry a
review record (reviewer, date, version). CI rejects content that fails
validation.

## Alternatives considered

- **Hardcoding content in Python:** mixes medical text with logic, so a
  clinician cannot review it and every wording change needs a code change.
- **A database:** adds infrastructure and hides content from version control,
  which makes review history harder to see.

## Consequences

- Clinicians can review content as plain text.
- Adding or correcting a protocol requires no code change.
- Git history becomes an audit trail of every content change.
- The schema is the safety gate: invalid or unsourced content cannot ship.
