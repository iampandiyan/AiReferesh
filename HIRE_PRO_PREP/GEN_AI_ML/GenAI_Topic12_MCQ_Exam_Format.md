# GenAI/AI-ML Principles — Topic 12: Timed Mixed MCQ Practice Set (Exam Format)

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Attempt all 20 questions first, without checking the answer key, to simulate real test conditions. Suggested pace: ~90 seconds/question (30 min ÷ 20 questions). Answer key with explanations is at the end.

---

## Questions

**1.** A model achieves 99% training accuracy but only 60% test accuracy. This is a classic sign of:
A. High bias
B. High variance
C. A well-fit model
D. Underfitting

**2.** What does `stratify=y` in `train_test_split` actually guarantee?
A. Faster splitting
B. The test set is always 20% of the data
C. Train and test sets preserve the original class proportions
D. Removes duplicate rows

**3.** What is the valid range of cosine similarity?
A. 0 to 1
B. -1 to 1
C. -infinity to infinity
D. 0 to infinity

**4.** Vector A points in the exact same direction as vector B, but A's magnitude is 3x larger. What is their cosine similarity?
A. 0.33
B. 3.0
C. 1.0
D. Cannot be determined

**5.** What does `chunk_overlap` in a text splitter actually guarantee, based on real tested behavior?
A. A fixed, guaranteed number of overlapping characters every time
B. Best-effort shared boundary text, constrained by where separators fall
C. No effect unless chunk_size is also increased
D. Automatic deduplication of repeated content

**6.** Why does decomposing a multi-hop question into sub-questions before retrieval improve accuracy?
A. It reduces the total number of tokens sent to the LLM
B. Each sub-question gets its own focused retrieval pass instead of one query trying to surface all needed facts at once
C. It eliminates the need for a vector database
D. It automatically re-ranks results

**7.** Setting temperature=0 (or very low) in an LLM's sampling makes output:
A. Completely random
B. More deterministic, favoring the single most likely token
C. Impossible to generate
D. Identical to top-p sampling

**8.** What is the key structural difference between top-k and top-p (nucleus) sampling?
A. They are identical, just different names
B. Top-k only works with temperature=0
C. Top-k keeps a fixed number of candidates; top-p keeps a variable number based on cumulative probability
D. Top-p is only used for classification tasks

**9.** On a tiny 4-row table, why might PostgreSQL's query planner ignore an HNSW vector index entirely and use a Sequential Scan instead?
A. HNSW indexes are broken on small tables
B. A full scan is cheaper than index overhead at very small scale — this is a real, verified cost-based decision
C. pgvector requires at least 1000 rows to function
D. The index needs to be rebuilt daily

**10.** In pgvector, what does the `<=>` operator compute?
A. L2 (Euclidean) distance
B. Cosine distance
C. Negative inner product
D. Jaccard similarity

**11.** What's the core structural difference between a "chain" and an "agent" in agentic AI systems?
A. Chains use Python, agents use JavaScript
B. A chain follows a fixed step sequence every time; an agent dynamically decides its next action
C. Agents cannot call tools
D. Chains are always faster regardless of task

**12.** In a LangGraph node function, what should it return?
A. The entire state object every time, fully reconstructed
B. Only the keys being updated — LangGraph merges partial updates automatically
C. A tuple of (state, error)
D. Nothing — state is modified in place

**13.** Which approach is generally best for keeping an AI system's knowledge current without retraining?
A. Full fine-tuning, repeated weekly
B. RAG — update the knowledge base, no retraining needed
C. Increasing the temperature parameter
D. LoRA fine-tuning only

**14.** What does LoRA do differently from full fine-tuning?
A. It retrains 100% of the model's weights, just faster
B. It freezes the original weights and trains small additional low-rank matrices instead
C. It only works for classification tasks
D. It removes the need for any training data

**15.** What does Mean Reciprocal Rank (MRR) specifically measure that plain Precision@k does not?
A. The total number of relevant documents retrieved
B. The position/rank of the FIRST relevant result
C. The average query latency
D. Whether the retrieval used cosine or L2 distance

**16.** Do RAGAS's core metrics (faithfulness, answer relevancy, etc.) require a live LLM to compute?
A. No, they're pure math like precision/recall
B. Yes — they are LLM-judged metrics, fundamentally different from ROUGE/BLEU/precision/recall
C. Only faithfulness needs an LLM, the rest don't
D. RAGAS doesn't use LLMs at all, it uses regex

**17.** What's the real, concrete difference between Lasso (L1) and Ridge (L2) regularization, demonstrated with actual coefficients?
A. They produce identical coefficients, just different names
B. Lasso can drive coefficients to exactly zero (feature selection); Ridge only shrinks them toward zero
C. Ridge is only for classification, Lasso only for regression
D. Lasso always performs worse than Ridge

**18.** Why did DBSCAN achieve a perfect 1.0 Adjusted Rand Index on moon-shaped clusters while KMeans only scored 0.2564?
A. DBSCAN used more computing power
B. KMeans assumes roughly spherical clusters; DBSCAN groups by density and handles non-convex shapes correctly
C. KMeans was given the wrong number of clusters
D. DBSCAN and KMeans always produce identical results

**19.** What's the key difference between MCP's stdio transport and its HTTP-based (streamable-http) transport?
A. stdio is for remote/hosted servers; HTTP is only for local testing
B. stdio is for local subprocess communication; HTTP-based transports are for remote/networked, hosted access
C. They require completely different tool definitions
D. stdio only works on Windows

**20.** Why do Transformers need positional encoding, while RNNs don't?
A. Transformers are too slow without it
B. Self-attention has no inherent notion of sequence order — it treats input as an unordered set unless position is explicitly injected
C. Positional encoding replaces the need for attention entirely
D. RNNs also need positional encoding, this is a myth

---

## Scoring Guide

| Score | Assessment |
|---|---|
| 18-20 correct | Strong — you're ready for this section of the gate |
| 14-17 correct | Good foundation — review the specific topics you missed before the exam |
| Below 14 | Revisit the full topic docs for the missed areas, prioritizing whichever topics had multiple misses |

---

## Answer Key & Explanations

| # | Answer | Topic | Explanation |
|---|---|---|---|
| 1 | B | Core ML | Large train/test gap = high variance (overfitting). High bias would show poor performance on BOTH train and test. |
| 2 | C | Core ML | Prevents accidental class imbalance skew in the split, especially important on imbalanced datasets. |
| 3 | B | Embeddings | 1 = identical direction, 0 = orthogonal, -1 = opposite direction. |
| 4 | C | Embeddings | Cosine similarity is magnitude-invariant — only direction matters. |
| 5 | B | RAG | Confirmed directly in testing — overlap didn't manifest as literal repeated text with newline-heavy documents, since the splitter respects separator boundaries first. |
| 6 | B | RAG | Directly matches the confirmed Lab 1.5 result (2% → 96% accuracy improvement from decomposition). |
| 7 | B | LLM Fundamentals | A commonly reversed MCQ trap — low temperature is NOT more random, it's more deterministic. |
| 8 | C | LLM Fundamentals | Top-p adapts to how confident/uncertain the distribution is; top-k always keeps a fixed count regardless. |
| 9 | B | Vector Databases | Directly confirmed with a real `EXPLAIN ANALYZE` run — indexes have overhead that only pays off past a certain data size. |
| 10 | B | Vector Databases | `<->` is L2 distance, `<=>` is cosine distance, `<#>` is negative inner product. |
| 11 | B | Agentic AI | Chains follow a fixed sequence; agents reason dynamically about what to do next. |
| 12 | B | Agentic AI | Verified directly in every working LangGraph example — nodes return partial state updates only. |
| 13 | B | Fine-tuning/Prompting/RAG | Updating a RAG knowledge base requires no retraining cycle, unlike fine-tuning. |
| 14 | B | Fine-tuning/Prompting/RAG | LoRA freezes the base model and trains small low-rank adapters, reducing catastrophic forgetting risk. |
| 15 | B | Evaluation Metrics | MRR = Mean RECIPROCAL RANK — cares only about the position of the first relevant hit. |
| 16 | B | Evaluation Metrics | This is exactly why RAGAS couldn't be run in the sandbox without a live LLM — it's LLM-judged, not pure computation. |
| 17 | B | ML Algorithms | Confirmed with real coefficient output — 4 of 10 Lasso coefficients hit exactly zero; Ridge shrunk all 10 but kept them non-zero. |
| 18 | B | ML Algorithms | A dramatic, real, verified gap — KMeans's centroid-based approach can't handle non-convex cluster shapes the way density-based DBSCAN can. |
| 19 | B | MCP | The exact same server/tool definitions ran under both transports in the verified demo — only the hosting/access pattern changes. |
| 20 | B | Transformers | RNNs process tokens sequentially, inherently encoding order; self-attention processes all tokens in parallel with no built-in order awareness. |

---

## Status
20 questions drawn directly from verified, real-tested content across all 11 GenAI/AI-ML topics — not generic textbook trivia. Exam-style format: attempt all questions first, then check the answer key.
