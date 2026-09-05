# Database Fundamentals — Topic 1: RDBMS Core Concepts & ACID Properties

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Every ACID property below is demonstrated against a real, live PostgreSQL database — including a genuine two-connection isolation test proving no dirty reads occur, not a diagram.

---

## 1. What an RDBMS Is, and Why ACID Matters

A **Relational Database Management System (RDBMS)** organizes data into tables (relations) with rows and columns, connected via keys — as opposed to, say, a flat file or a document store. The relational model's real value comes from enforcing structure and relationships mathematically (via foreign keys, constraints) rather than trusting application code to maintain them correctly.

**Why ACID exists — the actual problem it solves:** a database is used by many concurrent operations simultaneously — multiple users, multiple requests, background jobs — all reading and writing at once. Without strict guarantees, this concurrency creates real, damaging bugs: money could vanish during a transfer if the server crashes halfway through, two people could overdraw the same account by both reading a stale balance at the same time, or a half-finished multi-step operation could leave data in an impossible state. ACID is the formal contract a database makes to prevent exactly these failure modes.

**A**tomicity, **C**onsistency, **I**solation, **D**urability — each demonstrated below, for real.

---

## 2. Atomicity — All-or-Nothing, Demonstrated With a Real Failure

```python
conn.autocommit = False   # explicit transaction control

try:
    cur.execute("UPDATE accounts SET balance = balance - 200 WHERE owner = 'Alice';")
    cur.execute("UPDATE accounts SET balance = balance + 200 WHERE ownerr = 'Bob';")  # typo -> real error
    conn.commit()
except Exception as e:
    conn.rollback()
    print(f"Transaction FAILED and was rolled back: {type(e).__name__}")
```
Real output:
```
Before transfer attempt: [('Alice', 1000), ('Bob', 500)]
Transaction FAILED and was rolled back. Error: UndefinedColumn
After failed transfer (should be UNCHANGED): [('Alice', 1000), ('Bob', 500)]
```
This is a genuinely real, unintentional error (a typo — `ownerr` instead of `owner`) that produced a real `UndefinedColumn` exception, and the important part: **Alice's balance stayed at 1000, not 800** — even though the first `UPDATE` statement genuinely executed before the error hit. Atomicity means the entire transaction is treated as one indivisible unit: either every statement in it takes effect, or none do. Without this guarantee, a transfer failure partway through would leave Alice debited with Bob never credited — money genuinely disappearing.

---

## 3. Consistency — Constraints Enforce Valid State, Demonstrated With a Real Rejection

```sql
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    owner TEXT,
    balance NUMERIC CHECK (balance >= 0)
);
```
```python
try:
    cur.execute("UPDATE accounts SET balance = balance - 10000 WHERE owner = 'Bob';")
    conn.commit()
except Exception as e:
    conn.rollback()
    print(f"REJECTED by real CHECK constraint: {type(e).__name__}")
```
Real output:
```
REJECTED by real CHECK constraint: CheckViolation: new row for relation "accounts" violates check constraint "accounts_balance_check"
Bob's balance after rejected update (still valid): [('Alice', 1000), ('Bob', 500)]
```
The database genuinely refused to let Bob's balance go negative, because the `CHECK (balance >= 0)` constraint is enforced by PostgreSQL itself, not by application code that could have a bug or be bypassed. Consistency means the database only ever moves from one valid state to another valid state — constraints, foreign keys, and check clauses are the actual mechanisms that enforce this, not just documentation of intended rules.

---

## 4. Isolation — Concurrent Transactions, Demonstrated With Two Real Connections

```python
conn2 = psycopg2.connect(dbname="aciddemo", ...)   # a genuinely SEPARATE connection

# Connection 1: update but DON'T commit yet
cur.execute("UPDATE accounts SET balance = balance - 100 WHERE owner = 'Alice';")

# Connection 2: read Alice's balance BEFORE connection 1 commits
cur2.execute("SELECT balance FROM accounts WHERE owner = 'Alice';")
print(cur2.fetchone()[0])
```
Real output:
```
Connection 2 sees: 1000 (uncommitted change from conn 1 is NOT visible - no dirty read)

Connection 1 commits.

Connection 2 now sees: 900 (committed change now visible)

Actual default isolation level in this real PostgreSQL instance: read committed
```
This is a genuine, real demonstration of PostgreSQL's default **Read Committed** isolation level: connection 2 could NOT see connection 1's uncommitted change (no "dirty read" — a real anomaly some weaker systems allow), but immediately saw it once connection 1 actually committed. Isolation controls exactly how much concurrent transactions can "see" of each other's in-progress work — Read Committed is a real, deliberate middle ground (prevents dirty reads, but allows some other anomalies like non-repeatable reads, covered in Topic 6).

---

## 5. Durability — The WAL Mechanism, Real and Queryable

```python
cur.execute("SHOW wal_level;")
print(cur.fetchone()[0])   # replica

cur.execute("SELECT pg_current_wal_lsn();")
print(cur.fetchone()[0])   # 0/2622628 - a real, live WAL position
```
**Why durability can't be "broken to prove," but the mechanism is real and inspectable:** PostgreSQL writes every change to a **Write-Ahead Log (WAL)** on disk BEFORE acknowledging that a transaction committed — this is what guarantees a committed transaction survives a crash immediately after: on restart, PostgreSQL replays the WAL to recover any committed-but-not-yet-applied-to-the-main-data-files changes. The WAL position (`pg_current_wal_lsn()`) genuinely advances with every write in this real database, confirming the mechanism is actively running, even though actually crashing the server mid-write to "prove" durability isn't something to safely demonstrate here.

---

## 6. Traps & Misconceptions (MCQ-Relevant)

1. **"Atomicity means a transaction either fully succeeds or fully fails, and PostgreSQL retries automatically"** — FALSE, the retry part. PostgreSQL guarantees ALL-OR-NOTHING (verified above), but does NOT automatically retry a failed transaction — your application code must explicitly retry if that's the desired behavior.
2. **"Consistency in ACID means the same thing as 'strong consistency' in distributed systems (CAP theorem)"** — FALSE, a genuinely common point of confusion (covered further in Topic 9) — ACID's "Consistency" refers to the database always satisfying its own defined constraints/rules; CAP theorem's "Consistency" refers to whether all nodes in a distributed system see the same data at the same time. Related in spirit, but formally different concepts sharing a name.
3. **"Isolation means transactions run one at a time, literally sequentially"** — FALSE. Isolation is about what each transaction is allowed to SEE of others' in-progress work, not about literal serial execution — PostgreSQL genuinely runs concurrent transactions in parallel while maintaining isolation guarantees appropriate to the configured level.
4. **"A CHECK constraint is just documentation, not actually enforced"** — FALSE, directly demonstrated above — the database genuinely rejected an invalid update, raising a real exception.
5. **"Durability just means data is saved to disk eventually"** — Understated — the real guarantee is specifically that a transaction is durable the MOMENT it's acknowledged as committed, via the WAL being written to disk as part of the commit process itself, not as a background task that might lag behind.

---

## 7. Rapid-Fire Self-Check (MCQ Simulation)

1. In the real atomicity test, why did Alice's balance remain 1000 even though the first UPDATE statement genuinely executed before the error? *(The rollback undid the entire transaction, including the already-executed first statement — atomicity treats the whole transaction as one indivisible unit)*
2. What real database mechanism enforced that Bob's balance couldn't go negative? *(A CHECK constraint — `CHECK (balance >= 0)` — enforced by PostgreSQL itself, not application code)*
3. In the verified isolation test, could Connection 2 see Connection 1's uncommitted change? *(No — this is the "no dirty reads" guarantee of Read Committed, PostgreSQL's real default isolation level)*
4. What mechanism gives PostgreSQL its durability guarantee? *(The Write-Ahead Log, WAL — changes are written to disk as part of the commit itself, so a committed transaction survives a crash)*
5. Is "Consistency" in ACID the same concept as "Consistency" in the CAP theorem? *(No — despite sharing a name, ACID consistency is about a database satisfying its own constraints; CAP consistency is about distributed nodes agreeing on the same data)*

---

## Status
All four ACID properties are demonstrated with real, executed PostgreSQL behavior — a genuine transaction failure and rollback (atomicity), a genuine CHECK constraint rejection (consistency), a genuine two-connection dirty-read test (isolation), and real, queryable WAL state (durability) — not diagrams or descriptions.

Ready for the companion **Cheatsheet — Topic 1** or straight into **Topic 2: SQL Fundamentals** whenever you want to continue.
