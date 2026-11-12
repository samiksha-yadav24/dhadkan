# ADR 0005: How risk is presented

**Status:** Accepted
**Date:** 2026-11-12

## Context
IDRS (S6) is a diabetes screening score. Its positive predictive value at the
cutoff is 17% and it was derived in one Chennai study.

## Decision
- Use only Table 1 and the single cutoff of 60 from S6. No low/moderate/high
  tiers, because they are not in the paper.
- Output says "consider screening" and "not a diagnosis"; never "you have".
- Always state that it covers diabetes, not heart attack risk, and give the
  study's 17% figure.
- Input limits (adults 18-110, waist 40-200 cm) are our own design choices.
- Scoring tables live in code now; in Movement 5 they are exported to the
  bundle so the phone app does not duplicate them.

## Alternatives considered
- Three risk tiers from later studies: gap at 51-59 and a different source.
- Calling it a heart risk score: false, and unsafe to imply.

## Consequences
Honest, narrow, and easy to defend. A clinician can check it against S6 alone.
