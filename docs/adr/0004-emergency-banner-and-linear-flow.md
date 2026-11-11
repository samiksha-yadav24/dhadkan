# ADR 0004: Emergency banner above protocols; linear flow

**Status:** Accepted
**Date:** 2026-11-02

## Context
ADR 0002 said the first instruction is always to call emergency services.
The COLS algorithm (S1, S2) checks scene safety and response before calling,
so forcing the call as step 1 would contradict the source.

## Decision
1. Every rendered output begins with an emergency banner built from
   emergency_numbers.yaml. Protocol content cannot remove or reorder it.
2. Protocols are a linear list of steps; each step may carry a condition
   shown in text. No branching tree in v1.
3. Draft protocols display a visible "not clinician-reviewed" notice.

## Alternatives considered
- Forcing "call" as step 1: conflicts with the source order.
- A branching decision tree: needs schema changes and more content to verify.

## Consequences
Source order is preserved and the emergency number is never missing.
Branching can be added later if a clinician asks for it.
