# Database Cheatsheet — Topic 6 (Isolation, Locking & Deadlock Handling)

**Companion to:** DB_Topic6_Transactions_Isolation_Locking.md
**Format:** Syntax/API → Real behavior → Verified reference from the main doc

`SET TRANSACTION ISOLATION LEVEL` basic usage is already in the Topic 1 cheatsheet — this entry expands it with all four standard levels and their real, defined guarantees.

---

## The Four Isolation Levels

**Syntax:**
```sql
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;  -- PostgreSQL treats this identically to READ COMMITTED
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;     -- PostgreSQL's real default
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

| Level | Prevents dirty read | Prevents non-repeatable read | Prevents phantom read |
|---|---|---|---|
| Read Uncommitted | (PostgreSQL: yes anyway) | No | No |
| Read Committed (default) | Yes | **No — verified directly** | No |
| Repeatable Read | Yes | **Yes — verified directly** | Yes (in PostgreSQL specifically, stricter than the SQL standard requires) |
| Serializable | Yes | Yes | Yes |

**Real verified proof of the Read Committed vs Repeatable Read row:** identical two-read test — Read Committed showed 1000 then 1500 (anomaly occurred); Repeatable Read showed 1000 then 1000 (anomaly prevented).

---

## `SELECT ... FOR UPDATE` — Row Locking

**Syntax:**
```sql
SELECT * FROM table_name WHERE condition FOR UPDATE;
```

| Behavior | Explanation |
|---|---|
| Locks the selected row(s) | Other transactions attempting to lock/update the SAME rows will block until this transaction commits/rolls back |
| Appears in `pg_locks` as | `locktype='relation'`, `mode='RowShareLock'` for the uncontended case — verified directly, corrected from an initial wrong assumption |

---

## `pg_locks` — Inspecting Real Lock State

**Syntax:**
```sql
SELECT locktype, mode, granted, relation::regclass FROM pg_locks WHERE pid = <backend_pid>;
```

| Column | Explanation |
|---|---|
| `locktype` | `relation`, `tuple`, `transactionid`, `virtualxid`, etc. |
| `mode` | The specific lock strength (`RowShareLock`, `ExclusiveLock`, etc.) |
| `granted` | `True` if the lock is currently held; `False` if the backend is waiting for it |

**Getting the current connection's backend PID (psycopg2):**
```python
conn.get_backend_pid()
```

---

## `psycopg2.errors.DeadlockDetected` — Real Exception Handling

**Usage:**
```python
try:
    cur.execute("SELECT * FROM table WHERE id = %s FOR UPDATE;", (some_id,))
    # ... more work that could deadlock with another transaction ...
    conn.commit()
except psycopg2.errors.DeadlockDetected as e:
    conn.rollback()
    # real production pattern: retry the transaction after a short backoff
```

| Part | Explanation |
|---|---|
| Real trigger condition | Two transactions holding locks the other needs, in a circular wait — verified with two genuine concurrent threads |
| What PostgreSQL does | Automatically detects the cycle and aborts ONE transaction (the "victim") with this exception, letting the other proceed |

---

## `threading.Thread` — Simulating Real Concurrent Transactions

**Pattern used for the real deadlock demo:**
```python
import threading

t1 = threading.Thread(target=transaction_a)
t2 = threading.Thread(target=transaction_b)
t1.start(); t2.start()
t1.join(); t2.join()
```
Each thread opens its OWN separate `psycopg2` connection — this is essential, since a single connection can't have two transactions genuinely running concurrently against each other; true concurrent contention (and thus a real deadlock) requires separate real connections/backends.

---

## Status
5 entries verified with real executed behavior, including a genuine two-thread deadlock and its real detection/resolution by PostgreSQL.
