# ADR 0003: v1 feature scope

**Status:** Accepted
**Date:** 2026-10-31

## Context
Similar apps exist. This project is a portfolio piece that should show
engineering quality, not feature count. Medical features need verified content.

## Decision
v1 includes: offline PWA, validated content, CPR metronome (Web Audio clock),
spoken prompts with text fallback, rescuer-swap prompt driven by content,
risk-awareness questionnaire, regional charts, Hindi and Marathi.
Deferred to v2: accelerometer rate feedback, practice scoring.
Excluded: paramedic reports (needs stored data), multi-country numbers
(needs per-country verified sources).

## Alternatives considered
- Adding every suggested feature: more surface to verify and test, higher risk.
- Accelerometer coaching in v1: depth cannot be measured reliably; wrong
  feedback is a safety risk.

## Consequences
A smaller product that can be fully tested and clinician-reviewed.
The swap interval and compression rate are content values with sources,
added to the schema once the guideline conflicts are resolved.
