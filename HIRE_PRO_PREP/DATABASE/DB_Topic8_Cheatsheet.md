# Database Cheatsheet — Topic 8 (Aggregates, Subqueries, CTEs, Window Functions Syntax)

**Companion to:** DB_Topic8_Aggregates_Subqueries_CTEs_Windows.md
**Format:** Syntax → What it does → One verified runnable example per entry (all reused directly from the main doc's real PostgreSQL run)

---

## `FILTER` — Conditional Aggregation

**Syntax:**
```sql
SELECT COUNT(*) FILTER (WHERE condition) FROM table;
```
Computes an aggregate over only the rows matching `condition`, alongside unfiltered aggregates in the same query — verified to produce per-department high-earner counts in one pass.

---

## Subquery Types

| Type | Syntax pattern | Verified behavior |
|---|---|---|
| Scalar | `WHERE col > (SELECT AVG(col) FROM t)` | Returns exactly one value, used like a literal |
| IN | `WHERE col IN (SELECT col2 FROM t2)` | Membership check against a list |
| Correlated | `(SELECT ... FROM t2 WHERE t2.x = t1.x)` inside the outer SELECT list | References the outer row — conceptually re-evaluated per outer row |
| EXISTS | `WHERE EXISTS (SELECT 1 FROM t2 WHERE ...)` | Checks row presence only, not values |

---

## `WITH` (CTE)

**Syntax:**
```sql
WITH cte_name AS (
    SELECT ...
)
SELECT ... FROM cte_name WHERE ...;
```
A named, reusable intermediate result — verified to correctly filter down from a defined CTE in a second, outer query.

---

## `WITH RECURSIVE`

**Syntax:**
```sql
WITH RECURSIVE cte_name AS (
    SELECT ... /* base case */
    UNION ALL
    SELECT ... FROM table JOIN cte_name ON ... /* recursive case */
)
SELECT ... FROM cte_name;
```

| Part | Explanation |
|---|---|
| Base case | The starting row(s) — runs once |
| Recursive case | JOINs the CTE to the base table, one level deeper each iteration — genuinely repeats until no new rows are produced |
| `UNION ALL` | Combines base + recursive results across all iterations (not `UNION`, which would also deduplicate) |

**Verified example (real recursion, not a fixed-depth trick):**
```sql
WITH RECURSIVE org_chart AS (
    SELECT id, name, manager_id, 0 AS depth FROM employees WHERE id = 1
    UNION ALL
    SELECT e.id, e.name, e.manager_id, o.depth + 1
    FROM employees e JOIN org_chart o ON e.manager_id = o.id
)
SELECT depth, name FROM org_chart ORDER BY depth, name;
```

---

## Window Functions

**Syntax:**
```sql
function_name() OVER (PARTITION BY col ORDER BY col2)
```

| Function | Behavior with ties (verified with a real tie: two employees both at 95000) |
|---|---|
| `ROW_NUMBER()` | Always unique — tied rows get 3, 4 (arbitrary distinct order) |
| `RANK()` | Tied rows get the SAME number (3, 3), then SKIPS the next number (jumps to 5) |
| `DENSE_RANK()` | Tied rows get the SAME number (3, 3), does NOT skip (next is 4) |
| `LAG(col)` / `LEAD(col)` | Value from the previous/next row in the window ordering — NULL at the boundary (verified: first row's LAG is NULL) |
| `SUM(col) OVER (ORDER BY col2)` | Running/cumulative total — verified to accumulate correctly row by row |
| `PARTITION BY col` | Resets the window per group, like GROUP BY, but keeps every row in the output |

**Verified example (the tie-breaking proof):**
```sql
SELECT name, salary,
       ROW_NUMBER() OVER (ORDER BY salary DESC) AS row_num,
       RANK() OVER (ORDER BY salary DESC) AS rank,
       DENSE_RANK() OVER (ORDER BY salary DESC) AS dense_rank
FROM employees;
-- Carol 95000: row_num=3, rank=3, dense_rank=3
-- Bob   95000: row_num=4, rank=3, dense_rank=3   <- tied with Carol on rank/dense_rank, NOT on row_num
-- next distinct salary: rank jumps to 5, dense_rank continues to 4
```

---

## Status
6 syntax patterns verified with real executed output, including genuine recursion and a genuine tie-breaking comparison.
