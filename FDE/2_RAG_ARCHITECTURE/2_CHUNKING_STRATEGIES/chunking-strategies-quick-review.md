# Module 4 · Lesson 4.2 — Chunking Strategies (Quick Review)

> **One-line idea:** Chunking = cutting documents into pieces before embedding. Where you cut decides whether the model sees complete, citable context. It is the biggest accuracy lever after embedding choice, and the most under-invested.

---

## 1. The AcmeCorp Story (Why This Matters)

- **Corpus:** ~800 FAQs + ~4,200 long-form articles + ~30 policy PDFs.
- **Setup:** Default `RecursiveCharacterTextSplitter`, 500 tokens, 50 overlap, applied to everything.
- **Bug:** Refund Policy **clause 3.2** is split across chunk 142 and chunk 143. Header sits in 142, eligibility text in 143.
- **What happened:** Model retrieved only 143, had no section context, cited clause 3.1 instead → **citation hallucination (FM7)** → ~$4K legal-escalation ticket.
- **Fix:** Per-content-type chunking + semantic + hierarchical + parent expansion at retrieval.
- **Result:** Faithfulness **~64% → ~89%** (same docs, same model, same retrieval-K; only the chunker changed).

---

## 2. What You Should Be Able To Do

- Pick between fixed-size, semantic, sentence-window and hierarchical chunking per content type.
- Implement **parent-document retrieval** (the default for legal/policy RAG).
- Handle tables, code, and chat logs with the right chunker.
- Diagnose whether a failing RAG is due to chunking, chunk size, overlap, or upstream parsing.
- Plan a re-chunk migration without downtime.

---

## 3. The 4 Chunking Strategies

| Strategy | How it works | Use for |
|---|---|---|
| **Fixed-size** | ~500 tokens + 50 overlap. Splits mid-sentence/clause | Blogs, READMEs, transcripts, reviews |
| **Semantic** | Cuts at sentence/paragraph/topic boundaries; sub-clauses stay whole | PDFs, policies, legal text, long-form help articles |
| **Sentence-window** | N sentences per chunk, K sentences overlap | Long-form reasoning, multi-sentence claims |
| **Hierarchical** | Index small child chunks; expand to the parent section for the model | Policies, contracts, regulations, multi-section articles |

- **Tradeoff:** Fixed-size is cheap and fast but loses citation traceability. Semantic + hierarchical costs ~2–3x more at ingest but fixes the FM7 bug.

### "Fixed-size" is really RecursiveCharacterTextSplitter
- Walks separators: paragraph → line → sentence → word → character. Only goes finer when a piece is still too big.
- Smarter than raw `CharacterTextSplitter` (single separator, worst mid-clause cuts).
- Still has **no idea "clause 3.2" is one unit**, so policy docs need semantic + hierarchical on top.

---

## 4. Which Chunker for Which Content?

| Content type | Best chunker | Why |
|---|---|---|
| Policy / ToS / SLA | Semantic + hierarchical | Sub-clauses whole; parent gives section context |
| API docs / code | Function-boundary | One function = one chunk |
| Pricing / SLA tables, CSVs | Row-as-chunk, header replicated | Each row complete; header gives column meaning |
| Support chat transcripts | Turn-as-chunk, thread-as-parent | Turn is retrievable; thread is context |
| FAQ entries | One FAQ = one chunk | Already short and self-contained |
| Blogs, transcripts, reviews | Fixed 500 + 50 overlap | No structure; cheap default is fine |

### Anti-example: JSON spec with a fixed splitter
- A 500-token splitter cuts mid-field, leaving orphan tails like `["free","pro","business"]` with no parameter name.
- Retrieval returns the orphan tail → FM7 citation hallucination.
- **Fix:** Structure-aware splitter (`RecursiveJsonSplitter` or custom). One field = one chunk, parent path stored as metadata.

---

## 5. How Semantic Chunking Decides Where to Cut

- Embeds every sentence, compares adjacent groups, **cuts where cosine distance spikes** (topic shift).
- No fixed size, and **no fixed overlap needed** (the cut is already in a low-similarity trough).
- Key knobs:

| Knob | Meaning |
|---|---|
| `percentile` (default) | Cut above the Nth percentile of distances (e.g. 95th). Robust, corpus-relative |
| `standard_deviation` | Cut above mean + k·σ. Tighter on low-variance docs |
| `gradient` | Cut on rate of change. Best for gradually drifting topics |
| `buffer_size` | Sentences grouped per comparison. Bigger = smoother, less noise-driven cuts |

- Real API: `SemanticChunker(embeddings, breakpoint_threshold_type=...)` from `langchain_experimental`. No `parent_aware` flag exists.
- Get section context from **parent-doc retrieval**, not from overlap.

---

## 6. Beyond the 4: LLM-Driven Chunking

| Method | Idea | Cost / tradeoff |
|---|---|---|
| **Agentic chunking** (Kamradt Level 5) | LLM proposes boundary offsets, so it cuts on meaning | One LLM call per doc; most expensive. Use when semantic breakpoints keep misfiring (cross-referential contracts) |
| **Proposition / Dense-X** (Chen 2023) | Decompose text into standalone factoid statements and index those | ~+5–12pp on hard retrieval; one LLM call per passage; index bloat; can lose nuance, so keep a pointer to the source passage |

---

## 7. Parent-Document Retrieval (Policy / Long-Form Default)

**Index small, retrieve small, expand to parent.**

1. Embed small child chunks (~150–250 tokens): precise matching.
2. Retrieve top-K children.
3. Deduplicate and resolve to parent section (~800–1500 tokens).
4. Send **parents** (not children) to the model.

- **Use when:** strong hierarchy (clauses, contract sections, Markdown H1/H2/H3, Notion blocks).
- **Skip when:** flat text with no hierarchy (transcripts, reviews); parents just add noise.
- **Cost/benefit:** ~+20% storage for ~+25pp faithfulness on policy-citing questions.
- Canonical implementation: LangChain `ParentDocumentRetriever`.

### Metadata that makes a citation traceable
Stamp on every chunk at ingest:

| Field | Purpose |
|---|---|
| `chunk_id` | Unique; points into doc store |
| `doc_id` | Source document |
| `section_id` | Parent for expansion |
| `page` | Clickable, verifiable citation |
| `effective_date` | Which policy revision was in force |
| `version` | Chunker version (guards against re-chunk amnesia) |

Result: "Refund Policy, Section 3, clause 3.2 (p.4, eff. 2026-05-01)", auditable end to end.

---

## 8. Sentence-Window and Overlap Rules

- **Sentence-window:** N sentences (~5–10) per window; next overlaps by K (~1–3).
- Retrieval matches the **centre sentence** (precision); generation sees the **whole window** (context).
- LlamaIndex `SentenceWindowNodeParser`; ~+7–11pp faithfulness on long-form slice.
- **Use for:** research notes, RFCs, narrative docs. **Skip for:** FAQs, policy text.
- Overlap costs ~+15–30% storage/re-embed.

### Overlap rule of thumb

| Chunker | Overlap |
|---|---|
| Fixed-size | 50–75 tokens (~10–15%) |
| Semantic | None; the boundary is the safety |
| Sentence-window | 1–3 sentences |
| Hierarchical | None on children; the parent is the overlap |

---

## 9. Per-Content-Type Chunking Details

### Tables
- **Never** let a fixed splitter cut a table row.
- Option A: **each row = one chunk, header replicated** (best for retrieval).
- Option B: **whole table = one chunk** if it fits ~1500 tokens (best for cross-row reasoning).

### Code
- Chunk at **function/class boundaries**. Never split a function body.
- Keep docstring + signature + body together (Sourcegraph / Cursor pattern).

### Chat logs
- **Turn** (~150 tokens) = retrievable unit. **Thread** (~800–2000 tokens) = parent.
- On retrieval, expand from turn to thread.

### Factory pattern (pseudocode)
`chunker_for(content_type)` returns the right chunker:
- pdf / regulation / contract → `SemanticChunker`
- markdown / readme → header-based
- code / api_docs → function-boundary
- csv / table → row-as-chunk (header replicated)
- chat / transcript → turn chunker, thread parent
- default → fixed 500 / 50

> **Only `SemanticChunker` is a real API.** The others are teaching sketches you build yourself.
> Per-content-type pipelines are ~2–3x more code to maintain, but they are the path to the +25pp lift.

---

## 10. How to Choose Chunk Size (Measure, Don't Guess)

1. **Freeze a golden set:** 30–50 questions, each with the gold chunk(s) and a reference answer.
2. **Sweep:** sizes 256 / 512 / 1024 × overlaps 0 / 10 / 15%. Hold embedder, retriever, K, prompt constant.
3. **Plot two curves:** recall@k and faithfulness vs. size.
4. **Pick the knee:** where recall plateaus and faithfulness peaks. Usually **not the max-recall row**, because oversized chunks dilute embeddings and hurt faithfulness.

Example sweep result:

| Size / overlap | Recall@5 | Faithfulness | Verdict |
|---|---|---|---|
| 256 / 10% | 0.71 | 0.79 | Precise match, context-starved |
| **512 / 15%** | **0.86** | **0.89** | **The knee: ship this** |
| 1024 / 10% | 0.88 | 0.83 | Recall up, faithfulness down (diluted) |

---

## 11. Late Chunking and Contextual Retrieval

### Late chunking
- **Embed the whole doc first** (long-context embedder, ~8K–32K tokens), then chunk the contextualised embeddings. Each chunk's vector "remembers" the full document.
- **Use for:** short docs (<~8K tokens): memos, reviews, single-section contracts, FAQs.
- **Skip for:** docs bigger than the embedder's context (full ToS ~25K tokens).
- **Tradeoff:** simpler pipeline, but locked to long-context embedders (Jina v3, Voyage long-context).

### Anthropic's Contextual Retrieval (cheapest big win)
- Before embedding, an LLM reads the whole doc and writes **~50–100 tokens of chunk-specific context** ("This chunk is from the Refund Policy, Section 3, month-11 cancellation rule"). Prepend it to the chunk.
- Fixes the stranded-chunk (FM7) bug **at the embedding layer**.
- Reported **~49% fewer failed retrievals** (with contextual BM25 + reranker).
- Cost with prompt caching: ~**$1.02 per 1M doc tokens**.
- Composes with everything: semantic/hierarchical chunker → add context prefix → expand to parents at retrieval.

---

## 12. Re-Chunking = Re-Embedding

- New chunker → new boundaries → new text → new embeddings. **Whole index is invalidated.**
- Cost example: 1M docs (~1–2B tokens) at ~$0.06/1M ≈ **$60–$120** embedding spend (fully loaded migration costs more).
- **Plan a re-chunk when:** faithfulness regressed, or a new content type entered the corpus.
- **Skip for:** small chunk-size/overlap tuning within the same chunker family (A/B on a small slice).

### Migration runbook
1. **Dual-write:** new docs chunked and embedded by both old and new chunkers.
2. **Backfill:** overnight re-chunk + re-embed of historical corpus.
3. **Shadow-read:** ~10% of queries hit the new index; compare retrieval@K and faithfulness.
4. **Cutover:** when new beats old by **>~2pp** on the promotion gate.
5. **Retire** old index after a **30-day rollback window**.

- Tag every vector with `chunker_version` and reject reads against stale versions.
- Total: ~2 weeks of dual-write for safety.

---

## 13. AcmeCorp Per-Content-Type Plan

| Content | Count | Approach |
|---|---|---|
| FAQ entries | ~800 | One FAQ = one chunk. Don't re-cut |
| Long-form articles | ~4,200 | Semantic at sentence boundaries, ~50-token overlap, ~3–5 chunks each, article ID as parent |
| Policy PDFs | ~30 | Sub-clause-aware semantic + hierarchical. **Never split clause 3.2.** Regex sentinel test before promotion |
| Pricing / SLA tables | — | Row-as-chunk, header replicated |

- **Regulated expansion** (EU bank GDPR, HIPAA, OCC bulletins): same framework. Regulator PDFs go through the policy chunker; customers often spot-check ~20–30 sub-clauses during diligence.

---

## 14. Five Production Gotchas

1. **The "clause 3.2" split:** fixed chunkers split mid-numbering. Add a regex sentinel test before promotion.
2. **The table cut:** validate that any chunk with `<table>` markers contains both open and close tags.
3. **Parent-doc explosion:** 10 matched children across 8 parents blows the context window. **Cap parents at K≈3–5.**
4. **Chunk-size drift:** tokenizer mismatch (OpenAI tokenizer vs character-based chunker) makes 500 become 600. Use the same tokenizer end-to-end.
5. **Re-chunk amnesia:** changed the chunker but didn't re-embed, so queries hit old boundaries. Use chunker-version metadata and reject stale reads.

---

## 15. FDE Field Note: The Chunker-Selection Memo

A 1-page memo to write before committing to a chunker:

1. Per-content-type inventory of the corpus.
2. Chosen chunker per type with a one-line defence.
3. Golden-set proof: new chunker beats default by **>~5pp** faithfulness.
4. Re-chunk runbook (dual-write, backfill, shadow-read, cutover, rollback).

This is what compliance officers and DPOs sign off on, not the code. **If you can't defend the chunker in writing, don't ship it.** Chunker choice must be **eval-driven** (Hamel Husain).

---

## 16. Analogy

Chunking = cutting a book for a reader who can only read one page at a time.
- **Chapter boundaries** (semantic): each piece is self-contained.
- **Every 250 words** (fixed-size): sentences split, argument lost.
- **Finger-bookmark on the chapter intro** (hierarchical / parent-doc): reader can flip back for context.

**Limit of the analogy:** an LLM can't re-read previous pages at query time. The chunk it gets is *all* it sees.

---

## 17. Quick-Fire Quiz Answers

| Q | Answer |
|---|---|
| Q1: Clause split across chunks 142/143 | **b) Citation hallucination** (143 lacks the header from 142) |
| Q2: Parent-document retrieval | **c) Index small children, retrieve them, expand to parent for context** |
| Q3: Fixed-size overlap rule | **b) 50–75 tokens (~10–15%)** |
| Q4: Pricing-tier table | **b) Row-as-chunk with header replicated, or whole table as one chunk** |
| Q5: Re-chunk cost (1M docs) | **b) ~Same as re-embedding (~$60–$120 at voyage-3.5)** |

---

## 18. Practice Exercises (Topics Only)

- **Easy:** Reproduce the GDPR Article 7(7)(b) split bug (500-token vs. semantic), diff the outputs.
- **Easy:** Build the parent-doc map `{parent_id: {parent_text, children}}` and demo the lookup.
- **Medium:** Implement `chunker_for()` for 5 content types.
- **Medium:** Hierarchical retrieval flow + faithfulness eval.
- **Hard:** Late chunking vs chunk-then-embed on a ~7K-token section (5 cross-chunk questions).
- **Medium:** Chunk-size / overlap sweep (9 configs), find and defend the knee.
- **Hard:** Contextual retrieval: situate every chunk before embedding.
- **Graded:** Production chunking pipeline for a mid-market bank's OCC-bulletin RAG (~1M docs).

---

## 19. Cheat Sheet (Memorize These)

- Chunker swap alone: **64% → 89% faithfulness**.
- **FAQ = 1 chunk. Policy = semantic + hierarchical. Table = row + header. Code = function. Chat = turn + thread parent.**
- Semantic = no overlap needed. Fixed = 50–75 tokens. Window = 1–3 sentences.
- **Parent-doc:** index small, expand to parent, **cap parents at 3–5**.
- Stamp metadata: `doc_id`, `section_id`, `page`, `effective_date`, `chunker_version`.
- **Pick chunk size by the knee** (recall plateau + faithfulness peak), not max recall.
- **Contextual retrieval** = cheapest big win (~49% fewer failed retrievals).
- **Re-chunk = re-embed.** Dual-write → backfill → shadow-read → cutover → 30-day rollback.
- **Measure first, write the memo, then ship.**
