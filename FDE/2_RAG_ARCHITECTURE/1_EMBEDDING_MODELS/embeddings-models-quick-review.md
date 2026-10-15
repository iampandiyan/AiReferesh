# Module 4 · Lesson 4.1 — Embedding Models (Quick Review)

> **One-line idea:** An embedding model turns text into a list of numbers so that similar meanings sit close together. Picking the right one is the first big decision in RAG.

---

## 1. The AcmeCorp Story (Why This Matters)

- **Setup:** 5,000 help-center articles, ~500 words each → ~2.5M tokens.
- **Start:** `text-embedding-3-small` → indexing cost ≈ **$0.05** one-time; English retrieval@10 ≈ **84%**.
- **Problem:** Expansion to Spain, Mexico, Singapore → multilingual retrieval drops to ≈ **71%**. This is **FM8 (language mismatch)**.
- **Fix:** Swap to **Cohere embed-v4** → ≈ **89%** (**+18pp**).
- **Takeaway:** Cost is tiny, quality is everything. One model choice made a big difference.

### A/B results on the multilingual subset

| Model | Dim | Score | Note |
|---|---|---|---|
| text-embedding-3-large | 3072 | ~77% | Slightly better, 4x storage |
| cohere embed-v4 | 1024 | ~89% | 100+ languages, hosted SaaS (AcmeCorp's pick) |
| voyage-3-large | 1024 | ~91% | Top of MTEB multilingual |
| bge-base-en-v1.5 | 768 | ~86% English only | Weak on non-English |
| bge-m3 (self-host) | 1024 | ~87% | Open-source, multilingual |

---

## 2. What You Should Be Able To Do

- Compare OpenAI, Cohere, Voyage, BGE on dimension, cost, latency, quality.
- Recommend a model based on index size, query volume, refresh cadence, re-embed cost.
- Decide when to stay off-the-shelf vs fine-tune.
- Build a retrieval@K eval on **your own** golden set.
- Plan a 1M+ doc re-embedding migration with zero downtime.

---

## 3. The 5 Provider Families

| Family | Models | Dim | Price / 1M tokens | Strength |
|---|---|---|---|---|
| **OpenAI** | 3-small / 3-large | 1536 / 3072 | ~$0.02 / ~$0.13 | English-first, cheap default |
| **Cohere** | embed-v4 | 1024 (MRL 256/512/1024/1536) | ~$0.12 | 100+ languages, US/EU regions |
| **Voyage** | voyage-3-large | 1024 (MRL 256/512/1024/2048) | ~$0.18 | Top multilingual benchmarks |
| **BGE (BAAI)** | bge-base-en-v1.5, bge-m3 | 768–1024 | ~$0 per call (GPU rental) | Open-source, self-host |
| **Regional** | Qwen-embed (Mandarin), Mistral / multilingual-e5 (European), AraBERT (Arabic) | 768–1024 | ~$0 (self-host) | Language specialists |

### Decision guide

| Situation | Pick |
|---|---|
| English-heavy, fast, cheap | text-embedding-3-small |
| Multilingual customers | Cohere embed-v4 or voyage-3-large |
| On-prem / sovereign cloud (no data egress) | bge-m3 self-hosted |
| One dominant non-English language | Regional model (Qwen / Mistral / AraBERT) |
| 100M+ docs, cost-sensitive | bge-base-en-v1.5 self-hosted |

**Rule of thumb:** First check *deployment shape* (on-prem vs hosted) and *dominant language*. Cost/quality is the tiebreaker.

---

## 4. The 3 Axes: Dimension, Quality, Latency

### Dimension
- Controls storage cost and index speed. 768-dim float32 = ~3 KB per vector.
- "Biggest dimension wins" is the wrong instinct.

### Matryoshka (MRL) — the dimension knob
- Important info is packed in the **leading dimensions**, so you can **truncate + re-normalize** without re-embedding.
- Supported by: text-embedding-3, Cohere embed-v4, Voyage, Nomic.
- Example: 3072 → 1024 cuts storage ~3x with only a small recall loss (single-digit points).
- **Workflow:** embed at full width → sweep truncation lengths on your eval → keep the smallest dim that meets your quality bar.

### Vector quantization — the bigger storage lever
| Type | Size reduction | Notes |
|---|---|---|
| float32 (default) | 1x (4 bytes/dim) | Baseline |
| int8 scalar | ~4x smaller | Tiny recall loss, usually turned on first |
| binary (1 bit) | ~32x smaller | Bigger recall loss; rescore top-K with full vectors |

Example: 1M × 1024-dim = ~4 GB → ~1 GB (int8) → ~128 MB (binary). **Quantize before you shrink the model.**

### Quality
- Public benchmarks (MTEB, BEIR) are only a starting point.
- **Always measure retrieval@K on YOUR golden set.**

### Latency
- Hosted SaaS adds ~30–80 ms per query; self-hosted in same VPC ~5–15 ms.
- Target sub-100 ms p95 for chat. Cache frequent query embeddings.

### Build your own eval (the only benchmark that matters)
1. Embed corpus with the candidate model.
2. For each golden question, embed it and fetch top-K by cosine similarity.
3. A hit = expected doc is in top-K. Score = hits / total questions.
4. Repeat for every candidate model.

---

## 5. The Asymmetric-Embedding Trap

- Modern embedders treat **queries** and **documents** differently.
- **Cohere / Voyage:** use `input_type="query"` vs `input_type="document"`.
- **E5 models:** use text prefixes `"query: ..."` and `"passage: ..."`.
- Getting this wrong causes a **silent recall drop** — no error, looks like a bad model, but it's a wiring bug.
- First thing to check when a freshly re-embedded index performs worse.

---

## 6. Multilingual Specifics

Typical traffic mix for a global enterprise:

| Segment | Share | Best option |
|---|---|---|
| Pure English | ~50–65% | text-embedding-3-small |
| European (ES/FR/DE/PT) | ~20% | Cohere embed-v4 / Voyage |
| Mandarin / Cantonese | ~10% | Qwen-embed (bge-m3 fallback) |
| Code-mixed / regional (Spanglish, Singlish) | ~5–15% | Multilingual embedders (~10pp below pure-language) |

### Router pattern
1. **Detect language** with fastText (~5 ms).
2. **Route** to a per-language index/embedding model.
3. Keep 2–3 indexes in parallel with a multilingual fallback.

- **Cost:** ~2–3x storage.
- **Gain:** ~15–20pp on the non-English segment.

---

## 7. Re-embedding 1M+ Docs Without Downtime (Dual-Write Pattern)

| Phase | What happens |
|---|---|
| 1. Dual-write | New docs go into BOTH old (v1) and new (v2) index |
| 2. Backfill | Re-embed old corpus into v2 in batches (1M docs on 1x A100 ≈ 4–6 hrs, run overnight) |
| 3. Shadow-read | Serve from v1, also query v2, compare overlap, alert on divergence |
| 4. Cutover | Swap reads to v2; keep dual-write ~1 week as safety net |
| 5. Retire v1 | Stop writes, drop old index |

- **Total:** ~2 weeks, **zero downtime**.
- Dimension lock-in means 768-dim and 1536-dim vectors can't share one index.

### Monitor for drift after cutover
- Replay **canary golden-set queries** nightly; track recall@10 and MRR over time.
- Alert if recall falls **~3–5 points** below launch baseline.
- Watch for shifts in language mix or new document categories (FM8 creeping back).

---

## 8. Fine-Tuning vs Off-the-Shelf

- Fine-tuning gives roughly **+5–10pp** on hard retrieval, costing about **$600–$2,400**.

### Two tiers
| Tier | What it is | When |
|---|---|---|
| **Tier 1: Linear adapter on frozen embeddings** | Train a small matrix on top; no re-embed of base model | Almost all mid-market cases; try first |
| **Tier 2: Full contrastive encoder fine-tune** | Update model weights; mandatory full re-embed; expensive | Only if domain is truly out-of-distribution and Tier 1 is maxed |

### 3-gate rule — fine-tune only if ALL pass
1. Off-the-shelf recall is **≤ 85%** on your golden set.
2. **≥ 20%** of golden queries contain out-of-distribution jargon (product names, internal codes, niche regulations).
3. Fine-tune cost is **< 5%** of engagement value.

**Senior answer to "should we fine-tune?":** "Not yet" — a model swap (+18pp) beat a fine-tune (+3pp) in the AcmeCorp case.

### Anti-example
Engineer picks text-embedding-3-large (the "biggest") → only +6pp (71% → 77%) at 4x storage. Wrong lever: dimension instead of **language coverage**. Measure first, then pick the under-served axis.

---

## 9. Five Production Gotchas

1. **Dimension lock-in** — Wrong dimension early forces a re-embed later.
2. **Re-embed on model update costs real money** — Don't promise "embeddings stay current automatically."
3. **Benchmark ≠ your data** — MTEB rankings can flip on your domain; always re-measure.
4. **Self-hosting is GPU rental, not per-call** — bge-m3 on A100 ≈ $2–3/hr (us-east-1), $4–5/hr (eu-west-1), regardless of volume.
5. **Query-time latency** — SaaS adds 30–80 ms/query (~25 min/day at 50K queries). Cache and co-locate.

---

## 10. Why the Choice Is the Load-Bearing First Move

- **Cost is small, quality is everything.** 2.5M tokens costs ~$0.05 (small) or ~$0.30 (large). Pick on quality.
- **Multilingual expansion is the most common trigger** for engagement extension. Have the router ready.
- **Sovereign / regional customers are real.** Regulated EU banks, financial services, China subsidiaries rule out SaaS embedders → bge-base-en / bge-m3 + regional specialists.

---

## 11. Analogy

Choosing an embedding model = hiring a translator for a 50-person meeting.
- **Cheap translator** (3-small): fast, English-comfortable, weak on code-switching.
- **Specialist** (voyage-3-large): pricier, handles nuance.
- **Local hire** (Qwen / Mistral): cheap and perfect in one language, lost when speakers switch.

**Limit of the analogy:** an embedding can't ask clarifying questions, and it's locked in until you re-embed the corpus.

---

## 12. Interview Signal

FDE interviews (Anthropic, Glean, Decagon, Sierra, Mistral) ask: *"Your customer's RAG hits ~75% on language X — what do you try?"*

**Strong answer:** compare 5 providers on the customer's golden set → router pattern → fine-tune break-even framework → plan the migration.
**Weak answer:** "Use the biggest model."

---

## 13. Quick-Fire Quiz Answers

| Q | Answer |
|---|---|
| Q1: 3-small on non-English accuracy | **b) ~70–75%** (English-trained gap) |
| Q2: Strict on-prem residency | **c) bge-base-en / bge-m3 self-hosted** |
| Q3: Re-embed 1M docs strategy | **b) Dual-write, backfill, shadow-read, swap, retire** |
| Q4: Dimension lock-in | **c) Can't mix 768 and 1536 dims on the same index** |
| Q5: When fine-tuning pays back | **b) After maxing off-the-shelf; jargon-heavy; cost < ~5% of engagement** |

---

## 14. Practice Exercises (Topics Only)

- **Easy:** Monthly cost model for an 8M-chunk corpus (380 tokens each, re-embedded monthly).
- **Easy:** Pick one provider for a 60% code-mixed + 40% English corpus.
- **Medium:** pgvector dual-column migration + read-flag toggle (`openai_embedding vector(1536)` + `voyage_embedding vector(1024)`).
- **Medium:** Recall@10 dropped 89 → 71 after re-embed — list 4 root causes with diagnostics.
- **Hard:** Per-query language router with code-mixed fallback.
- **Hard:** Decision tree — full encoder fine-tune vs provider swap.
- **Medium:** Matryoshka truncation + int8/binary quantization — recall@k vs storage.

---

## 15. Cheat Sheet (Memorize These)

- Multilingual swap **3-small → Cohere embed-v4: 71% → 89% (+18pp)**.
- **Measure on YOUR golden set**, not public benchmarks.
- **MRL truncation** = free dimension cut, no re-embed.
- **Quantization** (int8 ~4x, binary ~32x) beats shrinking the model.
- **Query vs document input types** — wrong setting = silent recall drop.
- **Router** = fastText (~5 ms) + per-language index → +15–20pp.
- **Migration** = dual-write → backfill → shadow-read → cutover → retire (~2 weeks, no downtime).
- **Fine-tune** only if: recall ≤ 85%, jargon ≥ 20%, cost < 5% of engagement. Try the linear adapter first.
- **On-prem** → bge-m3. **Self-host cost** = GPU rental, not per call.
