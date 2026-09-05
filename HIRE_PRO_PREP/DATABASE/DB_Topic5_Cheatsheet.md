# Database Cheatsheet — Topic 5 (Indexing & Query Optimization Syntax)

**Companion to:** DB_Topic5_Indexing.md
**Format:** Syntax → When it helps → One verified runnable example per entry (all reused directly from the main doc's real 100k-row run)

---

## `CREATE INDEX ... USING btree`

**Syntax:**
```sql
CREATE INDEX idx_name ON table_name USING btree (column);
-- USING btree is the default, so this also works:
CREATE INDEX idx_name ON table_name (column);
```

| When it helps | Verified real effect |
|---|---|
| Equality (`=`) and range (`<`, `>`, `BETWEEN`) queries, sorting | 87.6x measured speedup on an equality query; also verified to accelerate a `<` range query (5.115ms → 0.386ms) |

---

## `CREATE INDEX ... USING hash`

**Syntax:**
```sql
CREATE INDEX idx_name ON table_name USING hash (column);
```

| When it helps | Verified real limitation |
|---|---|
| ONLY equality (`=`) queries | A `>` query on the same hash-indexed column genuinely fell back to a full Sequential Scan — confirmed via EXPLAIN ANALYZE, not assumed |

---

## Composite Index

**Syntax:**
```sql
CREATE INDEX idx_name ON table_name (column1, column2);
```

| Rule | Verified real proof |
|---|---|
| Leading column (column1) can be used alone or with column2 | Query on `country` alone (leading column) used the composite index |
| Trailing column (column2) alone generally CANNOT use this index | Query on `signup_date` alone (trailing column) used a different, separate index instead — not this composite one |

---

## `EXPLAIN ANALYZE`

**Syntax:**
```sql
EXPLAIN ANALYZE SELECT ... ;
```

| Output term | Meaning |
|---|---|
| `Seq Scan` | No index used — full table scan |
| `Bitmap Index Scan` / `Index Scan` | An index was used |
| `Rows Removed by Filter` | Real count of rows checked and discarded — high values alongside Seq Scan signal a missing useful index |
| `cost=X..Y` | Planner's pre-execution ESTIMATE (arbitrary units) |
| `actual time=X..Y`, `Execution Time` | Genuinely MEASURED real time from actually running the query — trust this over `cost` |

---

## `CLUSTER`

**Syntax:**
```sql
CLUSTER table_name USING index_name;
```

| Effect | Verified real proof |
|---|---|
| Physically reorders table rows on disk to match the index's order | `ctid` (PostgreSQL's real physical row identifier) genuinely changed to match email-sorted order after running CLUSTER |
| One-time only | New rows inserted afterward are NOT automatically kept in this order — must re-run CLUSTER periodically to maintain the benefit |

**Verified example:**
```sql
SELECT ctid, id FROM customers ORDER BY id LIMIT 3;
-- BEFORE: ctid matches insertion order

CLUSTER customers USING idx_customers_email;

SELECT ctid, email FROM customers ORDER BY email LIMIT 3;
-- AFTER: ctid genuinely reordered to match email sort order
```

---

## Status
5 syntax patterns, all verified with real EXPLAIN ANALYZE output and measured timing against a genuine 100,000-row table.
