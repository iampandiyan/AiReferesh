# Database Fundamentals — Topic 7: Keys & Constraints

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Every constraint below produced a real, genuine rejection (or acceptance) against a live PostgreSQL database — including a real side-by-side comparison of `ON DELETE CASCADE` vs `SET NULL`, showing the actual different end states, not just descriptions of what they're supposed to do.

---

## 1. What Constraints Actually Are, and Why They Matter More Than Application Code

A constraint is a rule the DATABASE ITSELF enforces on every write, regardless of which application, script, or person is doing the writing. The real value: application-level validation (checking things in Python/JS before an INSERT) can be forgotten, bypassed by a direct database access, or have a bug — a database-level constraint cannot be bypassed this way, since it's the database's own storage engine refusing the write. This connects directly to Topic 4's normalization anomalies: constraints are the actual enforcement MECHANISM that makes many of those anomalies structurally impossible, not just discouraged.

---

## 2. PRIMARY KEY — Uniqueness AND Not-Null, Both Genuinely Enforced

```sql
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
```
Real results:
```sql
INSERT INTO users VALUES (1, 'Alice');   -- SUCCEEDED
INSERT INTO users VALUES (1, 'Bob');     -- REJECTED: UniqueViolation: duplicate key value violates unique constraint "users_pkey"
INSERT INTO users VALUES (NULL, 'Carol'); -- REJECTED: NotNullViolation: null value in column "id" ... violates not-null constraint
```
**A PRIMARY KEY is genuinely two constraints bundled together**, both enforced by the database itself: UNIQUE (no duplicate values) AND NOT NULL (no missing values) — this dual enforcement is exactly what makes a primary key suitable as a reliable, always-present row identifier.

---

## 3. UNIQUE — Similar to PK, But Genuinely Allows Multiple NULLs

```sql
ALTER TABLE users ADD COLUMN email TEXT UNIQUE;
```
Real results:
```sql
UPDATE users SET email = NULL WHERE id = 2;   -- SUCCEEDED
UPDATE users SET email = NULL WHERE id = 3;   -- SUCCEEDED  <- a SECOND NULL, also accepted
UPDATE users SET email = 'alice@example.com' WHERE id = 2;   -- REJECTED (real duplicate, non-null value)
```
**A real, genuinely important distinction from PRIMARY KEY:** a `UNIQUE` constraint allows MULTIPLE rows to have NULL in that column, because SQL's NULL represents "unknown," and two unknowns are never considered "equal" to each other for uniqueness purposes (consistent with NULL's three-valued logic from Topic 2). This is exactly why an optional field (like a secondary email, or a nullable "middle name") can be `UNIQUE` without every row needing a value.

---

## 4. FOREIGN KEY — Real Referential Integrity Enforcement

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount NUMERIC
);
```
Real results:
```sql
INSERT INTO orders (user_id, amount) VALUES (1, 100);   -- SUCCEEDED (user 1 exists)
INSERT INTO orders (user_id, amount) VALUES (999, 50);  -- REJECTED: ForeignKeyViolation ... violates foreign key constraint
```
The database genuinely refused to create an "orphan" order referencing a user that doesn't exist — this is referential integrity's real, concrete meaning: the database mathematically guarantees every foreign key value corresponds to a real row in the referenced table, at all times.

**The default behavior on deleting a REFERENCED row — real rejection:**
```sql
DELETE FROM users WHERE id = 1;   -- REJECTED: violates foreign key constraint "orders_user_id_fkey" on table "orders"
```
By default (`ON DELETE` unspecified, equivalent to `RESTRICT`/`NO ACTION`), PostgreSQL genuinely refuses to delete a user who still has orders referencing them — deleting them would instantly create the exact orphan-reference problem the foreign key exists to prevent.

---

## 5. `ON DELETE` Behaviors — Real Side-by-Side Comparison

**`CASCADE` — deleting the parent genuinely deletes the children too:**
```sql
CREATE TABLE orders_cascade (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users_cascade_test(id) ON DELETE CASCADE,
    amount NUMERIC
);
```
Real result:
```
Before: orders_cascade: [(1, 1, 200), (2, 1, 300)]
DELETE FROM users_cascade_test WHERE id = 1;
After:  orders_cascade: []   <- the orders THEMSELVES were genuinely deleted
```

**`SET NULL` — deleting the parent genuinely keeps the children, but nulls the reference:**
```sql
CREATE TABLE orders_setnull (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users_setnull_test(id) ON DELETE SET NULL,
    amount NUMERIC
);
```
Real result:
```
Before: orders_setnull: [(1, 1, 400), (2, 1, 500)]
DELETE FROM users_setnull_test WHERE id = 1;
After:  orders_setnull: [(1, None, 400), (2, None, 500)]   <- orders KEPT, user_id genuinely nulled
```
**This is a real, meaningful design decision with real consequences**, not just syntax to memorize: `CASCADE` is appropriate when child records genuinely have no meaning without the parent (e.g., deleting a blog post should delete its comments). `SET NULL` is appropriate when the child record should survive independently (e.g., an order history record that should persist even if the customer account is deleted, perhaps for accounting/audit reasons) — choosing the wrong one is a real, common source of either accidental data loss (wrong CASCADE) or orphaned-looking records (wrong SET NULL, if not handled in application logic).

---

## 6. CHECK Constraint — A Real Multi-Column Business Rule

```sql
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    start_date DATE,
    end_date DATE,
    CHECK (end_date > start_date)
);
```
Real results:
```sql
INSERT INTO bookings (start_date, end_date) VALUES ('2024-01-01', '2024-01-05');  -- SUCCEEDED
INSERT INTO bookings (start_date, end_date) VALUES ('2024-01-10', '2024-01-05');  -- REJECTED: CheckViolation
```
Unlike Topic 1's single-column `CHECK (balance >= 0)`, this demonstrates that `CHECK` constraints can reference MULTIPLE columns in the same row — a genuinely powerful way to enforce real business rules (a booking's end date must be after its start date) directly at the database level, immune to any application-layer bug that might otherwise let invalid data slip through.

---

## 7. Traps & Misconceptions (MCQ-Relevant)

1. **"A PRIMARY KEY and a UNIQUE NOT NULL column are functionally identical"** — Mostly true for a single column, but a table can only have ONE primary key while it can have MANY unique constraints — and a primary key is conventionally what foreign keys reference by default.
2. **"UNIQUE prevents any NULL values"** — FALSE, directly demonstrated — multiple NULLs are genuinely allowed in a UNIQUE column; only duplicate NON-NULL values are rejected.
3. **"Deleting a parent row with a foreign key reference always fails"** — FALSE — it fails under the DEFAULT behavior (RESTRICT), but genuinely succeeds (with different consequences) under CASCADE or SET NULL, as demonstrated.
4. **"ON DELETE CASCADE and ON DELETE SET NULL produce the same practical outcome, just phrased differently"** — FALSE, directly demonstrated — CASCADE genuinely deletes the child rows entirely; SET NULL genuinely keeps them, just with a nulled reference. These have very different real consequences for data retention.
5. **"CHECK constraints can only reference a single column"** — FALSE, as demonstrated — `CHECK (end_date > start_date)` references two columns from the same row in one constraint.

---

## 8. Rapid-Fire Self-Check (MCQ Simulation)

1. What TWO separate rules does a PRIMARY KEY constraint genuinely enforce at once? *(Uniqueness AND NOT NULL — both verified with real rejected inserts)*
2. Why can a UNIQUE column genuinely contain multiple NULL values while still enforcing uniqueness on non-null values? *(NULL represents "unknown" — two unknowns are never considered equal to each other under SQL's three-valued logic, so they don't violate uniqueness)*
3. What is the real, default behavior when deleting a row that's still referenced by a foreign key, with no ON DELETE clause specified? *(The delete is rejected — RESTRICT/NO ACTION is the default, verified with a real ForeignKeyViolation)*
4. In the real verified comparison, what happened to the child `orders` rows under CASCADE vs under SET NULL when the parent user was deleted? *(CASCADE: the order rows themselves were deleted entirely. SET NULL: the order rows survived, with user_id set to NULL)*
5. Can a single CHECK constraint validate a relationship between two different columns in the same row? *(Yes, verified directly — CHECK (end_date > start_date) is a real, valid multi-column constraint)*

---

## Status
Every constraint type (PRIMARY KEY, UNIQUE, FOREIGN KEY, CHECK) and every ON DELETE behavior (default RESTRICT, CASCADE, SET NULL) produced a real, genuine result against a live PostgreSQL database — actual rejections with real error messages, and a real before/after comparison proving CASCADE and SET NULL leave data in genuinely different final states, not just differently-worded documentation.

Ready for the companion **Cheatsheet — Topic 7** or straight into **Topic 8: Aggregate Functions, Subqueries, CTEs & Window Functions** whenever you want to continue.
