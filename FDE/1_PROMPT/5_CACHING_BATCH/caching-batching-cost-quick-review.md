# Prompt Caching, Batching & Cost Engineering: Quick Review (Module 3 · Lesson 3.5)

## The Big Idea
Most production prompts re-send the same long stable prefix on every call. **Cache it** (about 10x cheaper), **batch** non-urgent work (about 50% off), and **track cost** so the CFO hears about the bill from your dashboard, not the invoice.

**The story:** A ticket classifier made about 50K calls/day with a ~200K-token stable prefix (system + help docs + tools + examples) = about 10 billion tokens/day, about **$20K/day**. Adding **one parameter** (`cache_control`) dropped it to about **$2K/day**. Same model, same accuracy.

---

## 1. The FinOps Toolkit (3 primitives)

| Tool | Use for | Saving |
|------|---------|--------|
| **Prompt caching** | Re-used stable prefixes (system + tools + RAG + examples) | About 90% on the cached part |
| **Batch API** | Non-realtime work (evals, overnight enrichment) | About 50%, 24h SLA |
| **Token economy** | Long chat histories (summarize / truncate / RAG) | Fewer tokens per call |

---

## 2. Anthropic Prompt Caching

**Key numbers:**
- **Cache read:** about **0.1x** of normal input price
- **Cache write:** about **1.25x** (paid once per TTL window)
- **TTL:** about **5 minutes** (ephemeral, longer TTLs on enterprise tiers)
- **Up to 4 breakpoints** per request

**How:** Add `cache_control: {"type": "ephemeral"}` on the **last block of the stable prefix**. Everything up to and including that block is cached. Everything after is fresh each call.

**Layer order:** tools → system → messages → last user content block.

**Check it worked** in `response.usage`:
- `cache_creation_input_tokens` = written (1.25x)
- `cache_read_input_tokens` = read from cache (0.1x)
- `input_tokens` = normal price
- `output_tokens` = always normal price

**Use when:** system prompt, tools, RAG chunks and few-shot are stable across many calls.
**Don't use when:** content varies per user, or traffic is very low (under about 100 calls/day per prefix).
**Mistake:** `cache_control` on everything. Cache only truly stable prefixes (writes cost extra).

---

## 3. The Cost Math (50K calls/day, 200K prefix, Sonnet 5 at ~$2/M input)

| Scenario | Daily prefix cost |
|----------|-------------------|
| No caching | about $20,000 |
| Perfect hit rate | about $2,000 |
| Realistic (95% hits, 5% cold writes) | about $3,150 |

- About **10x** reduction. Savings about $16,850/day, about $505K/month.
- The user's ticket (about 500 tokens) stays full price.
- **Break-even:** If a prefix serves only 1-2 calls before changing, caching **loses** money (1.25x write tax). At 3 calls: 1.25 + 3×0.1 = about 1.55x vs 3x uncached, so you still save.

---

## 4. Cross-Provider Routing (after the July 30, 2026 OpenAI price cut)

| Model | Input $/M | Output $/M | Note |
|-------|-----------|------------|------|
| Claude Sonnet 5 | about $2.00 | about $10.00 | Best reasoning; pair with caching |
| Claude Haiku | about $0.80 | about $4.00 | Default triage |
| gpt-5.6-terra | about $2.00 | about $12.00 (was $17) | Pricier on output |
| gpt-5.6-luna | about $0.20 | about $1.20 (was $2.40) | Cheapest output |

- For short-output work (about 80 output tokens/ticket), **output cost dominates**. Luna about $4.80/day vs Haiku about $16/day.
- **OpenAI caching is automatic** (about 0.1x cached input, no code). **Anthropic caching is explicit** (you place breakpoints and instrument).
- On RAG, auto-cached Luna is the raw-dollar floor, but the lesson keeps Anthropic for tool parity (L3.4), reasoning, and **debuggable hit rates**. The pick is parity + control, not price.
- **Re-run the routing math after every pricing change.** It's not stable.

---

## 5. Batch API
- Submit a **JSONL of requests**, get results within 24h (usually 1-2h), billed at about **50%**.
- **Good for:** eval runs, snapshot regeneration, overnight enrichment, re-scoring when a new model drops.
- **Bad for:** user-facing chat, anything needed in under 24h.
- **Mistake:** Using batch for "by morning" jobs. The SLA is 24h, so results could arrive at 4pm.
- Batch outputs land in one file with one timestamp, which is good for audit trails (tag each batch with its purpose).
- **Caching + batch:** The lesson says they don't compose (either-or). Anthropic's docs describe caching inside batches as best-effort, so verify on your own workload.

---

## 6. Token Economy: Summarize vs Truncate vs RAG

| Pattern | What | Cost | Right for |
|---------|------|------|-----------|
| **Summarize** | Rolling ~500-token summary of old turns + last 5 verbatim | 1 summary call per ~10 turns | Long chat / support threads |
| **Truncate** | Keep last N turns | Zero | Short or stateless flows |
| **RAG** | Index history, retrieve top-K per turn | Embedding + search | Knowledge-heavy, multi-session |
| **Stuff everything** | All turns + docs + examples | Scales linearly | **Nothing. Refactor.** |

**Trade-offs:** summarize loses fidelity, truncate loses memory, RAG adds infra.
**Router rule:** under 10 turns → truncate; has KB + enterprise → RAG; else → summarize.
**Why not stuff everything:** Cost grows linearly, and lost-in-the-middle hits past about 100K tokens.

---

## 7. Cost Dashboards (FinOps)
Instrument on **day 1** (about 1 hour of OpenTelemetry setup saves quarterly CFO escalations). Metrics:
- `gen_ai.cost.usd` (by model + customer tier, from L2.5)
- `gen_ai.cache.hit_rate` = cache_read / (cache_read + cache_creation + input). **Alert below about 80%.**
- **$/customer/day** (top 10 spenders)
- `gen_ai.batch.utilization` (target: above 80% of non-realtime work in batch)

**Interview signal:** "How would you tell a customer their bill?" Answer: caching + batch + hit-rate dashboard + per-customer $ + a re-derived routing memo after price changes. Not "look at the invoice."

---

## 8. Five Production Gotchas
1. **Prompt edits invalidate the cache** (even one word). Stage edits across warming windows, not at peak (L3.6 versioning).
2. **Multi-tenant cache pollution:** Don't rely on the cache being tenant-private. Make sure the model never sees cross-tenant data, and tag content with a tenant ID.
3. **TTL eviction under load:** The 5 min TTL can behave like 1-2 min on busy days. Don't assume 100% hits.
4. **Batch and caching don't compose** (per the lesson; see note in section 5).
5. **Caching low-reuse prefixes loses money** (1.25x write tax). Measure hit rate; don't cache eagerly.

---

## 9. Real-World Cases
- **Procurement/CFO conversations:** "Cost per customer per month by model and tier" is the chart they ask for. Dashboards turn "we trust Anthropic" into "we save $X/month, here's the trend."
- **Regional/sovereign batch:** Self-hosted regional models (open models, Mistral, Qwen) can beat Haiku batch by about 3-5x on $/token for in-language overnight work. Same schema, different endpoint.
- **Audit-friendly batches:** One batch = one audit-trail entry (GDPR / CCPA / EU AI Act retention), not 10,000 separate calls.

---

## 10. Analogy: A Stamp on a Recurring Vendor Order
- Stamp the template once, and later orders skip the long approval and only check this month's line items.
- **Where it breaks down:** The stamp (cache) expires in about 5 minutes, re-stamping costs 1.25x, and any template change (prompt edit) breaks the stamp.

---

## 11. Quiz Answers (Self-Check)
| Q | Answer | Why |
|---|--------|-----|
| Q1 | **b** | Cache reads cost about 0.1x (10% of full price) |
| Q2 | **c** | Breakpoint at the end of the stable prefix (system + tools + RAG + examples) |
| Q3 | **b** | About 50% off, 24-hour SLA |
| Q4 | **b** | Prefix stable across many calls within the TTL |
| Q5 | **b** | Everything before the breakpoint is still cacheable, everything after is fresh each call |

---

## 12. Quick Memory Hooks
- **Cache read 0.1x, write 1.25x, TTL 5 min, up to 4 breakpoints**
- **One `cache_control` on the END of the stable prefix**
- **Cache only stable + high-volume prefixes**
- **Batch = 50% off, 24h SLA, never for realtime**
- **Summarize / Truncate / RAG, never "stuff everything"**
- **Hit rate below 80% → alert**
- **Re-run routing math after every price change**
- **Instrument cost on day 1**
