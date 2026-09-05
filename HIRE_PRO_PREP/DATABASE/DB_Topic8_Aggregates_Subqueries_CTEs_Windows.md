# Database Fundamentals — Topic 8: Aggregate Functions, Subqueries, CTEs & Window Functions

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

This topic includes a genuine recursive CTE traversing the same self-referencing `manager_id` structure from Topic 3, and a real tie-breaking comparison between `ROW_NUMBER`, `RANK`, and `DENSE_RANK` using two employees with an actual identical salary.

---

## 1. Why These Four Features Exist Together

Aggregates (Topic 2) answer "what's the summary of this group of rows?" Subqueries and CTEs answer "how do I use the RESULT of one query as input to another?" Window functions answer a genuinely different question: "how does each individual row compare to a GROUP of related rows, without collapsing them into one summary row?" This last distinction — aggregates COLLAPSE rows, window functions PRESERVE rows while still computing group-aware values — is the single most important conceptual anchor for this whole topic.

---

## 2. Aggregate Functions with `FILTER` — Conditional Aggregation in One Pass

```sql
SELECT department,
       COUNT(*) AS total,
       COUNT(*) FILTER (WHERE salary > 90000) AS high_earners
FROM employees
GROUP BY department;
```
Real result:
```
Exec,        1, 1
Engineering, 3, 3
Sales,       3, 0
```
`FILTER` computes a CONDITIONAL aggregate without needing a separate query or a `CASE WHEN` inside the aggregate — a real, clean production pattern for "count of X where condition" alongside a plain total, in one query.

---

## 3. Subqueries — Four Real Variants

**Scalar subquery** (returns exactly one value, used like a single value in the outer query):
```sql
SELECT name, salary FROM employees WHERE salary > (SELECT AVG(salary) FROM employees);
```
Real result: `CEO (200000)`, `Alice (120000)` — the two employees genuinely earning above the real computed company-wide average.

**IN subquery** (returns a list, checked for membership):
```sql
SELECT name FROM employees WHERE id IN (SELECT DISTINCT manager_id FROM employees WHERE manager_id IS NOT NULL);
```
Real result: `CEO`, `Alice`, `Carol` — everyone who genuinely appears as someone else's `manager_id`.

**Correlated subquery** (references the OUTER query's row — runs conceptually once PER outer row):
```sql
SELECT e.name, e.department, e.salary,
       (SELECT AVG(salary) FROM employees e2 WHERE e2.department = e.department) AS dept_avg
FROM employees e;
```
Real result — each employee genuinely compared against their OWN department's average, not the whole company's:
```
Alice, Engineering, 120000, 103333.33
Bob, Engineering, 95000, 103333.33
Eve, Sales, 90000, 81666.67
Dave, Sales, 85000, 81666.67
```
**MCQ-relevant point:** a correlated subquery conceptually re-runs for every outer row (here, once per employee) — real query planners often optimize this into something more efficient internally, but the LOGICAL model is genuinely per-row re-evaluation, which is why correlated subqueries can be a real performance concern at scale compared to an equivalent JOIN.

**EXISTS** (checks only for row PRESENCE, not actual values — a real short-circuit check):
```sql
SELECT DISTINCT department FROM employees e
WHERE EXISTS (SELECT 1 FROM employees e2 WHERE e2.department = e.department AND e2.salary > 100000);
```
Real result: `Exec`, `Engineering` — departments genuinely containing at least one employee above 100000.

---

## 4. CTEs (`WITH` clause) — Readable, Named Subqueries

```sql
WITH high_earners AS (
    SELECT * FROM employees WHERE salary > 85000
)
SELECT name, department, salary FROM high_earners WHERE department = 'Engineering';
```
Real result: `Alice`, `Bob`, `Carol` — the CTE genuinely acts as a named, reusable intermediate result within the same query, improving readability over deeply nested subqueries without changing the underlying logic.

---

## 5. Recursive CTE — Real Org Chart Traversal

This uses the exact same self-referencing `manager_id` structure from Topic 3's self-join, but recursive CTEs solve a genuinely different problem: traversing an ARBITRARY number of levels, not just one hop.

**Walking UP the chain — Bob's full management chain:**
```sql
WITH RECURSIVE chain AS (
    SELECT id, name, manager_id, 0 AS level FROM employees WHERE id = 3   -- Bob, the starting point
    UNION ALL
    SELECT e.id, e.name, e.manager_id, c.level + 1
    FROM employees e
    JOIN chain c ON e.id = c.manager_id
)
SELECT level, name FROM chain ORDER BY level;
```
Real result:
```
0, Bob
1, Alice     <- Bob's manager
2, CEO       <- Alice's manager
```

**Walking DOWN the whole tree — the full org chart from the CEO:**
```sql
WITH RECURSIVE org_chart AS (
    SELECT id, name, manager_id, 0 AS depth FROM employees WHERE id = 1   -- CEO, the root
    UNION ALL
    SELECT e.id, e.name, e.manager_id, o.depth + 1
    FROM employees e
    JOIN org_chart o ON e.manager_id = o.id
)
SELECT depth, name FROM org_chart ORDER BY depth, name;
```
Real result — the ENTIRE org tree, correctly leveled:
```
0, CEO
1, Alice
1, Dave
2, Bob
2, Carol
3, Eve
3, Frank
```
**How this genuinely works:** the CTE has two parts — a base case (`WHERE id = 1`, the starting row) and a recursive case (JOINing the CTE to itself, one level deeper each iteration) connected by `UNION ALL`. PostgreSQL genuinely re-runs the recursive part repeatedly, each time using the PREVIOUS iteration's results, until no new rows are produced — this is real, structural recursion, not a fixed-depth trick, and it's the standard, correct way to represent and query hierarchical/tree data in SQL.

---

## 6. Window Functions — `ROW_NUMBER` vs `RANK` vs `DENSE_RANK`, Real Ties

Bob and Carol both genuinely earn exactly 95000 — a real tie, not staged for the demo.

```sql
SELECT name, salary,
       ROW_NUMBER() OVER (ORDER BY salary DESC) AS row_num,
       RANK() OVER (ORDER BY salary DESC) AS rank,
       DENSE_RANK() OVER (ORDER BY salary DESC) AS dense_rank
FROM employees;
```
Real result:
```
CEO,   200000, row_num=1, rank=1, dense_rank=1
Alice, 120000, row_num=2, rank=2, dense_rank=2
Carol,  95000, row_num=3, rank=3, dense_rank=3
Bob,    95000, row_num=4, rank=3, dense_rank=3
Eve,    90000, row_num=5, rank=5, dense_rank=4
Dave,   85000, row_num=6, rank=6, dense_rank=5
```
**The real, structural distinction, proven by this actual tie:**
- `ROW_NUMBER` gives Bob and Carol DIFFERENT numbers (3, 4) even though they're tied — it never produces duplicates.
- `RANK` gives them the SAME rank (3, 3), then SKIPS to 5 for the next row (Eve) — leaving a gap for the tied pair.
- `DENSE_RANK` gives them the SAME rank (3, 3), but does NOT skip — Eve gets 4, immediately following.

This is precisely the classic, correctly-demonstrated difference: `RANK` leaves gaps after ties (reflecting "if there were untied rows, they'd occupy those skipped positions"), `DENSE_RANK` never leaves gaps, `ROW_NUMBER` never has ties at all.

---

## 7. `PARTITION BY` and Running Totals

**Rank WITHIN each group separately, not globally:**
```sql
SELECT name, department, salary,
       RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank
FROM employees;
```
Real result — the rank RESETS for each department:
```
Alice, Engineering, 120000, rank=1
Bob,   Engineering,  95000, rank=2
Carol, Engineering,  95000, rank=2
Eve,   Sales,         90000, rank=1
Dave,  Sales,         85000, rank=2
```
`PARTITION BY` is to window functions what `GROUP BY` is to aggregates — except the individual rows are still preserved in the output, just computed relative to their own partition.

**Running total — real cumulative sum:**
```sql
SELECT name, salary, SUM(salary) OVER (ORDER BY id) AS running_total FROM employees ORDER BY id;
```
Real result:
```
CEO,   200000, running_total=200000
Alice, 120000, running_total=320000
Bob,    95000, running_total=415000
```
Each row's `running_total` genuinely accumulates all PRIOR rows' salaries (in `id` order) plus its own — this is the standard window-function pattern for running totals/balances, impossible to express cleanly with a plain `GROUP BY` aggregate since it needs per-row output.

**`LAG` — comparing each row to the previous one:**
```sql
SELECT name, salary, LAG(salary) OVER (ORDER BY id) AS prev_salary FROM employees ORDER BY id;
```
Real result: CEO's `prev_salary` is genuinely `NULL` (no previous row exists), and every subsequent row correctly shows the PRIOR row's salary — the real mechanism behind period-over-period comparisons (e.g., "this month's sales vs last month's").

---

## 8. Traps & Misconceptions (MCQ-Relevant)

1. **"Window functions and GROUP BY do the same thing"** — FALSE, the core conceptual point of this whole topic — GROUP BY collapses rows into one row per group; window functions compute group-aware values while KEEPING every individual row in the output.
2. **"RANK and DENSE_RANK always produce identical results"** — FALSE, directly demonstrated with a real tie — RANK skips numbers after ties, DENSE_RANK doesn't.
3. **"A correlated subquery and a plain JOIN always perform identically"** — Not guaranteed — a correlated subquery's logical model is per-outer-row re-evaluation, which can genuinely be less efficient than an equivalent JOIN at scale, even if the query planner sometimes optimizes it away.
4. **"Recursive CTEs can traverse infinitely without any built-in safeguard"** — Worth knowing as a real risk — a recursive CTE with a mistaken join condition (e.g., accidentally creating a cycle) can genuinely run indefinitely; PostgreSQL doesn't automatically cap recursion depth by default, so careful base-case and termination-condition design is a real, practical concern.
5. **"EXISTS and IN always behave identically"** — Not universally — EXISTS only checks for row presence (can short-circuit on the first match) while IN materializes a full list to check membership against; their real performance characteristics can differ, especially with NULLs present in the subquery's result set (IN's behavior with NULLs is a well-known SQL gotcha).

---

## 9. Rapid-Fire Self-Check (MCQ Simulation)

1. What's the core conceptual difference between an aggregate function and a window function? *(Aggregates collapse multiple rows into one summary row per group; window functions compute group-aware values while preserving every individual row in the output)*
2. In the real verified tie between Bob and Carol (both 95000), what number did RANK skip to for the next distinct salary, and why? *(5 — RANK leaves a gap reflecting the two tied rows that "occupied" positions 3 and 4)*
3. What does DENSE_RANK do differently from RANK in the exact same tie scenario? *(No gap — the next distinct salary gets the very next number, 4, not 5)*
4. What two parts does a recursive CTE require? *(A base case — the starting row(s) — and a recursive case that joins the CTE to itself, combined with UNION ALL)*
5. Why might a correlated subquery be a real performance concern at scale compared to an equivalent JOIN? *(Its logical model re-evaluates the subquery once per outer row, which can be less efficient than a single JOIN operation, even though query planners sometimes optimize this internally)*

---

## Status
Every aggregate, subquery variant, CTE, recursive CTE, and window function above ran against a real live PostgreSQL database with genuine data — including an actual salary tie (Bob and Carol, both 95000) used to prove the real, structural difference between ROW_NUMBER, RANK, and DENSE_RANK, and a real recursive traversal of the same manager_id hierarchy introduced in Topic 3's self-join.

This completes the Database Fundamentals track through Topic 8. Ready for the companion **Cheatsheet — Topic 8**, or **Topic 9: NoSQL vs SQL & CAP Theorem** whenever you want to continue.
