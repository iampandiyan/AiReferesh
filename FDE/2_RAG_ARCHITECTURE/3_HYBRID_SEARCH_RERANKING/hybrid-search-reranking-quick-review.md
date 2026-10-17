# Module 4 · Lesson 4.3 — Hybrid Search and Reranking (Quick Review)

> **One-line idea:** Dense search misses exact matches. BM25 misses paraphrases. So run both, fuse the results, then rerank the top candidates with a cross-encoder.

---

## 1. The AcmeCorp Story (Why This Matters)

- **Corpus:** 5,000 help-center articles + 30 policy PDFs (chunked per L4.2, embedded per L4.1).
- **Dense-only problem:** Query "show me Refund Policy clause 3.2" returns paraphrases of clause 3.x, not the exact clause. Support needs the verbatim text.
- **BM25-only problem:** Query "how do I cancel my Pro subscription?" fails because the policy says "**terminate**", not "cancel".
- **Fix:** BM25 + dense in parallel → RRF fusion (k=60) → rerank top-50 → send top-10 to the LLM.
- **Result:** Hit-rate **~73% → ~91%** (+18pp) on the 100-question golden set.

---

## 2. What You Should Be Able To Do

- Wire BM25 + dense retrieval in parallel and fuse with RRF.
- Add a Cohere / Voyage / BGE reranker on top.
- Compare query rewriting, HyDE, multi-query, and ensembling, and know which actually moves recall.
- Justify the ~80–150 ms reranker latency to a customer.
- Pick a reranker per content type and diagnose hybrid latency.

---

## 3. Key Numbers

| Number | Meaning |
|---|---|
| **+18pp** | Hit-rate lift, dense-only → hybrid + rerank |
| **k=60** | Standard RRF constant (tune ±20, don't go to zero) |
| **+50–200 ms** | Reranker p95 latency |
| **~$0.002** | Cost per rerank call (rerank-4-fast ~$2/1M tokens) |
| **~194 ms** | Full pipeline p95 (BM25/dense + RRF + rerank) |
| **~$0.003** | Total cost per query (~$2,600/month at ~0.33 RPS) |

---

## 4. Step 1: Two Retrieval Lanes (BM25 + Dense)

### BM25 (sparse)
- Scores by term frequency / inverse document frequency (Robertson & Zaragoza 2009).
- **Catches:** exact phrases, clause numbers, named entities, model IDs, error codes.
- **Misses:** synonyms and paraphrases.
- Behind Elasticsearch, Postgres `tsvector`, and the sparse half of Pinecone hybrid.

### Dense
- Embeds query and docs into one vector space (DPR, Karpukhin 2020).
- **Catches:** paraphrases, near-synonyms, cross-language.
- **Misses:** exact section numbers (a number is a tiny signal in a sea of semantic content).

### Which to use when
| Corpus type | Pick |
|---|---|
| Paraphrase-heavy, no rigid identifiers (consumer FAQ) | Dense-only |
| Identifier-heavy, queries echo literal tokens (code, logs, clause numbers) | BM25-only |
| Mixed workload (AcmeCorp) | **Hybrid** |

### Worked example
| Query | BM25 | Dense |
|---|---|---|
| "show me Refund Policy clause 3.2" | Gold doc at rank 1 | Gold doc at rank 3 |
| "how do I cancel my Pro subscription?" | Garbage ("cancel" is literal) | Gold doc at rank 1 ("terminate" ≈ "cancel") |

→ Each lane wins one query type and loses the other. Ship only one and you systematically lose a query class.

### Anti-example: pure dense on rare terms
- Query: "how does the X-Ratchet rotation work in our SDK?" X-Ratchet is a proprietary name with no neighbours in the embedding space.
- Dense returns unrelated "session rotation / key rotation" articles. BM25 matches the literal token and finds the right SDK page.
- "Looks right, ranks wrong."

### Run in parallel
- Use `asyncio.gather`. Total latency = **max(BM25, dense)**, not the sum.
- BM25 ~5–15 ms; dense ~30–80 ms. The BM25 lane is essentially free.

---

## 5. Step 2: Reciprocal Rank Fusion (RRF)

**Formula:** each doc scores `1 / (k + rank)` per source; sum across sources; sort descending. `k = 60`.

```python
def rrf(rankings, k=60):
    scores = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0) + 1/(k + rank)
    return sorted(scores, key=scores.get, reverse=True)
```

- Example: doc at BM25 rank 4 and dense rank 1 → 1/63 + 1/60 = 0.0325 (highest total, wins).

### Why rank-based fusion?
- BM25 scores are unbounded (0–30); cosine scores are 0–1. Incomparable scales.
- RRF uses **rank only**, so no per-corpus normalization and no re-tuning when you swap embedders.
- Default in Pinecone, Elasticsearch hybrid, and LangChain `EnsembleRetriever`.
- **Trade-off:** discards raw confidence. If you need a calibrated score, re-score with a cross-encoder.

### Why k=60?
- Small k (e.g. 10): top ranks dominate too aggressively.
- Large k (e.g. 200): flattens toward a plain rank-sum.
- 60 is the empirical sweet spot (Cormack 2009). Don't go below ~30 without an eval.

### Weighted RRF
- `score(d) = Σ w_i / (k + rank_i)`
- Noisy BM25 corpus → bias dense (e.g. 0.7 dense / 0.3 sparse). Identifier-heavy corpus → flip it.
- **Best:** per-query-type routing. AcmeCorp sends clause-number queries to `w_sparse = 0.7` and free-text questions to `w_dense = 0.7`.

### When hybrid hurts
- On 50 exact-match clause queries: BM25-only hit **45/50**, hybrid hit only **42/50**. Dense candidates pushed exact matches down.
- Hybrid still wins overall (~84% vs ~51%) because it rescues the paraphrase slice.
- **Fix:** route lexical-looking queries to sparse-weighted RRF or BM25-only. **Measure per slice, not just in aggregate.**

---

## 6. Step 3: Cross-Encoder Reranking

- A **cross-encoder** takes the (query, doc) pair **jointly** (full attention across both) and outputs one relevance score. More accurate than a bi-encoder, which embeds query and doc independently.
- **Trade-off:** O(N) model calls, so run it on **top-50**, not the whole corpus.
- Flow: RRF top-50 → rerank → **top-10** to the LLM.

### Before vs after example
- Cross-encoder pulled `cancellation_walkthrough` from rank 9 to rank 3 and demoted `policy_v1_SUPERSEDED` out of the top-10.
- Net **+7pp precision@10**. Typical uplift ~+10–15pp on top-10 (depends on golden set).
- It catches subtle signals: "this is the LATEST policy, not the superseded one."

### Reranker options

| Reranker | p95 latency (50 docs) | Cost | Best for |
|---|---|---|---|
| **Cohere Rerank 4 (`rerank-v4.0-pro`)** | ~150 ms | Pricier than fast | Multilingual + English, 32K-token context; AcmeCorp default |
| **Cohere `rerank-4-fast`** | ~70 ms | ~$0.002/query | Sub-100 ms SLO path |
| **Voyage Rerank-2.5** | ~180 ms | ~$0.0025 | English-heavy, technical content |
| **Voyage Rerank-2.5-lite** | ~80 ms | ~$0.0012 | Latency-sensitive, consumer apps |
| **BGE-Reranker-v2-m3 (self-host)** | ~80 ms on A10 | Amortised GPU | On-prem / sovereign residency |
| **Jina Reranker v2 (self-host)** | ~90 ms on A10 | Amortised GPU | Open-weights multilingual, 100+ languages |

### When NOT to rerank
- Latency-critical chat with sub-100 ms p95 (use fast/lite, or skip on cache hits).
- Candidate pools of 500+ docs (Cohere caps at 1000, gets pricey).
- >100 RPS cost-sensitive workloads → self-host BGE.

### Frontier: ColBERT (late interaction)
- Stores **one vector per token**; scores with **MaxSim** (for each query token, take max cosine vs doc tokens, then sum).
- Acts as retriever **and** reranker in one pass; keeps token-level lexical precision.
- **Cost:** storage balloons 50–200x (PLAID / 2-bit quantization claws it back).
- **Pick when:** you self-host, need multilingual token-level matching at scale, and SaaS rerank calls are the bottleneck.
- **Skip when:** small/mid corpus where one Cohere call on top-50 (~150 ms) is enough.

### Measure rerank properly
- Recall@k / hit-rate only say *whether* the gold doc is in the top-k, not *where*.
- Use **MRR** (rewards first relevant doc near rank 1) and **nDCG@k** (rewards all relevant docs high, discounted by position).
- Protocol: freeze 100+ golden pairs → run with rerank off, log recall@10 + MRR + nDCG@10 → turn rerank on → diff per query.
- Rerank can be flat or negative on already-clean exact-match slices. **Measure per slice** (exact vs paraphrase).

---

## 7. Step 4: Query Rewriting and HyDE

### HyDE (Hypothetical Document Embeddings, Gao 2022)
- Ask an LLM to **draft a hypothetical answer first**, embed the **draft** (not the question), then retrieve.
- Why it works: a short abstract question vs. a long detailed draft. The draft sits closer to real docs in embedding space.
- Example: "how do I get my money back?" → draft mentions Refund Policy clause 3.2 → gold doc moves from rank 14 to rank 1.
- **Gain:** ~+5pp on hard paraphrase queries. **Cost:** one extra Haiku call (~$0.0002, ~150 ms).
- **Use for:** hard-paraphrase queries on technical/policy corpora.
- **Skip for:** simple factual queries, or when retrieval already hits 90%+.
- **Risk:** the LLM draft can hallucinate a tier or section that doesn't exist and pull retrieval toward fiction.
- **Mitigation:** run HyDE+dense in parallel with BM25; RRF arbitrates.

### Multi-query retrieval
- Generate 3–5 rephrasings, retrieve for each, merge with RRF, rerank the union.
- **Use when:** one phrasing misses edge cases (e.g. admins saying "deactivate the workspace" instead of "cancel"; multilingual reformulations).
- **Skip on:** hot-path consumer chat (latency).
- **Cost compounds:** 5x retrieval + bigger rerank batch (~$0.01 per query, about 5x a normal hybrid+rerank query).
- **Rule:** pick HyDE **OR** multi-query **OR** aggressive rerank per query. Stacking all three on a hot path is cost theatre. Reserve multi-query for batch/offline.

### Frontier: Anthropic Contextual Retrieval
- Fixes the **chunk side** (HyDE/multi-query fix the query side).
- Before indexing, a cheap LLM (Haiku) prepends a 1–2 sentence situating blurb to each chunk ("This chunk is from AcmeCorp's Refund Policy v2, section 3.2…"). Index into **both** BM25 and dense.
- Reported: **~49%** fewer retrieval failures; with rerank on top, **~67%**.
- One-time indexing cost (prompt-cache the document). Natural next layer once hybrid + rerank plateaus.

---

## 8. Step 5: The Production Pipeline

```
query
  ├─ BM25 top-20  ─┐ (parallel)
  └─ Dense top-20 ─┘
        ↓
   RRF fuse (k=60) → top-50
        ↓
   Cohere Rerank 4 → top-10
        ↓
   LLM generation
```

### Latency budget (p95)
| Stage | Time |
|---|---|
| BM25 | 12 ms |
| Dense (pgvector HNSW) | 38 ms |
| Parallel total | 38 ms (max, not sum) |
| RRF | 1 ms |
| Rerank (Cohere pro, 50 docs) | 155 ms |
| **Total** | **~194 ms** |

- Fits comfortably inside a ~2 s support-agent SLO; LLM generation is the dominant downstream cost.
- **Change the shape when:** 100+ RPS (self-host BGE), sovereign residency (BGE on-prem), sub-100 ms SLO (rerank-4-fast / Voyage lite / skip on simple queries).
- This is the retrieval shape feeding M5 sub-agent tools and the M11 capstone.

---

## 9. Analogy

Hybrid search = a **librarian + a search index**.
- **Librarian (dense):** knows what books are about by feel.
- **Search index (BM25):** finds exact phrases.
- **Reranking:** the librarian picks the best 3 from the 17 matches.

**Limit of the analogy:** a real librarian knows your role and history. A dense embedding only sees the current query (cold start). Personalisation (role filters, recent history) must be engineered explicitly.

---

## 10. Production Gotchas

1. **Reranker latency (+50–200 ms):** budget for it; use fast/lite or skip on simple queries for sub-second SLOs.
2. **BM25 index lives separately from the vector store:** deletes must hit both. A stale BM25 index is a silent **FM5** failure.
3. **Multi-query × reranker compounds cost:** pick one; reserve for batch.
4. **Never fuse raw cosine + raw BM25 scores:** incomparable scales. Use RRF, or normalise both to [0,1] first.
5. **Reranker context limit:** Cohere Rerank 4 takes up to 32K tokens per doc, but ultra-long chunks cost more and dilute relevance. Prefer focused chunks or summaries.

---

## 11. AcmeCorp Engagement: Hybrid Is the Default

- Policy PDFs have rigid clause numbering (clause 3.2, section 7.1(c), Annex B). Dense-only misses ~30% of these. **BM25 is non-negotiable.**
- Customer queries are paraphrase-heavy ("cancel" vs "terminate", "money back" vs "refund eligibility"). Dense + BM25 + RRF + rerank is the default.
- **Multilingual rollouts (Mexico / Madrid / Singapore):** hybrid handles translation noise better than dense alone, because BM25 catches surviving exact terms (product names, plan tiers, error codes).
- **Cross-region latency:** Cohere endpoints add ~30 ms vs in-region. Use rerank-4-fast, or self-host BGE-reranker-v2-m3 on the customer's GPU (regulated EU bank, health-tech, global-markets finance).
- Which vector store (pgvector, Qdrant, Pinecone) serves both indexes → Lesson 4.4.

---

## 12. Quick-Fire Quiz Answers

| Q | Answer |
|---|---|
| Q1: Why dense-only misses "clause 3.2" | **b)** Dense embeds for semantic similarity; the number is a weak signal. BM25 catches the exact match |
| Q2: How RRF merges lists | **b)** Sum `1/(k+rank)` across sources (k=60), sort descending |
| Q3: Cross-encoder uplift on top-10 | **a)** ~+10–15pp (depends on golden set) |
| Q4: HyDE trick | **b)** LLM drafts a hypothetical answer first; embed the draft, which is closer to real docs than the question |
| Q5: Multi-query + rerank cost | **c)** Compounds (5x retrieval + reranker); pick one or the other |

---

## 13. Practice Exercises (Topics Only)

- **Easy:** Reproduce dense-only failing on an exact-section query ("AML bulletin 4.5.2").
- **Easy:** BM25 with `rank_bm25` on the same corpus and query.
- **Medium:** Implement RRF from scratch and verify it beats either list alone.
- **Medium:** Weighted RRF: sweep the dense-vs-sparse alpha.
- **Medium:** Add Cohere Rerank 4 to the fused top-50.
- **Hard:** Rerank eval: recall@k, nDCG, MRR, and the slice where rerank hurts.
- **Hard:** HyDE: draft, embed, retrieve; honest comparison vs direct query.
- **Graded:** Production hybrid + rerank pipeline for Northwind Finance's OCC compliance RAG (800 bulletins; 4-strategy comparison memo + more).

---

## 14. Cheat Sheet (Memorize These)

- **Dense misses exact. BM25 misses paraphrase. Run both in parallel.**
- **RRF:** `1/(k+rank)`, **k=60**, rank-based, no score normalization needed.
- **Rerank top-50 → top-10** with a cross-encoder (~+7–15pp precision, +50–200 ms).
- **Latency:** parallel = max(lanes); full pipeline ~194 ms p95, ~$0.003/query.
- **Reranker picks:** Cohere pro (default), `rerank-4-fast` (speed), BGE (on-prem / high scale).
- **Weighted RRF + routing:** clause-number queries → sparse, free-text → dense.
- **Hybrid can hurt** exact-match slices (BM25 45/50 vs hybrid 42/50). Measure per slice.
- **Metrics:** recall@k + MRR + nDCG@k, not hit-rate alone.
- **HyDE** for hard paraphrase (+~5pp). **Multi-query** for batch only. **Pick one** of HyDE / multi-query / aggressive rerank.
- **Contextual Retrieval** (~49% fewer failures, ~67% with rerank) is the next layer.
- **Don't fuse raw scores.** Keep BM25 and vector deletes in sync.
