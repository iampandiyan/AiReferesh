# Module 4 · Lesson 4.5 — The Top 8 RAG Failure Modes (Quick Review)

> **One-line idea:** When a RAG system gets worse in production, it's almost never "the model regressed." It's one of 8 characteristic failure modes. Diagnose first, fix second, never roll back blindly.

---

## 1. The AcmeCorp Story (Why This Matters)

- **Dev accuracy:** ~88% (50-question golden set). **Prod two weeks later:** ~62%.
- **Team's reaction:** "The model regressed", so they prepared a rollback to the previous Claude revision.
- **FDE's move:** Don't roll back. Run the **8-FM diagnostic** on 50 failing prod queries (~2 hours).
- **Findings:**
  - **FM1** (lost-in-the-middle): 14 queries, long retrieved contexts.
  - **FM3** (conflicting evidence): 9 queries, old Refund Policy + v2 amendment both retrieved.
  - **FM8** (language mismatch): 12 Spanish / code-mixed queries on an English-only embedder.
- **Fixes (2 days):** end-anchor prompt, dedupe by canonical doc ID, swap to Cohere embed-v4.0.
- **Result:** back to ~**91%**. Rollback cancelled. The diagnostic spreadsheet became the SOC2 vendor-review artifact.
- **Root cause of the gap:** prod traffic exposed failure modes the dev golden set never covered.

---

## 2. What You Should Be Able To Do

- Name the 8 failure modes and describe each in one sentence.
- Categorize a failing query against the 8 FMs in **under 60 seconds**.
- Run the diagnostic on 50 failing prod queries and produce a fix-priority list.
- Apply the specific fix for each FM and know which lesson covers it.
- Defend a fix-or-accept decision per FM in a customer scorecard.

---

## 3. Key Numbers

| Number | Meaning |
|---|---|
| **8** | Failure modes in the checklist |
| **~80%** | "Model regressed" tickets that are actually RAG failures (anecdotal) |
| **60 sec** | Per-query categorization target (after ~50 reps) |
| **62% → 91%** | AcmeCorp outcome after 2 days of fixes |
| **~70%+** | Share of failures usually explained by the top 2–3 FMs |

---

## 4. The 8 Failure Modes

| FM | Name | Symptom | Fix |
|---|---|---|---|
| **FM1** | **Lost in the middle** | Long context (50K+); model recalls start and end, drops the middle | End-anchor prompt (L3.1) + reranker to shrink context to top-5 (L4.3) |
| **FM2** | **Irrelevant context** | Top-10 retrieved, only 2 relevant; noisy docs dilute | Lower K + cross-encoder reranker + relevance threshold |
| **FM3** | **Conflicting evidence** | Two retrieved docs disagree (old + new version) | Dedupe by canonical doc ID + prefer newest effective date |
| **FM4** | **Off-topic retrieval** | Ambiguous query pulls adjacent-topic docs | Query rewriting (HyDE) + cosine threshold |
| **FM5** | **Stale data** | Index retrieves the Nov 2024 version, not the May 2025 amendment | TTL on docs + effective-date filter + re-index on policy change |
| **FM6** | **Multi-hop gap** | Question needs 3+ docs; no single chunk has the answer | Query decomposition + retrieve per sub-question + aggregate |
| **FM7** | **Citation hallucination** | Model cites "Section 8(7)(b)" but it doesn't say that | Force citations + validate after generation; re-prompt if invalid |
| **FM8** | **Language mismatch** | Spanish / Mandarin / code-mixed query embeds poorly | Multilingual embedder + language detection + regional specialist |

### When the 8-FM taxonomy breaks down
- **Use it for:** first-pass triage of any production RAG quality regression (covers ~80% of failures).
- **Don't use it when:** the failures are generation-side (instruction-following drift, refusal misfires). Those need an M6 eval lifecycle.
- **Warning sign:** the "Other" bucket exceeds ~20% and you start force-fitting symptoms. Extend the taxonomy.
- **Anti-pattern:** rolling back the model first. It masks the symptom on the dev set; the FMs are still in prod.

### Three classes the 8 cards under-cover (fold into the same diagnostic)
1. **Chunk fragmentation / wrong granularity:** the gold answer spans a chunk boundary (different from FM6, which spans *documents*). Check whether the gold text lives fully in one chunk. Fix: 10–20% overlap, semantic/recursive chunking, late chunking, contextual chunking.
2. **Query-understanding / lexical-vs-semantic gap:** acronym, product code, or statute number vs. spelled-out docs (~0.4 cosine). If the acronym-expanded query finds the gold doc and the raw one doesn't, it's this. Fix: **hybrid dense + BM25**, acronym/synonym expansion, multi-intent decomposition.
3. **Metadata-filter / multi-tenant leakage:** a missing `tenant_id` / ACL / effective-date filter lets one tenant see another's docs. Looks like FM4/FM3 but it's a **security escalation** (GDPR breach + SOC2 finding). Fix: mandatory pre-filters at the vector-store layer, **fail-closed** if the filter is absent, and a test that tenant-A can never surface tenant-B doc IDs.

---

## 5. FM1 Deep Dive: Lost in the Middle

- **Finding (Liu et al. 2023):** U-shaped recall. Start and end recall well; the **middle drops ~30–50pp**. Newer models narrow the gap but don't close it.
- **Payoff of the L4.3 stack (Anthropic Contextual Retrieval, top-20 failure rate):**

| Technique | Failure reduction |
|---|---|
| Contextual embeddings alone | ~35% (5.7% → 3.7%) |
| + contextual BM25 (hybrid) | ~49% (→ 2.9%) |
| + reranker | ~**67%** (→ 1.9%) |

- **Mechanism:** a raw chunk ("revenue grew 3%…") lost *which company* and *which quarter*. Prepend ~50–100 tokens of chunk-specific context before embedding.

### 2026 update: 1M-context Opus 5 (GA 2026-07-24)
- **U-shape stays.** Per-percentile recall is still U-shaped; you just have more middle to lose.
- **Economics still favour retrieval:** top-5 rerank ≈ **$0.002/query** vs. stuffing 800K tokens ≈ **~$4/query**.
- **Lost-in-the-middle becomes "the tail":** hot path (<2 s support deflection) → short rerank-top-5 on Sonnet 5 / Haiku. Reserve 1M context for offline / batch / complex multi-hop. End-anchor stays correct on both paths.
- **Capability argument, not just cost:** **RULER** (2024) shows many models hold quality only for a fraction of their claimed window; **NoLiMa** (2025) shows most models fall below 50% of short-context score at 32K once literal matches are removed.

### The needle test (diagnostic)
1. Place a "needle" fact at ~5% / 25% / 50% / 75% / 95% of a long context.
2. Run the same query ~20 times per position.
3. Typical result: **90% / 70% / 45% / 65% / 88%** (U-shape).

### The fix is positional, not capability-based
- **Anchor at the end** (L3.1).
- **Shorten context** via reranker: top-50 → top-5 and the U-shape mostly disappears.
- **Repeat critical rules** at start and end: compliance jumps ~50% → ~95%+.

---

## 6. The Diagnostic Flow (A Doctor's Differential)

### Step 0: Name the STAGE before the FM (RAG triad, Ragas/TruLens)
| Layer | Question |
|---|---|
| **Context relevance / recall** | Did the right chunk reach the context? |
| **Groundedness / faithfulness** | Did the answer come from the context or the model's memory? |
| **Answer relevance** | Did the answer address the question? |

### Map FMs to pipeline stages
| Stage | FMs |
|---|---|
| Query understanding | FM4, FM8 |
| Retrieval / recall | FM2, FM8 |
| Ranking | FM2, FM4 |
| Generation | FM1, FM6, FM7 |
| Data / index layer | FM3, FM5 (exist in the corpus before the query arrives) |

### How to find 50 failing queries (no ground truth in prod)
1. **Reference-free LLM-judge metrics:** Ragas faithfulness and answer relevancy need no gold answer.
2. **Implicit signals:** thumbs-down, human escalation, "that's not what I asked", regenerate clicks, max-cosine below ~0.5.
3. **Online → offline loop:** prod traces → judge + signals rank candidates → human triages top slice → confirmed failures become the 50-query sample **and** get promoted into the golden set.

### The 4-step discipline
1. Pull 50 failing queries.
2. For each, read query + retrieved set + response; tag **FM1–FM8** (mark two if needed).
3. Tally. Pareto: 2–3 FMs usually explain ~70%+.
4. Fix the top 1–2 with L4.x patterns, re-eval, repeat.

### The diagnostic spreadsheet
Columns: `query_id, query_text, retrieved_top5_ids, model_response, expected_response, fm_primary, fm_secondary, fix_lesson, fix_status`.
Pivot by `fm_primary`. **This spreadsheet is the artifact handed to the customer's compliance team.**

Example distribution: FM1 28% · FM8 24% · FM3 18% · FM2 14% · FM7 10% · FM5 6% → top 3 = 70% → fix those first.

### Quantitative diagnosis: the 4 Ragas metrics
| Metric | Low means |
|---|---|
| **context_recall** | Retrieval / embedding bug (gold info never arrived) |
| **context_precision** | Low + high recall = ranking / dilution bug → needs reranker |
| **faithfulness** | Low + good context = generation bug (FM1 or FM7) |
| **answer_relevancy** | Answer doesn't address the question |

- **Measure recall at each hop:** recall@100 (post-retriever), recall@10 (post-reranker), end-to-end.
  - Present @100 but absent @10 → **reranker is demoting the right doc**.
  - Present @10 but answer wrong → **generation-side** (FM1 / FM7).
  - **FM2 lives in retrieval; FM1 lives in generation; recall@10 is the line between them.**
- **Suggested thresholds (compliance workload):** context_recall ≥ ~0.90, context_precision ≥ ~0.80, faithfulness ≥ ~0.90. Track nDCG@10 and MRR too.

### 50 queries vs. 500
- **50:** first-pass triage, ~2 hours, surfaces the top-2 FMs.
- **500+:** needed for tail FMs (FM6, FM7) hitting a small traffic slice; ~1 FDE-day.
- **Alternative:** stratify by query intent (tighter, but adds a labelling step).
- **Blind spot:** FMs that are time-bimodal (e.g. only during the daily index-refresh window) need M6 observability.
- **Anti-pattern:** categorizing in your head. The written spreadsheet is what survives procurement review.

---

## 7. FM6 and FM7: The Hardest to Detect

### FM6: Multi-hop reasoning gap
- Example: "Compare the Pro vs Business tier cancellation policy." No single chunk has both. The model picks one silently or hallucinates a synthesis.
- **Diagnostic:** check whether the full answer *could* be assembled from the retrieved chunks. If not → FM6.
- **Fix:** **query decomposition**: break into sub-questions, retrieve per sub-question (k=5), dedupe, then answer.

### FM7: Citation hallucination
- Example: model says "per Refund Policy clause 3.2, cancel within 90 days," but clause 3.2 is about pro-rata billing. Customer quotes it in a chargeback; legal finds out 6 weeks later.
- **Fix: force + validate:**
  1. Force `[doc_id]` citations.
  2. Check every cited ID is in the retrieved set; if not → regenerate with a strict prompt.
  3. Verify each citation actually **supports the claim** (LLM-judge).
- Result: hallucinated-citation rate ~11% → ~0.4% (own measurement).
- **Tradeoff:**
  - **Force-only:** non-regulated workloads; ~1 extra LLM call.
  - **Force + verify:** regulated (GDPR, HIPAA, SOX); ~2x latency, order-of-magnitude fewer bad citations.
- **Anti-pattern:** trusting "please cite accurately" in the system prompt. Frontier models still hallucinate citations (never zero).
- **Rejected alternative:** fine-tuning a citation-checker; breaks when the corpus rotates.

### Generation-layer: context under-utilization
- Model answers from **parametric memory**, sometimes contradicting retrieved context.
- **Signature:** faithfulness LOW while context_recall HIGH.
- **Fix:** stricter "answer only from the provided context, say so if it's not there" + a **groundedness gate** that blocks low-faithfulness responses.

### FM3 detection: know the conflict exists before you dedup
- Run a **pairwise contradiction pass** on top chunks (NLI model or cheap LLM "do these disagree?").
- **Temporal catch:** "what was the refund policy in 2024?" needs the *historical* version, so effective-date filtering must be **query-time-aware**, not blanket prefer-newest.

---

## 8. Each FM Maps to a Module 4 Lesson

| FM | Where the fix lives |
|---|---|
| FM1 | L3.1 (end-anchor) + L4.3 (reranker shortens context) |
| FM2 | L4.3 (reranker + threshold) + L4.1 (embedding quality) |
| FM3 | This lesson (dedupe + effective-date filter) |
| FM4 | L4.3 (HyDE) + L4.1 (embedding choice) |
| FM5 | L4.4 (TTL + re-index) + L3.6 (effective dates) + M7.5 (incremental sync + deletes) |
| FM6 | This lesson (decomposition) + L4.3 (multi-query) |
| FM7 | This lesson (validated citations) + L4.6 (Ragas faithfulness gate) |
| FM8 | L4.1 (multilingual embedder) + L4.2 (per-language chunking) |

### Fix-in-place vs. re-architect
- **Fix in place:** the FM is top-2 by frequency and a cheap fix (config, prompt, dependency swap) lifts accuracy without breaking anything.
- **Re-architect:** a structural choice caused it (e.g. English-only embedder + ~30% Spanish traffic). Costs 1–2 weeks of velocity; not doing it lets the FM compound every quarter.
- **Anti-pattern:** patching FM7 with a stronger model instead of post-generation verification. Stronger ≠ zero hallucination.

---

## 9. Analogy

Diagnosing RAG = a **doctor's differential diagnosis**. Symptoms (low accuracy, complaints, Ragas drop) have many causes (the 8 FMs). Run the checklist, narrow it down, treat the most likely.

**Limit of the analogy:** a doctor treats one patient; an FDE fixes a **population** by pivoting a 50-row spreadsheet. Also, the 8-FM tests are conventions *you* implement and pin in your eval harness (L4.6), not clinically validated tests.

---

## 10. Five Production Gotchas

1. **Dev golden set ≠ prod distribution.** The 88% → 62% gap is usually **golden-set drift**, not regression. Refresh quarterly with real prod-sampled queries.
2. **Two FMs at once.** FM1 + FM2 often co-occur. Mark both; don't force-pick.
3. **Customer SMEs in the loop.** FM7 needs domain knowledge (is the cited sub-clause actually wrong?). Pull in the customer's compliance officer.
4. **FM5 hides as FM3.** Old + new both retrieved looks like a conflict; the real cause is the old version shouldn't be retrievable. Re-index on updates; tag effective dates.
5. **The list isn't exhaustive.** Keep an "Other" bucket; if it exceeds ~20%, extend the taxonomy.

---

## 11. Where the Diagnostic Hits Hardest (AcmeCorp + Regulated Customers)

- **Policy version conflicts (FM3) are the rule.** Quarterly policy updates (v1 → v2 → v3); regulated customers add GDPR amendments, HIPAA addenda, and EU AI Act obligations (GPAI enforceable 2026-08-02). A naive RAG retrieves both versions and silently picks one. Baseline: dedupe by canonical doc ID + prefer newest effective date.
- **Language mismatch (FM8) is the most common engagement-extension failure.** English-only → rollout to Mexico City / Madrid / Singapore → ~20–30% of queries become low-recall. Fix: Cohere embed-v4.0 / voyage-3.5 + router pattern (L4.1); on-prem → bge-m3 + regional specialist (Qwen / Mistral / AraBERT).
- **Citation hallucination (FM7) is a compliance issue, not a quality issue.** Regulated bank (GDPR Art. 22; explanation obligation from Arts. 13–15 + Recital 71), US health-tech (HIPAA accuracy), global-markets finance (EU AI Act traceability). Auditors must trace each answer to the exact source clause. **Force + validate** is the audit-clean answer; it bridges to M6.2 Ragas faithfulness as a hard CI gate.

---

## 12. Interview Signal

FDE loops (Anthropic, Glean, Decagon, Sierra, Mistral) ask: *"Your RAG drops 30 points in prod, what do you do?"*

**Strong answer:** run the 8-FM diagnostic on 50 failing queries → tally by FM → fix the top 2–3 in priority order.
**Weak answer:** "We'll re-train."

---

## 13. Quick-Fire Quiz Answers

| Q | Answer |
|---|---|
| Q1: Lost-in-the-middle (FM1) | **b)** U-shape recall: start + end recalled well, middle drops |
| Q2: FM3 conflicting docs (Refund Policy v1 vs v2) | **c)** Dedupe by canonical doc ID; prefer newest effective date; tell the model a conflict was resolved |
| Q3: FM8 Spanish / Mandarin / code-mixed | **b)** Multilingual embedder + language detection + per-language routing + regional specialist |
| Q4: FM6 multi-hop gap | **b)** Needs 3+ docs; no single chunk has it. Fix: decompose + retrieve per sub-question + aggregate |
| Q5: FM7 citation hallucination fix | **b)** Force `[doc_id]` citations + validate post-generation; for compliance, verify the content supports the claim |

---

## 14. Practice Exercises (Topics Only)

- **Easy:** Reproduce lost-in-the-middle on a 30K-token context (needle test).
- **Easy:** Dedup-by-canonical-doc-id pipeline (FM3).
- **Medium:** FM4 cosine-threshold gate (voyage-3.5, GDPR erasure query).
- **Medium:** Multi-hop decomposition (compare GDPR and NIST AI RMF).
- **Hard:** Citation-validation loop (FM7): verify, re-prompt, fail closed.
- **Graded:** Categorize 50 failing answers, propose fixes, estimate uplift.
- **Medium:** Bisect failures: retrieval vs ranking vs generation.
- **Medium:** Flag failures on unlabeled prod traffic (reference-free).

---

## 15. Cheat Sheet (Memorize These)

- **"Model regressed" is usually a RAG failure.** Diagnose before rollback.
- **FM1 lost-in-middle · FM2 irrelevant · FM3 conflict · FM4 off-topic · FM5 stale · FM6 multi-hop · FM7 citation · FM8 language.**
- **Name the stage first** (query understanding → retrieval → ranking → generation; FM3/FM5 = data layer).
- **recall@10 splits retrieval from generation:** gold in top-10 but answer wrong → generation (FM1/FM7).
- **Fixes:** end-anchor + rerank (FM1) · dedupe + newest date (FM3) · multilingual embedder (FM8) · decompose (FM6) · force + validate citations (FM7).
- **Anchor + shorten + repeat** beats lost-in-the-middle, even with 1M context.
- **Hybrid + rerank = ~67% fewer retrieval failures** (Anthropic).
- **Faithfulness low + recall high = under-utilization** → "answer only from context" + groundedness gate.
- **Missing tenant filter = security incident,** so fail closed.
- **Find failures without ground truth:** judge metrics + thumbs-down / escalation / max-cosine < 0.5.
- **50 queries for triage, 500+ for tail FMs.** Keep it in a **spreadsheet**.
- **Refresh the golden set quarterly** from real prod queries.
- **"Other" bucket > 20%** = extend the taxonomy.
