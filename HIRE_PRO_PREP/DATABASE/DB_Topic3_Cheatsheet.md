# Database Cheatsheet — Topic 3 (JOIN Syntax Reference)

**Companion to:** DB_Topic3_Joins.md
**Format:** Syntax → Behavior on unmatched rows → One verified runnable example per entry

---

## `INNER JOIN`

**Syntax:**
```sql
SELECT ... FROM a INNER JOIN b ON a.key = b.key;
-- "INNER" is optional - plain JOIN means INNER JOIN
```

| Unmatched row on either side | Result |
|---|---|
| Excluded entirely | Only rows with a match on BOTH sides survive |

**Verified:** `employees INNER JOIN departments` → Heidi (no dept) and Marketing (no staff) both absent.

---

## `LEFT JOIN` / `LEFT OUTER JOIN`

**Syntax:**
```sql
SELECT ... FROM a LEFT JOIN b ON a.key = b.key;
```

| Unmatched row | Result |
|---|---|
| Left table (`a`) | Always kept, right-side columns become NULL |
| Right table (`b`) | Excluded if no matching left row exists |

**Verified:** `employees LEFT JOIN departments` → Heidi present (department=NULL), Marketing absent.

---

## `RIGHT JOIN` / `RIGHT OUTER JOIN`

**Syntax:**
```sql
SELECT ... FROM a RIGHT JOIN b ON a.key = b.key;
```

| Unmatched row | Result |
|---|---|
| Right table (`b`) | Always kept, left-side columns become NULL |
| Left table (`a`) | Excluded if no matching right row exists |

**Verified:** `employees RIGHT JOIN departments` (same table order as above) → Marketing present (name=NULL), Heidi absent — the exact mirror of LEFT JOIN's result.

---

## `FULL OUTER JOIN`

**Syntax:**
```sql
SELECT ... FROM a FULL OUTER JOIN b ON a.key = b.key;
```

| Unmatched row on either side | Result |
|---|---|
| Kept regardless | Union of what LEFT JOIN and RIGHT JOIN would each show |

**Verified:** Both Heidi AND Marketing present simultaneously.

---

## `CROSS JOIN`

**Syntax:**
```sql
SELECT ... FROM a CROSS JOIN b;
-- No ON clause - there's nothing to match on
```

| Behavior | Result size |
|---|---|
| Every row of `a` paired with every row of `b` | `COUNT(a) × COUNT(b)` |

**Verified:** 6 employees × 3 departments = 18, confirmed exactly.

---

## Self Join (Not a Keyword — a Usage Pattern)

**Syntax:**
```sql
SELECT e.name, m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;
```

| Part | Explanation |
|---|---|
| Same table, two aliases | `e` and `m` both reference `employees` — this IS the "self join," no special syntax needed |
| Typically LEFT JOIN | So rows with no manager (NULL manager_id) are still kept, rather than silently dropped |

---

## `ON` vs `USING`

**`ON`** — explicit condition, works when column names differ between tables:
```sql
SELECT ... FROM employees e JOIN departments d ON e.department_id = d.id;
```

**`USING`** — shorthand, ONLY works when the join column has the IDENTICAL name on both sides:
```sql
SELECT * FROM a JOIN b USING (id);   -- works: both tables have a column literally named 'id'
```

**Verified real failure when column names differ:**
```sql
SELECT e.name, d.name FROM employees e JOIN departments d USING (department_id);
-- psycopg2.errors.UndefinedColumn: column "department_id" specified in USING clause
-- does not exist in right table   (departments' PK is named 'id', not 'department_id')
```
`ON` was required for the employees/departments join throughout the main doc precisely because the column names don't match (`department_id` vs `id`) — `USING` genuinely isn't an option there.

---

## Status
6 syntax patterns verified with real executed output, including a genuine, real error demonstrating exactly when `USING` can and can't be used.
