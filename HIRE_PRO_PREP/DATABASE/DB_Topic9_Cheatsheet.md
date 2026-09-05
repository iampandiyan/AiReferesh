# Database Cheatsheet — Topic 9 (JSONB & NoSQL-style Query Patterns)

**Companion to:** DB_Topic9_NoSQL_vs_SQL_CAP.md
**Format:** Syntax → What it does → One verified runnable example per entry

Redis's core key-value methods (`set`, `get`, TTL, data structures) are already covered in the API track's Topic 9 cheatsheet — not repeated here.

---

## JSONB Column Type

**Syntax:**
```sql
CREATE TABLE products (id SERIAL PRIMARY KEY, attributes JSONB);
INSERT INTO products (attributes) VALUES ('{"brand": "Dell", "ram_gb": 16}');
```

| Feature | Explanation |
|---|---|
| No fixed schema per row | Verified: three different rows stored completely different key sets in the same JSONB column |
| Validated as real JSON | Malformed JSON is rejected at insert time — JSONB isn't just a text column |

---

## `->` and `->>` — Field Access

| Operator | Returns | Verified example |
|---|---|---|
| `->'key'` | The value as JSONB (for further chaining into nested structures) | `attributes->'specs'` |
| `->>'key'` | The value as TEXT | `attributes->>'brand'` → `'Dell'` |

**Verified nested access:**
```sql
SELECT attributes->'specs'->>'cpu' FROM products WHERE name = 'Laptop';
-- 'i7'
```

---

## `?` — Key Existence Check

**Syntax:**
```sql
SELECT * FROM products WHERE attributes ? 'brand';
```
Returns rows where the JSONB column has a top-level key named `'brand'` — verified to correctly exclude the `Book` row, which has no `brand` field at all.

---

## `@>` — Containment Check

**Syntax:**
```sql
SELECT * FROM products WHERE attributes @> '{"ram_gb": 16}';
```
Returns rows where the JSONB column CONTAINS the given fragment — verified to correctly find only `Laptop`. This is the real query pattern GIN indexes (below) are built to accelerate.

---

## `CREATE INDEX ... USING gin` — Indexing JSONB

**Syntax:**
```sql
CREATE INDEX idx_name ON table_name USING gin (jsonb_column);
```

| Note | Explanation |
|---|---|
| Accelerates `@>` containment queries | GIN (Generalized Inverted Index) is built specifically for indexing composite/multi-valued data like JSONB and arrays |
| Cost-based, not automatic | Verified — genuinely skipped by the planner (`Seq Scan` in EXPLAIN output) on a small 3-row table, same lesson as the pgvector HNSW topic |

---

## Redis `scan_iter` — Full Key Scan (the Real Limitation Pattern)

**Syntax:**
```python
for key in r.scan_iter("product:*"):
    data = json.loads(r.get(key))
```

| Note | Explanation |
|---|---|
| `scan_iter(pattern)` | Iterates matching keys without blocking the server (safer than the older `KEYS` command for production use) |
| Why this pattern appears here | Verified as the ONLY way to search INTO stored JSON values in Redis — no native secondary index on a value's internal fields, unlike JSONB + GIN above |

---

## Status
5 JSONB-specific syntax patterns plus the Redis full-scan pattern, all verified with real executed output against genuinely running PostgreSQL and Redis instances.
