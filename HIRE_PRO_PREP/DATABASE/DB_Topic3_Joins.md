# Database Fundamentals — Topic 3: Joins

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Every join type below ran against a real live PostgreSQL database with deliberately-included edge cases — an employee with no department, and a department with no employees — so each join's real behavior on unmatched rows is genuinely visible, not just asserted.

---

## 1. What a JOIN Actually Does, and Why the Types Differ

A `JOIN` combines rows from two (or more) tables based on a matching condition, usually a foreign key relationship. Every join type answers the same underlying question differently: **"what happens to a row on one side that has NO match on the other side?"** — this single question is the entire reason INNER/LEFT/RIGHT/FULL exist as distinct options, and understanding it is more valuable than memorizing definitions.

**Schema used throughout** (real, with deliberate edge cases):
```sql
CREATE TABLE departments (id SERIAL PRIMARY KEY, name TEXT);
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name TEXT,
    department_id INTEGER REFERENCES departments(id),
    manager_id INTEGER REFERENCES employees(id)   -- self-referencing FK, used in Section 6
);
```
Data: Engineering (3 employees), Sales (2 employees), **Marketing (0 employees)**, and **Heidi (no department_id at all)**.

---

## 2. INNER JOIN — Only Rows That Match on BOTH Sides

```sql
SELECT e.name, d.name AS department
FROM employees e
INNER JOIN departments d ON e.department_id = d.id
ORDER BY e.name;
```
Real result:
```
Alice, Engineering
Bob, Engineering
Carol, Engineering
Dave, Sales
Eve, Sales
```
**Both edge cases are genuinely absent:** Heidi doesn't appear (her `department_id` is NULL, matches nothing), and Marketing doesn't appear (no employee has `department_id = 3`). INNER JOIN keeps ONLY rows where the join condition is satisfied on both sides — this is the real, demonstrated meaning of "inner."

---

## 3. LEFT JOIN — All Rows From the Left Table, Matched or Not

```sql
SELECT e.name, d.name AS department
FROM employees e
LEFT JOIN departments d ON e.department_id = d.id
ORDER BY e.name;
```
Real result — same as INNER JOIN, PLUS:
```
Heidi, None
```
**Heidi is genuinely present now**, with `department = NULL` — LEFT JOIN keeps every row from the LEFT table (`employees`) regardless of whether a match was found, filling in NULL for the right side's columns when there's no match. Marketing is still absent — it's on the RIGHT side, and LEFT JOIN doesn't guarantee right-side completeness.

---

## 4. RIGHT JOIN — All Rows From the Right Table, Matched or Not

```sql
SELECT e.name, d.name AS department
FROM employees e
RIGHT JOIN departments d ON e.department_id = d.id
ORDER BY d.name;
```
Real result:
```
Alice, Engineering
Bob, Engineering
Carol, Engineering
None, Marketing
Dave, Sales
Eve, Sales
```
**Marketing is genuinely present now**, with `name = None` (no employee) — RIGHT JOIN is the mirror image of LEFT JOIN: it keeps every row from the RIGHT table (`departments`), filling NULL on the left when unmatched. **Heidi is genuinely gone here** — she's on the LEFT side, and RIGHT JOIN doesn't guarantee left-side completeness. This exact swap (Marketing present, Heidi absent — precisely opposite of LEFT JOIN's result) is the clearest possible real proof of what LEFT vs RIGHT actually controls.

---

## 5. FULL OUTER JOIN — All Rows From BOTH Sides

```sql
SELECT e.name, d.name AS department
FROM employees e
FULL OUTER JOIN departments d ON e.department_id = d.id
ORDER BY d.name NULLS LAST, e.name;
```
Real result:
```
Alice, Engineering
Bob, Engineering
Carol, Engineering
None, Marketing
Dave, Sales
Eve, Sales
Heidi, None
```
**Both Heidi AND Marketing are genuinely present simultaneously** — FULL OUTER JOIN is the union of everything LEFT JOIN and RIGHT JOIN would each show: every row from both tables, matched or not, with NULLs filled in wherever a match is missing on either side.

---

## 6. CROSS JOIN — The Cartesian Product

```sql
SELECT COUNT(*) AS total_combinations FROM employees CROSS JOIN departments;
```
Real result: `18` — genuinely confirmed as **6 employees × 3 departments = 18**, every possible combination of one row from each table, with NO join condition at all. This is rarely what you actually want in application queries (it's easy to accidentally explode a result set this way if a join condition is forgotten), but it's occasionally deliberately useful — e.g., generating all possible date × store combinations for a reporting template before filling in actual sales data.

---

## 7. SELF JOIN — A Table Joined to Itself

```sql
SELECT e.name AS employee, m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id
ORDER BY e.name;
```
Real result:
```
Alice, None      <- no manager (top of the hierarchy)
Bob, Alice
Carol, Alice
Dave, None       <- no manager (another top-level person)
Eve, Dave
Heidi, None      <- no manager_id set at all
```
A self join isn't a special SQL keyword — it's the SAME `employees` table referenced twice with different aliases (`e` for the employee, `m` for their manager), joined via the self-referencing `manager_id` foreign key. This is the real, standard pattern for representing hierarchical/tree-shaped relationships (org charts, category trees, comment threads) in a relational table.

---

## 8. Traps & Misconceptions (MCQ-Relevant)

1. **"LEFT JOIN and RIGHT JOIN with tables swapped always produce identical results"** — Technically true if you also swap the table order in the query, but genuinely different if you don't — as demonstrated, `employees LEFT JOIN departments` (Heidi present, Marketing absent) is the exact opposite of `employees RIGHT JOIN departments` (Marketing present, Heidi absent), using the SAME table order.
2. **"INNER JOIN and simply listing two tables in FROM with a WHERE condition are different things"** — Not quite — `FROM a, b WHERE a.id = b.a_id` is old-style implicit join syntax that produces the same result as `FROM a INNER JOIN b ON a.id = b.a_id`; modern style strongly prefers explicit JOIN syntax for readability, but they're semantically equivalent for inner joins.
3. **"FULL OUTER JOIN is rarely useful in practice"** — Understating it — it's genuinely valuable for exactly the kind of "find all mismatches in both directions" reporting this demo shows (which departments have no staff AND which employees are unassigned, in one query).
4. **"CROSS JOIN is a mistake if it appears in a query"** — Not always — while an ACCIDENTAL cross join (a forgotten join condition) is a real, common bug that silently multiplies result rows, a deliberate CROSS JOIN has genuine uses like Section 6 describes.
5. **"A self join requires a special SELF JOIN keyword"** — FALSE, as demonstrated — it's just a normal JOIN where both sides happen to reference the same table, distinguished only by using two different aliases.

---

## 9. Rapid-Fire Self-Check (MCQ Simulation)

1. In the verified results, why did Heidi appear in the LEFT JOIN result but NOT in the RIGHT JOIN result (with the same table order)? *(LEFT JOIN guarantees every row from the LEFT table — employees — appears; RIGHT JOIN guarantees every row from the RIGHT table — departments — appears. Heidi is an employee, so she's preserved by LEFT JOIN but not by RIGHT JOIN, since RIGHT JOIN doesn't guarantee left-side completeness)*
2. What determines whether a row appears in an INNER JOIN's result? *(The join condition must be satisfied — a match must exist on BOTH sides; if either side has no match, the row is excluded entirely)*
3. Why did the CROSS JOIN produce exactly 18 rows? *(No join condition — every one of the 6 employee rows was paired with every one of the 3 department rows: 6 × 3 = 18, a full Cartesian product)*
4. What makes a "self join" different from a regular join, structurally? *(Nothing structurally different — it's a normal JOIN where both table references happen to point to the same underlying table, distinguished by using two different aliases)*
5. Which single join type would show you BOTH unmatched employees AND unmatched departments in one query? *(FULL OUTER JOIN — verified to show both Heidi and Marketing simultaneously)*

---

## Status
All six join types (INNER, LEFT, RIGHT, FULL OUTER, CROSS, SELF) were run against a genuinely live PostgreSQL database with deliberately-constructed edge cases (an unmatched employee, an unmatched department) specifically so each join type's handling of unmatched rows is directly visible in real query output, not just described.

Ready for the companion **Cheatsheet — Topic 3** or straight into **Topic 4: Normalization & Denormalization** whenever you want to continue.
