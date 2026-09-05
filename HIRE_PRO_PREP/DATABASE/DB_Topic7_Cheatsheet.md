# Database Cheatsheet — Topic 7 (Keys & Constraints Syntax)

**Companion to:** DB_Topic7_Keys_and_Constraints.md
**Format:** Syntax → Real enforcement behavior → Verified reference from the main doc

---

## `PRIMARY KEY`

**Syntax:**
```sql
CREATE TABLE t (id INTEGER PRIMARY KEY, ...);
-- or, for composite keys:
CREATE TABLE t (col1 INT, col2 INT, ..., PRIMARY KEY (col1, col2));
```

| Enforces | Verified real behavior |
|---|---|
| Uniqueness | Duplicate insert → `UniqueViolation` |
| NOT NULL | NULL insert → `NotNullViolation` |
| One per table | A table can only have one PRIMARY KEY (composite or single-column) |

---

## `UNIQUE`

**Syntax:**
```sql
ALTER TABLE t ADD COLUMN col TEXT UNIQUE;
-- or inline: CREATE TABLE t (col TEXT UNIQUE);
```

| Enforces | Verified real behavior |
|---|---|
| Uniqueness of non-null values | Duplicate non-null value → `UniqueViolation` |
| Does NOT enforce NOT NULL | Multiple NULLs genuinely accepted — verified with two separate NULL inserts, both succeeded |
| Many per table | A table can have multiple UNIQUE constraints, unlike PRIMARY KEY |

---

## `FOREIGN KEY` / `REFERENCES`

**Syntax:**
```sql
CREATE TABLE child (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES parent(id)   -- default ON DELETE behavior = RESTRICT
);
```

| Enforces | Verified real behavior |
|---|---|
| Referential integrity on INSERT | Inserting a value with no matching parent row → `ForeignKeyViolation` |
| Referential integrity on parent DELETE (default) | Deleting a referenced parent row → `ForeignKeyViolation`, rejected |

---

## `ON DELETE` Clauses

**Syntax:**
```sql
... REFERENCES parent(id) ON DELETE CASCADE;
... REFERENCES parent(id) ON DELETE SET NULL;
... REFERENCES parent(id) ON DELETE RESTRICT;   -- also the implicit default
```

| Clause | Real verified effect when parent is deleted |
|---|---|
| `CASCADE` | Child rows are genuinely DELETED too |
| `SET NULL` | Child rows survive, their FK column genuinely becomes NULL |
| `RESTRICT` / default | The parent DELETE itself is rejected while children reference it |

---

## `CHECK`

**Syntax:**
```sql
CREATE TABLE t (
    col1 NUMERIC CHECK (col1 >= 0),                    -- single-column
    start_date DATE, end_date DATE,
    CHECK (end_date > start_date)                        -- multi-column, table-level
);
```

| Enforces | Verified real behavior |
|---|---|
| Any boolean SQL expression | Violating row → `CheckViolation`, insert/update rejected |
| Can span multiple columns | `CHECK (end_date > start_date)` verified to reject an invalid date pair |

---

## Status
5 constraint types, all verified with real rejections/acceptances against a genuinely running PostgreSQL database.
