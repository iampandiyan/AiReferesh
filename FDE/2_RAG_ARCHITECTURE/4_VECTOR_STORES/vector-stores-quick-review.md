# Module 4 · Lesson 4.4 — Vector Stores Deep-Dive (Quick Review)

> **One-line idea:** After embedding, you need a place to store millions of vectors and find the closest ones fast. Pick the store by **customer constraints** (existing stack, audit, residency, scale), not by headline benchmark.

---

## 1. The AcmeCorp POC Story (Why This Matters)

- **Eng team wants:** Pinecone Serverless (p95 ~**12 ms**, managed).
- **Infra team says:** AcmeCorp already runs **Postgres 16** with a DBA, backups, and access controls. A new vector vendor = a new vendor.
- **Benchmark:** Pinecone ~12 ms vs pgvector (HNSW) ~18 ms. Pinecone is faster, but only by ~**6 ms**.
- **Decision:** **pgvector wins**, not because it's faster, but because **5 constraints stack** (existing Postgres, DBA discipline, backups, access controls, single audit boundary).
- **Pinecone wins when:** greenfield with no Postgres, managed-first preference, or scale beyond ~100M vectors.

---

## 2. What You Should Be Able To Do

- Name the 5 stores and give a one-line trade-off for each.
- Compare HNSW vs IVF on recall, build time, memory, tuning.
- Recommend a store given residency, security-review, and cost constraints, and defend it in 90 seconds.
- Plan a store migration without downtime (dual-write).

---

## 3. Key Numbers

| Number | Meaning |
|---|---|
| **12 ms** | Pinecone p95 (index-only, same region) |
| **18 ms** | pgvector p95 (Postgres 16 + HNSW) |
| **5** | Production vector stores |
| **multi-week** | Cross-store migration timeline |
| **<10M docs, ~10 RPS** | AcmeCorp scale where procurement beats latency |

---

## 4. The 5 Vector Stores

| Store | What it is | p95 | Best for |
|---|---|---|---|
| **pgvector** | Postgres extension. HNSW + IVFFlat; `tsvector` for BM25 in the same DB | ~18 ms | **AcmeCorp default**; mid-market with existing Postgres |
| **Qdrant** | Rust, self-host or managed. Native sparse + dense hybrid, great filtering | ~10 ms | Greenfield self-hosted, hybrid native |
| **Pinecone** | Managed Serverless. Zero ops, hosted US/EU | ~12 ms | Non-Postgres, managed-first, global |
| **Weaviate** | Multi-modal (text/image/audio), built-in embedder modules, GraphQL + REST | ~15 ms | Multi-modal workloads |
| **Milvus** | Distributed by default, built for 100M+ vectors; big ops overhead | ~20 ms at scale | High scale |

---

## 5. Three Common Misconceptions

1. **"Pinecone is always faster than pgvector."** False. Below ~5M vectors with Postgres already in the stack, co-located pgvector saves the network hop and per-query cost. Pinecone's edge shows at 50M+ vectors, sustained high QPS, or zero-ops needs.
2. **"More dimensions = better quality."** False. Over-dimensional embeddings on small corpora can hurt HNSW recall (e.g. 1024-dim BGE on 5K docs can lose to 384-dim).
3. **"You can hot-swap vector stores: dump and reload."** False. Migration is multi-week: re-embed if metric/dimension differs, dual-write, gradual read cutover, 30-day rollback window. Each store has a proprietary index format, so snapshot-and-restore doesn't work.

---

## 6. HNSW vs IVF

| Property | **HNSW** | **IVF** |
|---|---|---|
| Recall@10 | ~96–99% | ~89–95% |
| Query latency | Low | Moderate |
| Build time | Slow (minutes to hours at 10M) | Fast (seconds to minutes) |
| RAM | High (graph in memory) | Low (centroids only) |
| Ingest throughput | Lower | Higher |
| Best for | **Query-heavy** (support agent, policy Q&A, compliance RAG) | **Ingest-heavy** (live feeds, log search) |

- **Flat brute-force** is fine under ~100K vectors.
- pgvector HNSW: `m = 16, ef_construction = 64` (defaults).
- pgvector IVFFlat: `lists ≈ sqrt(N_rows)`.

---

## 7. Why pgvector Wins on the Procurement Checklist

Trade-off: accept ~6 ms extra p95 for zero new vendor surface.

1. **Existing Postgres:** `CREATE EXTENSION vector;` takes 1 day vs 6–12 weeks of vendor procurement + security review.
2. **Audit-friendly:** queries logged via `pg_stat_statements`; same RBAC; auditors map 1:1 to existing procedures (SOC2 later).
3. **Backups:** existing Postgres backups cover the vector index for free.
4. **Access controls:** row-level security and column encryption on the same table.
5. **Regional / sovereign customers:** self-host in the customer's VPC with zero data egress. Pinecone needs cross-border data-flow approval (~8–14 weeks).

- The 6 ms is real but bounded. At ~1M docs / ~10 RPS it doesn't move the SLO. At ~100M docs / ~1000 RPS it matters, and that's when you migrate.
- **When not pgvector:** greenfield + no Postgres + global multi-region → Pinecone.

---

## 8. Hybrid Search Support Across Stores

| Store | Hybrid (sparse + dense) | How |
|---|---|---|
| **pgvector** | Yes (manual) | `tsvector` + vector column in one Postgres; RRF in app code |
| **Qdrant** | Yes (native) | Built-in sparse + dense vectors |
| **Pinecone** | Yes (managed) | Separate sparse-dense indexes + hybrid API |
| **Weaviate** | Yes (native) | `hybrid` operator with alpha tuning |
| **Milvus** | Partial | Native dense; sparse via Elasticsearch + app-level fusion |

- **AcmeCorp default:** pgvector + tsvector. One transaction, one backup, one access boundary; fuse with RRF in application code (as in L4.3).

---

## 9. Reconciling Latency: Index-Only vs End-to-End

- Pinecone's **12 ms is index-only** from the same region. But it's hosted, so every query pays a **network round-trip**.
- Co-located pgvector's **18 ms is already end-to-end** (~0 ms hop).
- From another region, the wire adds tens to ~220 ms, swamping the 6 ms index win.
- **Rule:** compare stores on **end-to-end p95 from where your callers live**, not on vendor in-region index latency.

---

## 10. Anti-Pattern: Pinecone Serverless at Small Scale

- AcmeCorp POC: 5K docs, ~0.5 RPS.
- **Pinecone:** ~$50–70/mo (Standard $50 minimum + usage) + query cost + cross-region egress (~$0.08–0.10/GB).
- **pgvector on existing Postgres:** ~$0 marginal, $0 egress.
- **Break-even:** ~5M docs at sustained 50+ RPS, or no Postgres in the stack.
- Also pointless because LLM inference (~800 ms p95) dwarfs a ~6 ms vector win.
- **Reserve Pinecone** for genuine zero-ops + scale + multi-region needs.

---

## 11. Six Levers for Operating the Index

### 1. Quantization (memory vs recall)
| Type | Size cut | Notes |
|---|---|---|
| **Scalar (SQ)** float32 → int8 | ~4x | Tiny recall loss; rescore top candidates |
| **Product (PQ / IVF-PQ)** | ~8–32x | More recall loss; billion-scale FAISS recipe |
| **Binary (BQ)** 1 bit/dim | ~32x | Hamming distance; float-rescore top few hundred |
| **pgvector `halfvec`** (0.7.0+) | 2x | Float16; negligible recall change; low-risk first move |

- 1024-dim: ~4 GB at 1M vectors (float32) → ~1 GB (int8) → ~128 MB (binary). At 100M: ~400 GB → ~100 GB → ~13 GB.
- **Quantize to keep the hot index in RAM, then rescore to recover recall.**

### 2. Filtered search (the recall cliff)
- **Post-filter:** ANN top-k then drop non-matching rows. A selective filter (~1% of rows) can drop recall from ~0.97 to ~0.55, or return fewer than k results.
- **Naive pre-filter:** can strand the HNSW entry node from the surviving subgraph.
- **Fixes:** Qdrant's **filterable HNSW**; pgvector **partial indexes** + **iterative index scans** (0.8).
- **Rule:** measure recall with your real filters applied.

### 3. Multi-tenancy
| Pattern | Pros / cons |
|---|---|
| **Namespace/partition per tenant** | Cheap, logical isolation; whale tenant = noisy neighbour |
| **Row-level (`tenant_id` + WHERE / RLS)** | Cheapest; inherits the filter recall cliff; give big tenants a partial index |
| **Separate index/collection/DB per tenant** | Hard isolation, per-tenant encryption/delete; cost and ops scale with tenant count |

- **Default:** row-level for the long tail, dedicated collection for whale or regulated tenants.

### 4. Freshness and delete tombstones
- HNSW deletes are **soft (tombstones)**; recall and latency drift as they pile up.
- pgvector: need `VACUUM`, eventually `REINDEX`. Qdrant/Milvus compact automatically.
- HNSW inserts are costly (~`ef_construction` work each). IVF appends are cheap but centroids drift.
- Freshness lag: seconds for single-row pgvector insert, minutes for batch rebuild.
- **Runbook:** schedule VACUUM/optimise; REINDEX/rebuild when tombstones exceed ~**20%**.

### 5. Recall-vs-latency sweep
Tune the dominant knob on **your corpus**: IVF `nprobe`, HNSW `ef_search`.

| Setting | Recall@10 | p95 (index-only) |
|---|---|---|
| IVF nprobe = 8 | 0.82 | ~4 ms |
| IVF nprobe = 20 | 0.88 | ~7 ms |
| IVF nprobe = 80 | 0.95 | ~18 ms |
| HNSW ef_search = 40 | 0.90 | ~5 ms |
| HNSW ef_search = 128 | 0.96 | ~12 ms |
| HNSW ef_search = 256 | 0.98 | ~22 ms |

- Dial, not a default: stop at the first value that clears your recall SLO. Re-run after any embedding or corpus change.

### 6. DiskANN (when the graph outgrows RAM)
- HNSW keeps the whole graph in RAM; past ~100M–1B vectors, RAM becomes the constraint.
- **Vamana / DiskANN:** SSD-laid-out graph + small in-RAM cache of PQ vectors.
- Where: **Milvus DiskANN**, **pgvectorscale** (StreamingDiskANN for Postgres), **CAGRA** (GPU, via NVIDIA cuVS).
- Trade-off: ~2–5x slower than in-RAM HNSW, ~5–10x less RAM.
- AcmeCorp (<10M docs): non-issue.

---

## 12. Decision Framework

| Customer constraint | Pick | Why |
|---|---|---|
| Mid-market SaaS with existing Postgres (AcmeCorp) | **pgvector** | 5-constraint stack, zero new vendor |
| Self-hosted greenfield, native hybrid | **Qdrant** | Best ops surface; sparse + dense built in |
| Managed-first, no DB infra, global | **Pinecone Serverless** | Lowest p95, zero ops, ships in 1 day |
| Multi-modal (text + image) | **Weaviate** | Native multi-modal + modules |
| 100M+ vectors | **Milvus** | Distributed; built for the high end |
| On-prem (regulated EU, US health-tech, global-markets finance) | **pgvector or Qdrant self-host** | Stays in customer VPC; zero egress |

- If scale is already >100M docs, skip the framework and go straight to Milvus.

---

## 13. AcmeCorp Operational Story

- **Setup:** Postgres 16 on managed service (RDS / Cloud SQL / Crunchy), us-east-1 or eu-west-1 per residency. HNSW on the embedding column, `tsvector` on chunk text. The same DBA runs both.
- **HNSW build:** ~30 min on 5K articles; ~4–8 hours at 10M docs. Run as a DDL migration on a **replica, then promote**.
- **Backup:** existing nightly `pg_dump`; no special handling.
- **Sharding:** not needed at 5K–50M docs; M7.1 covers partial indexes for 100M+.
- **Enterprise tier** (regulated EU bank, health-tech, global-markets finance): same pgvector pattern inside their VPC. Auditor maps to existing Postgres procedures (on-prem-deployer archetype).
- **Qdrant self-host:** when no Postgres exists (greenfield startups); better hybrid ergonomics.
- **Pinecone Serverless:** when no DBA and zero ops wanted; watch cross-region egress and residency review (~8–14 weeks in regulated industries).
- **Milvus:** only when projecting 100M+ vectors.

---

## 14. Analogy

A vector store = your library's **catalogue + shelving**.
- **pgvector:** catalogue in the same building as the books.
- **Pinecone:** managed catalogue in a different city. Faster, but remote.
- **Qdrant:** self-hosted catalogue with efficient shelving.

**Limit of the analogy:** vector indexes ingest millions of vectors in minutes (the catalogue underplays throughput). Also, a store is only as good as the **embedding model** that filled it. Great store + bad embedder = bad retrieval.

---

## 15. Production Gotchas

1. **Index rebuild on schema change:** new embedding column = re-index every row (4–8 hrs at 10M). Do on a replica + promote.
2. **Backup/restore differs:** pgvector inherits Postgres backup; Pinecone exports via API (slow >10M); Qdrant snapshots are fast. Plan DR before shipping.
3. **Cross-store migration is multi-week:** ~$6–18K of FDE time depending on scale.
4. **Don't fuse raw scores across stores:** use RRF.
5. **HNSW defaults are conservative:** for 10M-doc query-heavy, try `m=32`, `ef_construction=200`; re-tune per customer.

---

## 16. Quick-Fire Quiz Answers

| Q | Answer |
|---|---|
| Q1: Why pgvector wins despite being slower | **b)** Runs on existing Postgres; 5 constraints stack vs a 6 ms win at <10M docs, ~10 RPS |
| Q2: HNSW vs IVF | **b)** HNSW: better recall, more RAM, slower build (query-heavy). IVF: faster build, less RAM, slightly lower recall (ingest-heavy) |
| Q3: On-prem + audit-ready + runs Postgres | **c) pgvector** |
| Q4: pgvector → Qdrant migration, 1M docs | **b)** Multi-week: re-embed + dual-write + cutover + cleanup + 30-day rollback |
| Q5: Index rebuild on schema change | **b)** Real cost: minutes to hours of CPU + extra disk; plan like a migration |

---

## 17. Practice Exercises (Topics Only)

- **Easy:** pgvector hello-world: install, insert, query.
- **Easy:** HNSW vs IVF: build time and query latency on 10K rows.
- **Medium:** Qdrant in Docker: insert and benchmark vs pgvector.
- **Medium:** pgvector hybrid: vector + tsvector + RRF in SQL.
- **Hard:** Quantization: halfvec + scalar quantization, recall vs memory.
- **Medium:** Filtered search: tenant_id isolation, pre-filter vs post-filter.
- **Hard:** pgvector → Qdrant migration runbook (5 phases).
- **Graded:** 1-page store decision memo for AcmeCorp RAG over OCC bulletins (~5M chunks).

---

## 18. Cheat Sheet (Memorize These)

- **Pick by customer constraint, not benchmark.**
- **AcmeCorp default = pgvector** (existing Postgres + DBA + backups + access control + audit; zero new vendor).
- Pinecone ~12 ms vs pgvector ~18 ms: only ~6 ms; compare **end-to-end p95**, not index-only.
- **HNSW** = query-heavy (high recall, high RAM, slow build). **IVF** = ingest-heavy (fast build, low RAM).
- **Quantize first:** `halfvec` 2x, int8 4x, binary 32x; rescore to recover recall.
- **Filters can crash recall** (post-filter cliff). Use partial indexes / filterable HNSW; test with real filters.
- **Multi-tenancy:** row-level for the long tail, dedicated collection for whales/regulated.
- **Tombstones:** VACUUM on schedule, REINDEX at ~20%.
- **Sweep `ef_search` / `nprobe`** on your own corpus; stop at the first value that meets the recall SLO.
- **DiskANN** only past ~100M vectors.
- **Pinecone** = managed-first / zero ops / global. **Qdrant** = greenfield self-host. **Weaviate** = multi-modal. **Milvus** = 100M+.
- **Migration = multi-week:** re-embed, dual-write, gradual cutover, 30-day rollback. Fuse across stores with **RRF**.
