# Refund Agent Evaluation

- Accuracy: 17/50 (34.0%); Wilson 95% CI 22.4% to 47.8%.
- Mean model rounds: 2.00.
- P95 end-to-end latency: 7.399 seconds.
- Cost not estimated: configure Together input/output rates.
- Duplicate process attempts stopped by idempotency: 0.

## Tool Description Finding
Explicit WHEN, WHEN NOT, prerequisites, and side-effect descriptions make the allowed workflow easier to follow. Python independently enforces refund eligibility; the prompt is not an authorization boundary.

## Production Gaps
1. Redact sensitive values and review retention before logging prompts or tool payloads.
2. Replace the in-memory idempotency ledger with a durable, atomic store shared by workers.
3. Define bounded retries, backoff, timeout handling, and human review for uncertain outcomes.

Rate-card estimates use configured values and may drift. All identifiers and records in this exercise are synthetic.
