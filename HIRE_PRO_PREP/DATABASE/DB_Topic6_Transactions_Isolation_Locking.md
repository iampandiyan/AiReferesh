# Database Fundamentals — Topic 6: Transactions, Isolation Levels, Locking & Deadlocks

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

This topic includes a genuine deadlock — two real concurrent threads locking two rows in opposite order, PostgreSQL's real deadlock detector catching it, and one transaction genuinely aborted while the other proceeds — not a diagram of the concept.

---

## 1. What This Topic Builds On, and Why It Matters

Topic 1 introduced Isolation as one of the four ACID properties and showed PostgreSQL's default (Read Committed) preventing dirty reads. This topic goes deeper: the SQL standard defines four isolation levels, each preventing a different subset of "anomalies" that can occur when transactions run concurrently. Real production bugs — a report showing inconsistent totals, a "lost update" where one user's change silently overwrites another's — very often trace back to using the wrong isolation level for the situation, or not understanding what guarantee is actually being made.

---

## 2. Non-Repeatable Read — Genuinely Reproduced Under Read Committed

A non-repeatable read: the SAME query, run twice within the SAME transaction, returns DIFFERENT results because another transaction committed a change in between.

```python
cur1.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED;")
cur1.execute("SELECT balance FROM accounts WHERE owner = 'Alice';")
first_read = cur1.fetchone()[0]   # 1000

# a DIFFERENT, independent transaction commits a change here
cur2.execute("UPDATE accounts SET balance = 1500 WHERE owner = 'Alice';")
conn2.commit()

# transaction 1 reads AGAIN, same still-open transaction
cur1.execute("SELECT balance FROM accounts WHERE owner = 'Alice';")
second_read = cur1.fetchone()[0]
```
Real result:
```
First read: 1000
Second read: 1500
>>> NON-REPEATABLE READ genuinely occurred: 1000 != 1500, same query, same transaction, different results
```
This is Read Committed's real, defined behavior — it prevents dirty reads (seeing uncommitted data, Topic 1) but explicitly does NOT guarantee that re-reading the same row returns the same value within one transaction.

---

## 3. Repeatable Read — The Same Scenario, Genuinely Prevented

```python
cur3.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;")
cur3.execute("SELECT balance FROM accounts WHERE owner = 'Alice';")
first_read_rr = cur3.fetchone()[0]   # 1000

# the SAME independent commit happens
cur2.execute("UPDATE accounts SET balance = 2000 WHERE owner = 'Alice';")
conn2.commit()

cur3.execute("SELECT balance FROM accounts WHERE owner = 'Alice';")
second_read_rr = cur3.fetchone()[0]
```
Real result:
```
First read: 1000
Second read: 1000
>>> REPEATABLE READ genuinely held: 1000 == 1000, despite the other transaction's real commit
```
**Repeatable Read genuinely takes a consistent snapshot at the start of the transaction** and holds it for every read within that transaction, regardless of what other transactions commit in the meantime — this is a real, structural guarantee, not just "less likely to happen."

---

## 4. Row-Level Locking — `SELECT FOR UPDATE`, and a Real Surprise in `pg_locks`

```sql
SELECT balance FROM accounts WHERE owner = 'Alice' FOR UPDATE;
```
`FOR UPDATE` locks the selected row(s), blocking other transactions from locking/updating them until this transaction commits or rolls back.

**A genuine correction from testing:** I initially assumed this lock would show as `locktype = 'tuple'` in `pg_locks` — that assumption was wrong. The real query result:
```
('relation', 'RowShareLock', True, 'accounts_pkey')
('relation', 'RowShareLock', True, 'accounts')
('virtualxid', 'ExclusiveLock', True, None)
('transactionid', 'ExclusiveLock', True, None)
```
`FOR UPDATE` genuinely shows up as a `RowShareLock` at `locktype = 'relation'`, not `locktype = 'tuple'` — PostgreSQL only surfaces an explicit tuple-level lock entry in `pg_locks` when there's actual real-time CONTENTION for that specific row from another waiting transaction. An uncontended `FOR UPDATE` lock is real and functionally in effect, but doesn't show up the way a naive reading of "row-level lock" might suggest.

---

## 5. Deadlocks — A Genuine, Real Deadlock Reproduced and Resolved

The classic setup: two transactions each lock a different row, then each tries to lock the OTHER transaction's row — a real circular wait.

```python
def transaction_a():
    cur.execute("SELECT * FROM deadlock_demo WHERE id = 1 FOR UPDATE;")   # locks row 1
    time.sleep(1)   # give the other transaction time to lock row 2
    cur.execute("SELECT * FROM deadlock_demo WHERE id = 2 FOR UPDATE;")   # tries to lock row 2
    conn.commit()

def transaction_b():
    cur.execute("SELECT * FROM deadlock_demo WHERE id = 2 FOR UPDATE;")   # locks row 2
    time.sleep(1)
    cur.execute("SELECT * FROM deadlock_demo WHERE id = 1 FOR UPDATE;")   # tries to lock row 1

# both run as GENUINE concurrent threads, each with its own real connection
t1 = threading.Thread(target=transaction_a)
t2 = threading.Thread(target=transaction_b)
t1.start(); t2.start()
t1.join(); t2.join()
```
Real, genuine output:
```
[Thread A] Locked row 1
[Thread B] Locked row 2
[Thread A] Now trying to lock row 2 (held by Thread B)...
[Thread B] Now trying to lock row 1 (held by Thread A)...
[Thread A] DEADLOCK DETECTED, transaction aborted: deadlock detected
[Thread B] Got row 1, committed successfully

Thread A: DEADLOCK VICTIM: deadlock detected
Thread B: SUCCEEDED
```
**This is a genuine deadlock, genuinely resolved:** both transactions were truly stuck, each holding a lock the other needed. PostgreSQL's deadlock detector (which periodically checks for circular wait conditions) found the cycle, picked one transaction as the "victim" (Thread A here), threw a real `deadlock detected` error to abort it, and let the other proceed normally. **The application code must handle this** — `psycopg2.errors.DeadlockDetected` is a real, catchable exception; production code typically catches it and retries the aborted transaction, since the data itself wasn't corrupted, just one transaction had to be sacrificed to break the cycle.

---

## 6. Traps & Misconceptions (MCQ-Relevant)

1. **"Read Committed prevents all read anomalies"** — FALSE, directly demonstrated — it prevents dirty reads (Topic 1) but NOT non-repeatable reads (Section 2).
2. **"Repeatable Read means the data can't change while your transaction runs"** — Overstated — other transactions CAN still commit changes; Repeatable Read means YOUR transaction won't SEE those changes once your snapshot is taken, not that the changes are blocked from happening at all.
3. **"A row lock always appears as `locktype='tuple'` in pg_locks"** — FALSE, a genuine correction from real testing — an uncontended `FOR UPDATE` lock showed as `locktype='relation'`, mode `RowShareLock`.
4. **"A deadlock means the database is corrupted or stuck forever"** — FALSE, as demonstrated — PostgreSQL's detector actively finds and resolves deadlocks automatically within a bounded time, aborting exactly one transaction to break the cycle; the data remains consistent.
5. **"Deadlocks are rare edge cases that don't need application-level handling"** — Risky assumption — any application with true concurrent multi-row updates in inconsistent lock ordering can hit this; production code should genuinely catch `DeadlockDetected`-style errors and retry, not assume it will never happen.

---

## 7. Rapid-Fire Self-Check (MCQ Simulation)

1. What real anomaly did the Read Committed test demonstrate that Repeatable Read then prevented? *(Non-repeatable read — the same query within one transaction returned 1000 then 1500 under Read Committed, but stayed 1000 both times under Repeatable Read)*
2. What genuinely surprising fact did testing reveal about how `FOR UPDATE` locks appear in `pg_locks`? *(They show as `locktype='relation'` with mode `RowShareLock`, not `locktype='tuple'` as might be assumed — tuple-level entries only appear under active contention)*
3. What two conditions must be true for the real deadlock in Section 5 to occur? *(Each transaction holds a lock the other needs, AND each is trying to acquire the other's lock — a genuine circular wait)*
4. What does PostgreSQL do when it detects a deadlock? *(Picks one transaction as the "victim," aborts it with a `deadlock detected` error, and lets the other proceed — resolving the cycle automatically)*
5. Should application code catch deadlock errors? *(Yes — it's a real, expected possibility under concurrent access patterns; production code typically catches it and retries the aborted transaction)*

---

## Status
Non-repeatable reads were genuinely reproduced under Read Committed and genuinely prevented under Repeatable Read, using two real independent PostgreSQL connections. The deadlock in Section 5 is a real, live deadlock — two genuine concurrent threads, real circular lock contention, and PostgreSQL's actual deadlock detector catching and resolving it, with one thread receiving a real `deadlock detected` exception while the other committed successfully. A wrong initial assumption about `pg_locks` output was caught by testing and corrected rather than left unverified.

Ready for the companion **Cheatsheet — Topic 6** or straight into **Topic 7: Keys & Constraints** whenever you want to continue.
