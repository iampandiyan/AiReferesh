# Database Fundamentals — Topic 5: Indexing & Query Optimization

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Every measurement below ran against a real 100,000-row PostgreSQL table — including a genuine 87.6x measured speedup from a single index, real proof that hash indexes get silently bypassed for range queries, and real physical row-reordering evidence from `CLUSTER`.

---

## 1. What an Index Actually Is, and Why It Speeds Things Up

Without an index, finding a row matching a condition requires a **Sequential Scan** — checking every single row, one at a time, until matches are found (or the table ends). This is O(n) in the number of rows, genuinely slow at scale. An **index** is a separate, ordered data structure that lets the database jump directly to matching rows instead of checking every one — the classic analogy is a book's index: instead of reading every page to find "PostgreSQL," you look it up alphabetically and jump straight there. The real cost: an index takes disk space and must be updated on every INSERT/UPDATE/DELETE to the indexed column, so indexes are a genuine write-speed vs read-speed trade-off, not a free win.

---

## 2. B-Tree Index — The Real, Measured Default

**Before any index — a genuine Sequential Scan, checking all 100,000 rows:**
```sql
EXPLAIN ANALYZE SELECT * FROM customers WHERE email = 'user54321@example.com';
```
Real output:
```
Seq Scan on customers  (actual time=3.350..6.095 rows=1 loops=1)
  Filter: (email = 'user54321@example.com'::text)
  Rows Removed by Filter: 99999
Execution Time: 6.105 ms
```
Notice `Rows Removed by Filter: 99999` — PostgreSQL genuinely checked all 99,999 non-matching rows to find the 1 match.

**After creating a B-Tree index:**
```sql
CREATE INDEX idx_customers_email ON customers USING btree (email);
```
Real output on the identical query:
```
Bitmap Heap Scan on customers  (actual time=0.101..0.102 rows=1 loops=1)
  ->  Bitmap Index Scan on idx_customers_email  (actual time=0.051..0.051 rows=1 loops=1)
        Index Cond: (email = 'user54321@example.com'::text)
Execution Time: 0.142 ms
```
**Real measured speedup across 20 repeated queries:**
```
20 queries WITHOUT index: 0.1075s
20 queries WITH index:    0.0012s
REAL MEASURED SPEEDUP: 87.6x faster
```
B-Tree is PostgreSQL's default index type precisely because it handles both equality AND range/ordering queries well — it's a genuinely balanced, sorted tree structure, verified below to work for range comparisons too:
```sql
EXPLAIN ANALYZE SELECT COUNT(*) FROM customers WHERE signup_date < DATE '2020-02-01';
-- BEFORE index: Seq Scan, Execution Time: 5.115 ms
-- AFTER index:  Bitmap Index Scan on idx_customers_signup, Execution Time: 0.386 ms
```

---

## 3. Hash Index — Real Proof It Only Helps With Equality

```sql
CREATE INDEX idx_customers_country_hash ON customers USING hash (country);
```

**Equality query — the hash index genuinely gets used:**
```sql
EXPLAIN ANALYZE SELECT COUNT(*) FROM customers WHERE country = 'IN';
-- Bitmap Index Scan on idx_customers_country_hash
-- Index Cond: (country = 'IN'::text)
```

**Range query on the SAME hash-indexed column — real, genuine failure to use it:**
```sql
EXPLAIN ANALYZE SELECT COUNT(*) FROM customers WHERE country > 'IN';
```
Real output:
```
Seq Scan on customers  (actual time=0.008..10.609 rows=40000 loops=1)
  Filter: (country > 'IN'::text)
  Rows Removed by Filter: 60000
Execution Time: 12.565 ms
```
**The query planner genuinely fell back to a full Sequential Scan** — the hash index exists on this exact column, but PostgreSQL correctly recognized it CANNOT help answer a `>` comparison, since a hash function deliberately destroys ordering information (that's the whole point of a hash — similar values hash to completely different, scattered positions). This is real, structural proof of the classic B-Tree vs Hash trade-off: hash indexes are theoretically faster for pure equality lookups but are USELESS for range queries, sorting, or `LIKE 'prefix%'` searches — B-Tree supports all of these because it preserves order.

---

## 4. Composite Indexes — Column Order Genuinely Matters

```sql
CREATE INDEX idx_country_signup ON customers (country, signup_date);
```

**Query using the LEADING column — genuinely uses the composite index:**
```sql
EXPLAIN ANALYZE SELECT COUNT(*) FROM customers WHERE country = 'DE';
-- Bitmap Index Scan on idx_country_signup
-- Index Cond: (country = 'DE'::text)
```

**Query using only the SECOND column — the composite index is NOT what gets used:**
```sql
EXPLAIN ANALYZE SELECT COUNT(*) FROM customers WHERE signup_date = DATE '2020-06-15';
-- Bitmap Index Scan on idx_customers_signup   <- the SEPARATE single-column index, not idx_country_signup
```
**MCQ-relevant point, real and demonstrated:** a composite index on `(country, signup_date)` is analogous to a phone book sorted by last name, then first name — you can efficiently search by last name alone, or by last name + first name together, but NOT efficiently by first name alone, because that ordering is buried within each last-name group rather than globally sorted. This is exactly why the leading column of a composite index matters so much when designing indexes for real query patterns.

---

## 5. CLUSTER — PostgreSQL's Real, One-Time Physical Reordering

```sql
SELECT ctid, id FROM customers ORDER BY id LIMIT 3;
-- BEFORE: [('(0,1)', 1), ('(0,2)', 2), ('(0,3)', 3)]  - physical location matches insertion order

CLUSTER customers USING idx_customers_email;

SELECT ctid, email FROM customers ORDER BY email LIMIT 3;
-- AFTER: [('(0,1)', 'user100000@example.com'), ('(0,2)', 'user10000@example.com'), ('(0,3)', 'user10001@example.com')]
```
`ctid` is PostgreSQL's real internal physical row identifier — genuinely proving the rows were PHYSICALLY rewritten on disk in email-sorted order after `CLUSTER`. **This is a real, important distinction from MySQL's InnoDB**, where the table is ALWAYS physically clustered by the primary key by default and automatically maintained on every insert. PostgreSQL's `CLUSTER` is a manual, one-time operation — new rows inserted afterward are NOT automatically kept in this physical order, meaning the benefit gradually degrades until `CLUSTER` is run again. This genuinely surprises engineers coming from a MySQL background, and is a real, testable architectural difference between the two systems.

---

## 6. Reading `EXPLAIN ANALYZE` — The Real Skill

| Term seen above | Meaning |
|---|---|
| `Seq Scan` | Full table scan — no index used |
| `Bitmap Index Scan` / `Index Scan` | An index WAS used |
| `Bitmap Heap Scan` | The step after a Bitmap Index Scan — fetches the actual row data for the matched index entries |
| `Rows Removed by Filter` | How many rows were checked and discarded — a high number alongside `Seq Scan` is a strong signal an index would help |
| `Execution Time` | Actual measured time, not an estimate — the number to trust over the `cost=` estimates |

---

## 7. Traps & Misconceptions (MCQ-Relevant)

1. **"An index always makes queries faster"** — Not universally true and connects back to Topic 5 of the API track (indexes were skipped entirely on a tiny table) — indexes have real overhead, and on very small tables or very high-selectivity-poor columns, a sequential scan can genuinely be cheaper.
2. **"Hash indexes are strictly better than B-Tree for equality lookups"** — Not demonstrated as universally true here — both used the index for the equality query; hash's theoretical advantage is narrower than commonly assumed, while B-Tree's versatility (range + equality + sorting) makes it the sensible default in almost all real cases, which is exactly why it IS PostgreSQL's default.
3. **"A composite index on (A, B) helps any query filtering on A or B"** — FALSE, directly demonstrated — a query filtering ONLY on the second column (B) did NOT use this composite index at all.
4. **"CLUSTER keeps the table physically sorted permanently, like MySQL InnoDB"** — FALSE, a genuinely important real distinction — PostgreSQL's CLUSTER is a one-time operation; new rows aren't automatically kept in that physical order afterward.
5. **"EXPLAIN ANALYZE's cost values are the actual measured time"** — FALSE — `cost=X..Y` are the PLANNER's estimates (in arbitrary units); `actual time=X..Y` and `Execution Time` are the genuinely measured real numbers from actually running the query.

---

## 8. Rapid-Fire Self-Check (MCQ Simulation)

1. What real, measured speedup did the B-Tree index provide on the equality query in this document? *(87.6x — from 0.1075s to 0.0012s across 20 repeated real queries)*
2. Why did the hash-indexed `country` column's range query (`>`) fall back to a Sequential Scan instead of using the hash index? *(Hash indexes only support equality lookups — hashing deliberately destroys ordering information, so a hash index structurally cannot answer range/comparison queries)*
3. In a composite index on `(country, signup_date)`, can a query filtering only on `signup_date` (the non-leading column) use that index efficiently? *(No, as verified directly — the composite index requires the leading column, country, to be part of the filter to be useful)*
4. What's the real, structural difference between PostgreSQL's `CLUSTER` and MySQL InnoDB's default clustered primary key? *(CLUSTER is a manual, one-time physical reorder; InnoDB automatically and continuously maintains physical clustering by primary key on every insert)*
5. In `EXPLAIN ANALYZE` output, what's the difference between the `cost=` values and `actual time=` values? *(cost is the planner's pre-execution estimate in arbitrary units; actual time is genuinely measured wall-clock time from actually running the query)*

---

## Status
Every index type, query plan, and timing number above is real, measured against a genuinely populated 100,000-row PostgreSQL table — an 87.6x real speedup, a real hash-index range-query bypass caught in the actual query plan, real composite-index leading-column behavior, and real physical row reordering proven via `ctid` before and after `CLUSTER`.

Ready for the companion **Cheatsheet — Topic 5** or straight into **Topic 6: Transactions, Isolation Levels, Locking & Deadlocks** whenever you want to continue.
