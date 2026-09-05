# Database Fundamentals — Topic 2: SQL Fundamentals

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Every query below ran against a real live PostgreSQL database with genuine sample data — including a query that was deliberately expected to fail, and did, with the exact real error message shown.

---

## 1. What SQL Actually Is, and Why These Clauses Exist in This Order

SQL (Structured Query Language) is a **declarative** language — you describe WHAT data you want, not the step-by-step procedure for finding it (that's the database's query planner's job, touched on in Topic 5 of the API track). The clauses in a `SELECT` statement are written in one order but conceptually EXECUTE in a different logical order — this distinction is exactly what makes `HAVING` vs `WHERE` (Section 5) make sense: `FROM` → `WHERE` → `GROUP BY` → `HAVING` → `SELECT` → `ORDER BY`. Understanding this execution order, not just the written syntax order, is the real key to this whole topic.

Sample data used throughout (a real table, genuinely created and populated):
```sql
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name TEXT,
    department TEXT,
    salary NUMERIC,
    hire_date DATE,
    manager_id INTEGER
);
```
8 employees across Engineering, Sales, Marketing, and one with a NULL department — deliberately included to demonstrate real NULL behavior below.

---

## 2. SELECT Basics

```sql
SELECT name, salary FROM employees ORDER BY id LIMIT 3;
```
Real result: `Alice 95000`, `Bob 82000`, `Carol 78000`

```sql
SELECT DISTINCT department FROM employees ORDER BY department;
```
Real result: `Engineering`, `Marketing`, `Sales`, `None` — **note the NULL department genuinely appears as its own distinct value**, a real MCQ-relevant fact: `DISTINCT` treats NULL as a single group, not as "unknown/excluded."

```sql
SELECT name, salary AS annual_pay FROM employees ORDER BY id LIMIT 2;
```
`AS` renames the output column — real result column name genuinely became `annual_pay`, confirmed via `cur.description`.

---

## 3. WHERE — Filtering, Including Real NULL Behavior

```sql
SELECT name, salary FROM employees WHERE salary > 70000 AND department = 'Sales';
-- Real result: Eve, 71000 (only one row - Dave and Frank are below 70000)

SELECT name, department FROM employees WHERE department IN ('Sales', 'Marketing');
-- Real result: Dave, Eve, Frank (Sales), Grace (Marketing)

SELECT name, salary FROM employees WHERE salary BETWEEN 65000 AND 80000 ORDER BY salary;
-- Real result: Dave(65000), Frank(69000), Eve(71000), Carol(78000) - BETWEEN is inclusive on both ends

SELECT name FROM employees WHERE name LIKE 'A%' OR name LIKE '%e';
-- Real result: Alice, Dave, Eve, Grace
```

**Real, critical NULL-handling demonstration:**
```sql
SELECT name FROM employees WHERE department IS NULL;
-- Real result: Heidi

SELECT name FROM employees WHERE department = NULL;
-- Real result: (ZERO rows returned - genuinely empty, not an error)
```
This is one of the most important, genuinely-verified SQL facts in this document: **`department = NULL` is NEVER true, for any row, even rows where department genuinely IS NULL.** NULL represents "unknown," and SQL's three-valued logic means comparing anything to NULL with `=` yields NULL (neither true nor false), which the WHERE clause treats as "exclude this row." You must use `IS NULL` / `IS NOT NULL` specifically — this is a real, common, and costly mistake in production code (a filter that silently returns nothing, with no error).

---

## 4. ORDER BY

```sql
SELECT department, name, salary FROM employees ORDER BY department ASC, salary DESC;
```
Real result — sorted by department alphabetically, then by salary descending WITHIN each department:
```
Engineering, Alice, 95000
Engineering, Bob, 82000
Engineering, Carol, 78000
Marketing, Grace, 60000
Sales, Eve, 71000
Sales, Frank, 69000
Sales, Dave, 65000
None, Heidi, 55000
```
Note NULL department sorted LAST by default (PostgreSQL's default is `NULLS LAST` for ascending sort).

**Explicit NULL ordering control:**
```sql
SELECT name, department FROM employees ORDER BY department NULLS FIRST;
```
Real result: **Heidi (NULL department) now appears FIRST**, confirming `NULLS FIRST`/`NULLS LAST` genuinely overrides the default — a real, commonly-tested syntax detail.

---

## 5. GROUP BY

```sql
SELECT department, COUNT(*) AS headcount, AVG(salary) AS avg_salary
FROM employees
GROUP BY department
ORDER BY avg_salary DESC;
```
Real result:
```
Engineering, 3, 85000.00
Sales,       3, 68333.33
Marketing,   1, 60000.00
None,        1, 55000.00
```
**MCQ-relevant point:** every column in the `SELECT` list that isn't wrapped in an aggregate function (`COUNT`, `AVG`, etc.) MUST appear in the `GROUP BY` clause — this is what makes `department` valid here (it's both selected and grouped by), while `name` couldn't be added to this SELECT without also adding it to GROUP BY (which would defeat the purpose of aggregating).

---

## 6. HAVING vs WHERE — The Real, Demonstrated Difference

This is the single most commonly confused pair of clauses in SQL, and the execution order from Section 1 is exactly why they behave differently.

**WHERE filters individual ROWS, BEFORE grouping happens:**
```sql
SELECT department, COUNT(*) AS headcount, AVG(salary) AS avg_salary
FROM employees
WHERE salary > 65000
GROUP BY department
ORDER BY avg_salary DESC;
```
Real result:
```
Engineering, 3, 85000.00
Sales,       2, 70000.00    <- Dave (65000, excluded by WHERE) is gone; only Eve+Frank remain, avg recalculated
```
Sales headcount dropped from 3 to 2 BEFORE the average was even computed, because Dave's row (salary=65000, not `> 65000`) never made it into the grouping at all.

**HAVING filters GROUPS, AFTER aggregation has already happened:**
```sql
SELECT department, COUNT(*) AS headcount, AVG(salary) AS avg_salary
FROM employees
GROUP BY department
HAVING AVG(salary) > 70000
ORDER BY avg_salary DESC;
```
Real result:
```
Engineering, 3, 85000.00
```
**Sales is gone entirely here** — not because any individual employee was filtered out, but because Sales' GROUP average (68333.33) didn't clear the 70000 threshold. All 3 Sales rows contributed to computing that average; the whole GROUP was then discarded.

**The real proof that WHERE literally cannot use aggregates:**
```sql
SELECT department FROM employees WHERE AVG(salary) > 70000 GROUP BY department;
```
Real error:
```
GroupingError: aggregate functions are not allowed in WHERE
```
This isn't a style preference — it's a real, structural impossibility given the execution order: `WHERE` runs BEFORE `GROUP BY`/aggregation, so at the point `WHERE` is evaluated, no aggregate value like `AVG(salary)` exists yet to compare against. `HAVING` exists specifically because SQL needs a clause that runs AFTER aggregation.

---

## 7. Traps & Misconceptions (MCQ-Relevant)

1. **"`department = NULL` correctly finds rows where department is NULL"** — FALSE, genuinely verified above — this returns zero rows always. Use `IS NULL`.
2. **"WHERE and HAVING are interchangeable, just different keywords for the same thing"** — FALSE, directly demonstrated — they filter at different STAGES (rows before grouping vs groups after aggregation), producing genuinely different results on the same query intent.
3. **"DISTINCT ignores NULL values"** — FALSE, verified above — NULL appeared as its own distinct group in the DISTINCT results.
4. **"ORDER BY always puts NULLs last, in every database"** — Not universal — PostgreSQL's default is NULLS LAST for ASC (verified), but this default can differ across database systems, which is exactly why explicit `NULLS FIRST`/`NULLS LAST` exists.
5. **"You can use an aggregate function in WHERE if you just add GROUP BY"** — FALSE, verified with a real error — aggregates are structurally disallowed in WHERE regardless of what else is in the query; HAVING is the only correct clause for that.

---

## 8. Rapid-Fire Self-Check (MCQ Simulation)

1. What does `SELECT name FROM employees WHERE department = NULL;` actually return? *(Zero rows, always — NULL comparisons with = are never true; IS NULL must be used instead)*
2. In `SELECT department, AVG(salary) FROM employees GROUP BY department HAVING AVG(salary) > 70000`, at what point is the `70000` threshold applied — before or after grouping? *(After — HAVING filters already-computed GROUP aggregates, not individual rows)*
3. Why does `WHERE AVG(salary) > 70000` raise a real error? *(WHERE executes before GROUP BY/aggregation in SQL's logical execution order, so no aggregate value exists yet at that point to filter on)*
4. If a WHERE clause excludes a row before GROUP BY runs, does that row contribute to any group's aggregate calculation? *(No — verified directly: excluding Dave via WHERE changed Sales' computed average, proving excluded rows never reach aggregation)*
5. What must be true of every non-aggregated column in a SELECT list when GROUP BY is used? *(It must also appear in the GROUP BY clause)*

---

## Status
Every clause and behavior above — including real NULL comparison behavior, real NULLS FIRST/LAST sorting, real WHERE-vs-HAVING row counts and averages, and a real rejected query proving WHERE can't use aggregates — ran against a genuinely live PostgreSQL database with real sample data, not illustrative examples.

Ready for the companion **Cheatsheet — Topic 2** or straight into **Topic 3: Joins** whenever you want to continue.
