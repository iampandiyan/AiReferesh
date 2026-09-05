# Database Cheatsheet — Topic 1 (Transaction Control & ACID-Related SQL)

**Companion to:** DB_Topic1_RDBMS_and_ACID.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

---

## `psycopg2` Transaction Control

**Initialization:**
```python
import psycopg2
conn = psycopg2.connect(dbname="mydb", user="postgres", password="...", host="localhost")
conn.autocommit = False   # explicit transaction control - the default in psycopg2 is actually False already
```

**Top methods:**
| Method | Explanation |
|---|---|
| `conn.autocommit = False` | Each statement is part of an open transaction until explicitly committed/rolled back |
| `conn.commit()` | Persist all changes made since the last commit/rollback |
| `conn.rollback()` | Discard ALL changes made since the last commit — verified to genuinely undo an already-executed statement when a later one in the same transaction fails |
| `conn.autocommit = True` | Each statement commits immediately on its own — useful for DDL like CREATE DATABASE which can't run inside a transaction block |

**Verified example (from the main doc):**
```python
try:
    cur.execute("UPDATE accounts SET balance = balance - 200 WHERE owner = 'Alice';")
    cur.execute("UPDATE accounts SET balance = balance + 200 WHERE ownerr = 'Bob';")  # typo
    conn.commit()
except Exception as e:
    conn.rollback()   # genuinely undoes the first UPDATE too
```

---

## `CHECK` Constraint (SQL)

**Syntax:**
```sql
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    balance NUMERIC CHECK (balance >= 0)
);
```

| Part | Explanation |
|---|---|
| `CHECK (condition)` | Any boolean SQL expression — the database rejects any INSERT/UPDATE that would violate it |
| Real enforcement | Verified — attempting to violate it raised a genuine `CheckViolation` exception, not a silent failure |

---

## Transaction Isolation Level Control

**Syntax:**
```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SELECT current_setting('transaction_isolation');
```

| Level (PostgreSQL) | Explanation |
|---|---|
| `READ COMMITTED` | PostgreSQL's real default — verified above; prevents dirty reads |
| `REPEATABLE READ` | Additionally prevents non-repeatable reads within the same transaction |
| `SERIALIZABLE` | Strictest — transactions behave as if run one at a time, fully sequentially |

**Verified example:**
```python
cur.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;")
cur.execute("SELECT current_setting('transaction_isolation');")
print(cur.fetchone()[0])   # serializable

conn.rollback()   # the isolation level setting itself is also transaction-scoped
cur.execute("SELECT current_setting('transaction_isolation');")
print(cur.fetchone()[0])   # read committed (back to default)
```

---

## WAL (Write-Ahead Log) Inspection

**Verified example:**
```python
cur.execute("SHOW wal_level;")
print(cur.fetchone()[0])   # replica

cur.execute("SELECT pg_current_wal_lsn();")
print(cur.fetchone()[0])   # 0/2622628 - a live, advancing WAL position
```

| Command | Explanation |
|---|---|
| `SHOW wal_level` | Shows the configured WAL detail level (`minimal`, `replica`, `logical`) |
| `pg_current_wal_lsn()` | Returns the current Write-Ahead Log position — advances with every committed write, confirming durability's underlying mechanism is actively running |

---

## Status
4 entries verified with real executed output against a genuinely running PostgreSQL instance.
