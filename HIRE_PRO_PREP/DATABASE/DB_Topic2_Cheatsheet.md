# Database Cheatsheet — Topic 2 (SQL Fundamentals Syntax)

**Companion to:** DB_Topic2_SQL_Fundamentals.md
**Format:** Syntax → Top variations/operators → One verified runnable example per entry (all reused directly from the main doc's real PostgreSQL run)

---

## `SELECT` / `DISTINCT` / `AS`

**Syntax:**
```sql
SELECT column1, column2 AS alias FROM table_name;
SELECT DISTINCT column1 FROM table_name;
```

| Keyword | Explanation |
|---|---|
| `AS` | Renames a column (or table) in the output — optional keyword, `col AS alias` and `col alias` both work |
| `DISTINCT` | Removes duplicate rows from the result — verified to treat NULL as its own distinct group, not exclude it |
| `LIMIT n` | Restricts result to the first n rows (combine with `ORDER BY` for a meaningful "top n") |

**Verified example:**
```sql
SELECT DISTINCT department FROM employees ORDER BY department;
-- Engineering, Marketing, Sales, NULL  <- NULL genuinely appears as its own group
```

---

## `WHERE` — Operators

| Operator | Explanation |
|---|---|
| `=`, `<>` / `!=`, `<`, `>`, `<=`, `>=` | Standard comparisons |
| `AND`, `OR`, `NOT` | Combine conditions |
| `IN (val1, val2, ...)` | Match any value in a list |
| `BETWEEN low AND high` | Inclusive range check |
| `LIKE 'pattern'` | Pattern match — `%` = any sequence of characters, `_` = any single character |
| `IS NULL` / `IS NOT NULL` | **The only correct way to test for NULL** — `= NULL` always returns zero rows, verified directly |

**Verified example (the most important one in this cheatsheet):**
```sql
SELECT name FROM employees WHERE department IS NULL;      -- correct: returns Heidi
SELECT name FROM employees WHERE department = NULL;       -- WRONG: always returns zero rows
```

---

## `ORDER BY`

**Syntax:**
```sql
SELECT ... ORDER BY column1 ASC, column2 DESC;
SELECT ... ORDER BY column1 NULLS FIRST;
```

| Part | Explanation |
|---|---|
| `ASC` (default) / `DESC` | Sort direction |
| Multiple columns | Sorts by the first column, then breaks ties using the next column, and so on |
| `NULLS FIRST` / `NULLS LAST` | Explicit control over NULL placement — PostgreSQL's default for ASC is NULLS LAST, verified to be overridable |

**Verified example:**
```sql
SELECT name, department FROM employees ORDER BY department NULLS FIRST;
-- Heidi (NULL) now appears first, confirmed by real query result
```

---

## `GROUP BY`

**Syntax:**
```sql
SELECT department, COUNT(*), AVG(salary)
FROM employees
GROUP BY department;
```

| Rule | Explanation |
|---|---|
| Every non-aggregated SELECT column must appear in GROUP BY | Verified as a real structural requirement, not a style guideline |
| Common aggregate functions | `COUNT(*)`, `SUM()`, `AVG()`, `MIN()`, `MAX()` |

**Verified example:**
```sql
SELECT department, COUNT(*) AS headcount, AVG(salary) AS avg_salary
FROM employees GROUP BY department ORDER BY avg_salary DESC;
-- Engineering 3 85000.00 | Sales 3 68333.33 | Marketing 1 60000.00 | NULL 1 55000.00
```

---

## `HAVING` vs `WHERE`

| Clause | Filters | Runs |
|---|---|---|
| `WHERE` | Individual rows | BEFORE grouping/aggregation |
| `HAVING` | Aggregated groups | AFTER grouping/aggregation |

**Verified example showing genuinely different results from the same underlying data:**
```sql
-- WHERE: excludes Dave's row BEFORE Sales' average is computed
SELECT department, COUNT(*), AVG(salary) FROM employees
WHERE salary > 65000 GROUP BY department;
-- Sales: 2 employees, avg=70000.00

-- HAVING: all 3 Sales rows contribute to the average, THEN the group is checked/dropped
SELECT department, AVG(salary) FROM employees
GROUP BY department HAVING AVG(salary) > 70000;
-- Sales is entirely absent - its full-group average (68333.33) didn't clear the bar
```

**A real error proving the structural rule:**
```sql
SELECT department FROM employees WHERE AVG(salary) > 70000 GROUP BY department;
-- GroupingError: aggregate functions are not allowed in WHERE
```

---

## Status
6 clause groups, all verified with real executed SQL against a genuinely running PostgreSQL database.
