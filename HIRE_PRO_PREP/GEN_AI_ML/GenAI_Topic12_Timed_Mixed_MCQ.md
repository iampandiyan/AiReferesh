# GenAI/AI-ML Principles — Topic 12: Timed Mixed MCQ Practice Set

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

This is the final GenAI/AI-ML topic — a mixed practice set drawing from all 11 prior topics, simulating the mixed-topic nature of the real gate (which combines DSA, DB, GenAI/AI-ML, and API/Backend all in one 30-minute MCQ round). An interactive version of this same quiz was also generated for timed self-testing — this document is the written reference for review afterward.

**Suggested use:** time yourself at roughly 90 seconds/question (30 min ÷ 20 questions) to simulate real pressure, then review explanations for anything missed.

---

## Questions & Answers

**1. (Topic 1 — Core ML)** A model achieves 99% training accuracy but only 60% test accuracy. This is a classic sign of:
**Answer: High variance.** A large train/test gap is the hallmark of overfitting. High bias would show poor performance on both train and test instead.

**2. (Topic 1 — Core ML)** What does `stratify=y` in `train_test_split` actually guarantee?
**Answer: Train and test sets preserve the original class proportions.** Prevents accidental class imbalance skew in the split, especially important on imbalanced datasets.

**3. (Topic 2 — Embeddings)** What is the valid range of cosine similarity?
**Answer: -1 to 1.** 1 = identical direction, 0 = orthogonal, -1 = opposite direction.

**4. (Topic 2 — Embeddings)** Vector A points in the exact same direction as vector B, but A's magnitude is 3x larger. What is their cosine similarity?
**Answer: 1.0.** Cosine similarity is magnitude-invariant — only direction matters.

**5. (Topic 3 — RAG)** What does `chunk_overlap` in a text splitter actually guarantee, based on real tested behavior?
**Answer: Best-effort shared boundary text, constrained by where separators fall.** Confirmed directly — overlap didn't manifest as literal repeated text with newline-heavy documents, since the splitter respects separator boundaries first.

**6. (Topic 3 — RAG)** Why does decomposing a multi-hop question into sub-questions before retrieval improve accuracy?
**Answer: Each sub-question gets its own focused retrieval pass** instead of one query trying to surface all needed facts at once — directly matches the confirmed Lab 1.5 result (2% → 96% accuracy).

**7. (Topic 4 — LLM Fundamentals)** Setting temperature=0 (or very low) in an LLM's sampling makes output:
**Answer: More deterministic, favoring the single most likely token.** A commonly reversed MCQ trap — low temperature is NOT more random.

**8. (Topic 4 — LLM Fundamentals)** What is the key structural difference between top-k and top-p (nucleus) sampling?
**Answer: Top-k keeps a fixed number of candidates; top-p keeps a variable number based on cumulative probability.** Top-p adapts to how confident/uncertain the distribution is.

**9. (Topic 5 — Vector Databases)** On a tiny 4-row table, why might PostgreSQL's query planner ignore an HNSW vector index entirely and use a Sequential Scan instead?
**Answer: A full scan is cheaper than index overhead at very small scale.** Directly confirmed with a real `EXPLAIN ANALYZE` run in Topic 5.

**10. (Topic 5 — Vector Databases)** In pgvector, what does the `<=>` operator compute?
**Answer: Cosine distance.** `<->` is L2 distance, `<#>` is negative inner product.

**11. (Topic 6 — Agentic AI)** What's the core structural difference between a "chain" and an "agent"?
**Answer: A chain follows a fixed step sequence every time; an agent dynamically decides its next action.**

**12. (Topic 6 — Agentic AI)** In a LangGraph node function, what should it return?
**Answer: Only the keys being updated** — LangGraph merges partial updates into the full state automatically, as verified in every working example.

**13. (Topic 7 — Fine-tuning vs Prompting vs RAG)** Which approach is generally best for keeping an AI system's knowledge current without retraining?
**Answer: RAG.** Update the knowledge base directly — no retraining cycle needed, unlike fine-tuning.

**14. (Topic 7 — Fine-tuning vs Prompting vs RAG)** What does LoRA do differently from full fine-tuning?
**Answer: Freezes the original weights and trains small additional low-rank matrices instead**, cutting trainable parameters dramatically and reducing catastrophic forgetting risk.

**15. (Topic 8 — Evaluation Metrics)** What does Mean Reciprocal Rank (MRR) specifically measure that plain Precision@k does not?
**Answer: The position/rank of the FIRST relevant result** — not the overall proportion of relevant results in the top k.

**16. (Topic 8 — Evaluation Metrics)** Do RAGAS's core metrics (faithfulness, answer relevancy, etc.) require a live LLM to compute?
**Answer: Yes — they are LLM-judged metrics**, fundamentally different from pure-computation metrics like ROUGE/BLEU/precision/recall.

**17. (Topic 9 — Common ML Algorithms)** What's the real, concrete difference between Lasso (L1) and Ridge (L2) regularization?
**Answer: Lasso can drive coefficients to exactly zero** (genuine feature selection); **Ridge only shrinks them toward zero** — confirmed with real coefficient output (4 of 10 Lasso coefficients hit exactly zero).

**18. (Topic 9 — Common ML Algorithms)** Why did DBSCAN achieve a perfect 1.0 Adjusted Rand Index on moon-shaped clusters while KMeans only scored 0.2564?
**Answer: KMeans assumes roughly spherical clusters; DBSCAN groups by density and correctly handles non-convex shapes.** A dramatic, real, verified gap.

**19. (Topic 10 — MCP)** What's the key difference between MCP's stdio transport and its HTTP-based (streamable-http) transport?
**Answer: stdio is for local subprocess communication; HTTP-based transports are for remote/networked, hosted access.** The exact same server/tool definitions ran under both in the verified demo.

**20. (Topic 11 — Transformers)** Why do Transformers need positional encoding, while RNNs don't?
**Answer: Self-attention has no inherent notion of sequence order** — it processes all tokens in parallel as an unordered set unless position is explicitly injected. RNNs inherently encode order through sequential processing.

---

## Scoring Guide

| Score | Assessment |
|---|---|
| 18-20 correct | Strong — you're ready for this section of the gate |
| 14-17 correct | Good foundation — review the specific topics you missed before the exam |
| Below 14 | Revisit the full topic docs for the missed areas, prioritizing whichever topics had multiple misses |

---

## Status
20 questions drawn directly from verified, real-tested content across all 11 GenAI/AI-ML topics — not generic textbook trivia. An interactive timed version of this same set was also generated for hands-on self-testing.

This completes the GenAI/AI-ML Principles track (Topics 1–12). Ready to move to **Database Fundamentals** or **API/Backend Fundamentals** whenever you want to continue — or revisit any DSA topics (3–10) that are still pending from the original track.
