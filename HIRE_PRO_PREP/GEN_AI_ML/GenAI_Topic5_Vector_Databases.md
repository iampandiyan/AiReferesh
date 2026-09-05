# GenAI/AI-ML Principles — Topic 5: Vector Databases

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Every SQL statement below ran against a genuinely live PostgreSQL 16 + pgvector instance set up in this sandbox — not simulated, not FAISS standing in for pgvector. This matches your lab environment's actual technology exactly.

---

## 1. What Is a Vector Database?

A vector database stores embeddings (Topic 2) alongside the original content, and provides efficient **similarity search** — finding the k nearest vectors to a query vector — instead of exact-match lookups like a traditional database index. `pgvector` adds this capability directly inside PostgreSQL rather than requiring a separate specialized system.

---

## 2. Setting Up a Vector Column

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding VECTOR(4)   -- dimension must be fixed and declared upfront
);
```
Verified: table created successfully against the real instance. **MCQ-relevant point:** the vector dimension is fixed per column — you can't mix 384-dim and 1536-dim embeddings in the same column, which is why changing embedding models mid-project usually requires a schema migration, not just a data update.

**Inserting vectors (via psycopg2 + the `pgvector` Python adapter, matching your lab pattern):**
```python
import psycopg2
from pgvector.psycopg2 import register_vector

conn = psycopg2.connect(dbname="ragdemo", user="postgres", password="postgres", host="localhost")
register_vector(conn)
cur = conn.cursor()

docs = [
    ("RAG reduces hallucination via grounding", [0.9, 0.1, 0.2, 0.05]),
    ("Chunking splits documents for context windows", [0.85, 0.15, 0.25, 0.1]),
    ("The stock market fell sharply today", [0.05, 0.9, 0.1, 0.8]),
    ("Cosine similarity measures vector angle", [0.88, 0.12, 0.3, 0.08]),
]
for content, emb in docs:
    cur.execute("INSERT INTO documents (content, embedding) VALUES (%s, %s)", (content, emb))
conn.commit()
```
Verified: 4 rows inserted successfully.

---

## 3. The Three Distance Operators — All Verified Against Real Data

pgvector provides three operators, and picking the right one matters — they can produce genuinely different rankings.

**`<->` — L2 (Euclidean) distance:**
```sql
SELECT content, embedding <-> '[0.87,0.13,0.22,0.07]'::vector AS distance
FROM documents
ORDER BY distance
LIMIT 3;
```
Output:
```
distance=0.0510  ->  RAG reduces hallucination via grounding
distance=0.0510  ->  Chunking splits documents for context windows
distance=0.0819  ->  Cosine similarity measures vector angle
```

**`<=>` — cosine distance:**
```sql
SELECT content, embedding <=> '[0.87,0.13,0.22,0.07]'::vector AS cosine_distance
FROM documents
ORDER BY cosine_distance
LIMIT 3;
```
Output:
```
cosine_distance=0.0013  ->  RAG reduces hallucination via grounding
cosine_distance=0.0016  ->  Chunking splits documents for context windows
cosine_distance=0.0033  ->  Cosine similarity measures vector angle
```

**`<#>` — negative inner product:**
```sql
SELECT content, embedding <#> '[0.87,0.13,0.22,0.07]'::vector AS neg_inner_product
FROM documents
ORDER BY neg_inner_product
LIMIT 3;
```
Output:
```
neg_inner_product=-0.8528  ->  Cosine similarity measures vector angle
neg_inner_product=-0.8435  ->  RAG reduces hallucination via grounding
neg_inner_product=-0.8210  ->  Chunking splits documents for context windows
```
**Genuinely useful finding from this real run:** notice the inner-product ranking put "Cosine similarity measures vector angle" FIRST, while L2 and cosine distance both put "RAG reduces hallucination via grounding" first. This is real, not a contrived example — raw inner product is sensitive to vector magnitude (unlike cosine, which normalizes it away — see Topic 2, Section 3), so it can genuinely re-rank results differently. **This is exactly why the choice of operator must match how your embeddings were produced** — if your embedding model doesn't normalize its output vectors, using `<#>` instead of `<=>` can silently give you worse-ranked results.

---

## 4. HNSW Indexing — Verified Real Index Creation

**HNSW (Hierarchical Navigable Small World)** builds a multi-layer graph structure for fast approximate nearest-neighbor search — this is the index type behind your lab's confirmed ~35x speedup at 5,000 rows.

```sql
CREATE INDEX ON documents USING hnsw (embedding vector_l2_ops)
WITH (m = 16, ef_construction = 64);
```
Verified — real index created:
```
documents_embedding_idx -> CREATE INDEX documents_embedding_idx ON public.documents
USING hnsw (embedding vector_l2_ops) WITH (m='16', ef_construction='64')
```

| Parameter | Explanation |
|---|---|
| `m` | Max number of connections per node in the graph — higher = better recall, more memory/build time |
| `ef_construction` | Search depth used while building the index — higher = better quality index, slower to build |
| `vector_l2_ops` | Tells the index which distance operator (`<->`, `<=>`, or `<#>`) it should optimize for — must match the operator used in your queries |

---

## 5. IVFFlat Indexing — Verified Real Index Creation

**IVFFlat** clusters vectors into `lists` groups (via k-means), then at query time only searches the most relevant clusters — trading some accuracy for speed, similar to FAISS's `IndexIVFFlat` from Topic 2.

```sql
CREATE INDEX ON documents USING ivfflat (embedding vector_l2_ops)
WITH (lists = 2);
```
Verified: index created successfully (deliberately tiny `lists = 2` for this 4-row demo table — pgvector's own documentation recommends `lists = rows / 1000` for larger datasets, so a real production table would use a much higher value).

**HNSW vs IVFFlat — the practical trade-off:**
| | HNSW | IVFFlat |
|---|---|---|
| Build time | Slower | Faster |
| Query speed | Generally faster | Generally slower |
| Recall (accuracy) | Generally higher | Lower, tunable via `probes` |
| Best for | Read-heavy workloads, most modern RAG use cases | Faster to rebuild when data changes frequently |

---

## 6. The Most Important Real Result: Indexes Don't Always Get Used

```sql
EXPLAIN ANALYZE
SELECT content FROM documents ORDER BY embedding <-> '[0.87,0.13,0.22,0.07]'::vector LIMIT 3;
```
Actual output from the real instance (both HNSW and IVFFlat indexes existed on the table at this point):
```
Limit  (cost=1.09..1.10 rows=3 width=40) (actual time=0.027..0.028 rows=3 loops=1)
  ->  Sort  (cost=1.09..1.10 rows=4 width=40) (actual time=0.026..0.027 rows=3 loops=1)
        Sort Key: ((embedding <-> '[0.87,0.13,0.22,0.07]'::vector))
        Sort Method: quicksort  Memory: 25kB
        ->  Seq Scan on documents  (cost=0.00..1.05 rows=4 width=40) (actual time=0.004..0.005 rows=4 loops=1)
Planning Time: 0.168 ms
Execution Time: 0.037 ms
```
**This is a genuinely important, real result, not a contrived teaching point:** PostgreSQL's query planner chose a **Sequential Scan**, completely ignoring both vector indexes, because the table only has 4 rows — a full scan is cheaper than the index overhead at this tiny scale. This is a live demonstration of exactly why your lab's HNSW speedup was measured and confirmed at 5,000 rows, not on a handful of rows — **indexes have overhead that only pays off past a certain data size**, and `EXPLAIN ANALYZE` is the standard tool for verifying whether an index is actually being used in production, rather than assuming it is just because it exists.

---

## 7. FAISS vs pgvector — Practical Comparison

| | FAISS | pgvector |
|---|---|---|
| Nature | Standalone library, in-memory (or disk-backed with extra setup) | Postgres extension — vectors live alongside your relational data |
| Best for | Pure vector search at very large scale, maximum raw speed | Combining vector search with SQL filtering/joins on existing relational data |
| Persistence | Manual (save/load index files) | Automatic — it's just a Postgres table |
| Filtering by metadata | Requires separate bookkeeping | Native — a normal `WHERE` clause alongside the vector search |

**Your Lab 1.2 confirmed finding is directly relevant:** cross-encoder reranking produced identical scores across FAISS and pgvector — the choice of vector store affects retrieval speed/scalability, not the semantic quality of what's retrieved, since both are doing the same underlying similarity math.

---

## 8. Traps & Misconceptions (MCQ-Relevant)

1. **"Creating a vector index always speeds up every query"** — FALSE, as Section 6 directly proves. On small tables, the planner may skip the index entirely because a sequential scan is cheaper.
2. **"HNSW and IVFFlat give identical results"** — FALSE. Both are *approximate* nearest-neighbor methods — they can miss the true nearest neighbor in exchange for speed, unlike an exact brute-force scan.
3. **"`<#>` and `<=>` always rank results the same way"** — FALSE, as Section 3's real query results show — inner product is magnitude-sensitive, cosine distance is not.
4. **"You can just add an HNSW index to speed up any vector column"** — Not quite — the `vector_l2_ops`/`vector_cosine_ops`/`vector_ip_ops` operator class must match the distance operator you actually use in queries, or the index won't be usable for that query.
5. **"pgvector and FAISS are interchangeable, pick whichever"** — Not accurate for every case — if you need to combine vector search with relational filtering (e.g., "find similar documents uploaded by this user last month"), pgvector's native SQL integration is a real practical advantage FAISS doesn't have without extra engineering.

---

## 9. Rapid-Fire Self-Check (MCQ Simulation)

1. Why might PostgreSQL's query planner ignore a vector index and use a sequential scan instead? *(On small tables, sequential scan is cheaper than the index overhead — the planner chooses based on cost estimates, not blindly using any index that exists)*
2. What does the `m` parameter control in an HNSW index? *(Max connections per node in the graph — trades memory/build time for recall)*
3. Why did `<#>` (inner product) produce a different top result than `<->` and `<=>` in the verified example? *(Inner product is sensitive to vector magnitude, unlike cosine distance which normalizes it away)*
4. What's the standard tool for verifying whether a vector index is actually being used by a query? *(`EXPLAIN ANALYZE`)*
5. Name one practical advantage of pgvector over FAISS for a real application. *(Native SQL integration — can combine vector similarity search with relational filtering/joins in one query, without separate bookkeeping)*

---

## Status
Every SQL statement, index creation, and query plan in this document was executed against a real, live PostgreSQL 16 + pgvector 0.6.0 instance set up specifically for this verification — not FAISS standing in for pgvector, and not invented output. The sequential-scan finding in Section 6 was not anticipated going in; it emerged from actually running `EXPLAIN ANALYZE` and turned out to be one of the most instructive results in this whole topic.

Ready for the companion **Cheatsheet — Topic 5** or straight into **Topic 6: Agentic AI & Orchestration** whenever you want to continue.
