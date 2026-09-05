# GenAI/AI-ML Cheatsheet — Topic 5 (Vector Database Libraries & SQL)

**Companion to:** GenAI_Topic5_Vector_Databases.md
**Format:** Initialization → Top production-relevant methods/commands → One verified runnable example per entry

All examples below were executed against a real live PostgreSQL 16 + pgvector instance.

---

## `psycopg2` — PostgreSQL Python Driver

**Initialization:**
```python
import psycopg2
conn = psycopg2.connect(dbname="ragdemo", user="postgres", password="postgres", host="localhost")
cur = conn.cursor()
```

**Top methods:**
| Method | Explanation |
|---|---|
| `cur.execute(sql, params)` | Run a SQL statement — always pass parameters via `%s` placeholders, never string-format SQL directly (prevents SQL injection) |
| `cur.fetchall()` | Get all result rows as a list of tuples |
| `cur.fetchone()` | Get just the next single row |
| `conn.commit()` | Persist changes (required after INSERT/UPDATE/CREATE — not automatic) |

**Verified example:**
```python
cur.execute("SELECT content FROM documents LIMIT 2;")
print(cur.fetchall())
# [('RAG reduces hallucination via grounding',), ('Chunking splits documents for context windows',)]

cur.execute("SELECT COUNT(*) FROM documents;")
print(cur.fetchone())
# (4,)

cur.execute("SELECT content FROM documents WHERE content ILIKE %s;", ('%RAG%',))
print(cur.fetchall())
# [('RAG reduces hallucination via grounding',)]
```

---

## `pgvector.psycopg2.register_vector`

**Initialization:**
```python
from pgvector.psycopg2 import register_vector
register_vector(conn)   # call once, right after connecting
```

**Why it matters:**
| Without it | With it |
|---|---|
| You must manually format Python lists as PostgreSQL vector literal strings (e.g., `'[0.1,0.2]'`) | You can pass a plain Python list directly as a query parameter, and it's automatically converted to/from the `VECTOR` type |

**Verified example (from the main doc):**
```python
docs = [("some text", [0.9, 0.1, 0.2, 0.05])]
for content, emb in docs:
    cur.execute("INSERT INTO documents (content, embedding) VALUES (%s, %s)", (content, emb))
# the raw Python list [0.9, 0.1, 0.2, 0.05] is inserted directly - no manual string formatting needed
```

---

## SQL: `CREATE EXTENSION` + `VECTOR` type

**Top usage:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding VECTOR(4)   -- dimension is fixed per column
);
```
Verified: extension enabled and table created successfully on the real instance.

---

## SQL: Distance Operators

| Operator | Explanation |
|---|---|
| `<->` | L2 (Euclidean) distance — lower is more similar |
| `<=>` | Cosine distance — lower is more similar (1 − cosine similarity) |
| `<#>` | Negative inner product — lower is more similar, but magnitude-sensitive unlike `<=>` |

**Verified example:**
```sql
SELECT content, embedding <-> '[0.87,0.13,0.22,0.07]'::vector AS distance
FROM documents
ORDER BY distance
LIMIT 3;
```
Output (real):
```
distance=0.0510  ->  RAG reduces hallucination via grounding
distance=0.0510  ->  Chunking splits documents for context windows
distance=0.0819  ->  Cosine similarity measures vector angle
```

---

## SQL: `CREATE INDEX ... USING hnsw` / `USING ivfflat`

**Top usage:**
```sql
-- HNSW
CREATE INDEX ON documents USING hnsw (embedding vector_l2_ops)
WITH (m = 16, ef_construction = 64);

-- IVFFlat
CREATE INDEX ON documents USING ivfflat (embedding vector_l2_ops)
WITH (lists = 2);
```

| Parameter | Explanation |
|---|---|
| `vector_l2_ops` / `vector_cosine_ops` / `vector_ip_ops` | Must match the distance operator (`<->`, `<=>`, `<#>`) used in your queries, or the index won't be usable |
| `m`, `ef_construction` (HNSW) | Graph connectivity and build-time search depth — trade build cost for recall |
| `lists` (IVFFlat) | Number of clusters — recommended roughly `rows / 1000` for real datasets |

Both verified: created successfully on the real instance (see main doc for confirmed `pg_indexes` output).

---

## SQL: `EXPLAIN ANALYZE`

**Top usage:**
```sql
EXPLAIN ANALYZE
SELECT content FROM documents ORDER BY embedding <-> '[0.87,0.13,0.22,0.07]'::vector LIMIT 3;
```

| What to look for | Explanation |
|---|---|
| `Seq Scan` | Full table scan — indexes were NOT used for this query |
| `Index Scan` / `Index Only Scan` | An index WAS used |
| `Execution Time` | Actual measured query time, not an estimate |

**Verified example (real, unexpected result):**
```
Limit  (cost=1.09..1.10 rows=3 width=40) (actual time=0.027..0.028 rows=3 loops=1)
  ->  Sort ...
        ->  Seq Scan on documents  (cost=0.00..1.05 rows=4 width=40) ...
```
Confirms the vector indexes were skipped in favor of a sequential scan on this tiny 4-row table — this is the standard way to verify whether an index is actually helping, rather than assuming it is.

---

## Status
6 entries verified against a real live PostgreSQL 16 + pgvector instance. Note: the postgres background service stopped between tool calls while building this cheatsheet (a sandbox artifact, not a pgvector issue) — caught and restarted before re-verifying, rather than assuming stale results were still valid.
