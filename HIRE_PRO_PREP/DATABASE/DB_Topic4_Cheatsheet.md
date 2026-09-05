# Database Cheatsheet — Topic 4 (Normalization Quick Reference & DDL Patterns)

**Companion to:** DB_Topic4_Normalization.md
**Format:** Rule → Violation signal → Fix pattern → Verified reference from the main doc

---

## Normal Forms — Quick Reference Table

| Form | Rule | Violation Signal | Fix |
|---|---|---|---|
| 1NF | Atomic values only, no repeating groups | A column stores multiple values (comma-separated list, array-like text) | Split into a child table with one row per value |
| 2NF | No partial dependency on a composite key | A non-key column depends on only PART of a composite primary key | Move that column to its own table, keyed by the part it actually depends on |
| 3NF | No transitive dependency | A non-key column depends on ANOTHER non-key column, not directly on the key | Move that column to its own table, referenced by foreign key |
| BCNF | Every determinant must be a superkey | A non-superkey column determines another column's value (rare edge case with overlapping candidate keys) | Same fix pattern — split into a separate table |

**Verified real examples of each, with actual anomalies reproduced:** see the main Topic 4 doc — phone numbers (1NF), product_name in order_items (2NF), department_location in employees (3NF).

---

## `REFERENCES` — Foreign Key Constraint Syntax

**Syntax:**
```sql
CREATE TABLE orders_norm (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers_norm(customer_id),
    product TEXT,
    amount NUMERIC
);
```

| Part | Explanation |
|---|---|
| `REFERENCES table(column)` | Declares a foreign key — PostgreSQL enforces that any value inserted here must exist in the referenced table's column |
| Effect on normalization | This IS the mechanism that makes normalized schemas queryable via JOIN — the FK is what lets scattered facts be reassembled |

---

## Composite Primary Key Syntax

**Syntax:**
```sql
CREATE TABLE order_items_2nf (
    order_id INTEGER,
    product_id INTEGER REFERENCES products_2nf(product_id),
    quantity INTEGER,
    PRIMARY KEY (order_id, product_id)
);
```

| Part | Explanation |
|---|---|
| `PRIMARY KEY (col1, col2)` | The combination of both columns must be unique — neither column alone is guaranteed unique |
| Relevance to 2NF | 2NF's partial-dependency rule only applies to tables with a composite key like this — a single-column PK table automatically satisfies 2NF |

---

## `RETURNING` — Get Generated Values Back Immediately

**Syntax:**
```sql
INSERT INTO customers_norm (name, email) VALUES ('Bob', 'bob@old-email.com') RETURNING customer_id;
```

| Part | Explanation |
|---|---|
| `RETURNING column` | Returns the specified column(s) from the just-inserted (or updated/deleted) row(s) in the same round-trip |
| Why it matters here | Used throughout the main doc's verification to immediately capture an auto-generated `SERIAL` id for use in subsequent inserts, without a separate query |

**Verified pattern (used repeatedly in the main doc):**
```python
cur.execute("INSERT INTO customers_norm (name, email) VALUES ('Bob', '...') RETURNING customer_id;")
bob_id = cur.fetchone()[0]
```

---

## Status
Normal form rules summarized as a quick-reference table, plus the 3 core DDL patterns (REFERENCES, composite PRIMARY KEY, RETURNING) used throughout the main doc's real verified schemas.
