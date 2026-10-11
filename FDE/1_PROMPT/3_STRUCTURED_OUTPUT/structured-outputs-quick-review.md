# Structured Outputs: Quick Review (Module 3 · Lesson 3.3)
**OpenAI JSON mode vs Anthropic tool-use**

## The Big Idea
Both providers can force a model's reply into a fixed shape. The wire formats differ, but they **consume the same Pydantic schema** (`model_json_schema()`). Put a **validation layer + recovery ladder** in front of either one so "wrong shape" becomes an automatic retry, not a 3 AM page.

**The story:** After a model update, tool-use shape compliance dropped from about 99.8% to about 99.5% (3 bad calls per 1,000). The discriminated union caught them with a clean `ValidationError`. A 4-rung recovery ladder got conformance back to about 99.8%, with no P0 tickets.

---

## 1. Two Providers, One Pydantic Schema

| | **OpenAI Structured Outputs** | **Anthropic tool-use-for-JSON** |
|---|---|---|
| How | `responses.parse(..., text_format=Model)` | One tool in `tools=[...]` + `tool_choice` forcing it |
| Guarantee | Schema conformance at **token-decoding** level (strict) | Lenient by default; add `"strict": true` for a guarantee |
| Result read from | `response.output_parsed` | the `tool_use` block's `.input` |
| Schema rules | `additionalProperties: false` everywhere; recursion depth ≤ 5 | JSON Schema 2020-12, **no top-level `oneOf`** |

- **Anthropic tool-use** needs `tool_choice={"type":"tool","name":"..."}` to force the call. Declaring the tool alone isn't enough.
- Result: same typed Pydantic object from both providers, so downstream code is provider-agnostic.

---

## 2. Anthropic Native Structured Outputs (Nov 2025+)
- Tool indirection is **no longer needed** for plain JSON answers.
- Two switches:
  - `output_config.format` = JSON schema, enforced at decoding level (OpenAI-strict-style)
  - `"strict": true` on a tool definition = tool input guaranteed to match its schema
- Numeric bounds (`ge`/`le`, min/max) aren't supported on the wire. Keep them in Pydantic for validation.
- **Tool-use-for-JSON is now the legacy pattern.** You'll still see it in production, and it's the right choice when you actually want a tool call (L3.4).

**Which to use when:**
- **OpenAI Structured Outputs:** single schema, simplest API
- **Anthropic native (`output_config`):** plain JSON answers on a current SDK
- **Anthropic tool use:** multi-tool decisions or older stacks

---

## 3. Discriminated Unions (multi-intent outputs)
- Use when one ticket can map to different actions with **different fields** (refund, access, escalate, ...).
- `Field(discriminator="type")` with `type: Literal["refund"]` etc. The model commits to one shape first, then fills fields.
- **Benefit over a bare `Union`:** hybrid responses raise a clean `ValidationError` instead of silently routing to whichever sub-model accepts first.
- Catches about the 20% multi-intent tail. Cost: more complex schemas.
- **Skip it** for single-intent classification. A flat enum is simpler.
- **Gotcha:** discriminator must be a **non-nullable** `Literal`.

---

## 4. Schema Flattening (one model, both providers)
Three rules fix about 90% of "provider rejects my schema" errors:
1. **`additionalProperties: false` on every object**, via `model_config = ConfigDict(extra="forbid")` on every `BaseModel`
2. **No top-level `oneOf`**: wrap unions in a parent `BaseModel` (e.g. `AgentResponse` with an `action` field)
3. **Recursive `$ref` max depth 5** (bound it with `max_length` or bounded modeling)

Don't keep a separate Pydantic model per provider. That doubles maintenance.

---

## 5. The 4-Rung Recovery Ladder
When the model returns the wrong shape anyway:

| Rung | Step | What it does |
|------|------|--------------|
| 1 | **Validate** | `model_validate()`; catch `ValidationError`, keep `.errors()` |
| 2 | **Re-prompt** | Resend request + the validation error + "fix the JSON". Fixes most cases |
| 3 | **Repair** | `json-repair` library fixes trailing commas, braces, quoted ints. Cheap, no LLM call |
| 4 | **Escalate** | Stronger model (Haiku → Sonnet) or domain default + log for the snapshot suite |

- Typical split: about 99.5% pass on rung 1, 0.4% rung 2, 0.08% rung 3, 0.02% rung 4.
- Skip retries = lose about 5% of calls. Run all 4 rungs always = double cost. Calibrate per workload.
- **Interview signal:** Name all 4 rungs, `json-repair` for rung 3, and the Haiku → Sonnet escalation. Not just "retry."

---

## 6. Picking a Provider per Workload

| Workload | Pick | Why |
|----------|------|-----|
| High-volume, simple schema (ticket triage) | **OpenAI Structured Outputs** | Token-level guarantee, simpler ops |
| Nuanced multilingual / compliance-bound agent | **Anthropic tool-use + Sonnet 5 + ladder** | Better reasoning; ladder catches drift after model updates |
| Regional / sovereign deployment | **Regional provider** (Mistral EU, Qwen CJK; OpenAI-compatible JSON mode) | Language coverage + data residency |
| Migration eval | Same schema, fan out to all providers | Fair comparison |

- OpenAI: >10K calls/day, simple schema, latency-sensitive.
- Anthropic: multi-tool workloads.
- **Mistake:** Choosing a provider by fashion instead of by measurement.

---

## 7. Five Production Gotchas
1. **Two different "JSON modes":** `{"type":"json_object"}` = any valid JSON (unconstrained). `{"type":"json_schema","strict":true}` = the strict one. Mixing them up is the #1 bug.
2. **Nullable discriminator:** Pydantic v2 raises at class definition.
3. **Ladder infinite loop:** If escalation reuses the same wrapper, it recurses forever. Cap at **one** escalation, then raise.
4. **`content[0]` isn't always the tool call:** There may be a text block first. Loop and pick `type == "tool_use"`.
5. **Pydantic upgrade changes schema output:** Pin the version and re-run the snapshot suite on every upgrade.

---

## 8. Real-World Cases
- **Code-mixed input:** Models emit string amounts ("$5,000.00") instead of ints. Rung 2 (re-prompt with the error) fixes it in one round.
- **Regional providers:** Mistral, Qwen, DeepSeek and open models ship OpenAI-compatible JSON modes. Same schema, different endpoint URL, good for customers who refuse US egress.
- **PII boundary:** `Annotated[str, AfterValidator(strip_pii)]` strips sensitive data (SSN, card, IBAN) at the boundary. Aligns with GDPR Art. 5 / 32, CCPA, HIPAA. Reused as the input filter in L3.7.

---

## 9. Analogy: Passport Office
- **OpenAI strict** = online form that won't submit until every field is valid (checked at the keyboard).
- **Anthropic tool-use** = clerk at the counter who hand-checks and returns bad forms.
- **Where it breaks down:** Real schemas keep changing (new intents, new compliance fields), and LLM errors are vague ("JSON parse failed"), not specific like form software. That's why the ladder exists.

---

## 10. Quiz Answers (Self-Check)
| Q | Answer | Why |
|---|--------|-----|
| Q1 | **c** | Strict mode guarantees schema conformance at the token-decoding layer |
| Q2 | **b** | Need `tool_choice={"type":"tool","name":"..."}` to force the tool |
| Q3 | **b** | Discriminator = single-model lookup; hybrids raise a clean `ValidationError` |
| Q4 | **c** | Missing `additionalProperties: false`, or recursive `$ref` over depth 5 |
| Q5 | **b** | Validate → re-prompt with error → deterministic repair → escalate |

---

## 11. Quick Memory Hooks
- **One Pydantic schema, two providers:** `model_json_schema()`
- **OpenAI** = `text_format` (strict, token-level) | **Anthropic** = `output_config` (new) or tool + `tool_choice` (legacy)
- **Ladder:** Validate → Re-prompt → Repair → Escalate ("VRRE")
- **Flatten:** `extra="forbid"`, no top-level `oneOf`, recursion ≤ 5
- **Discriminated union** = no silent mis-routing
- **Never "just retry"**
- **Pin Pydantic, re-run snapshots**
