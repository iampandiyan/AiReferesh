# Database Fundamentals — Topic 10: Timed Mixed MCQ Practice Set (Exam Format)

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Attempt all 20 questions first, without checking the answer key, to simulate real test conditions. Suggested pace: ~90 seconds/question. Answer key with explanations is at the end.

---

## Questions

**1.** In the real atomicity test, Alice's balance stayed at 1000 even though the first UPDATE statement genuinely executed before a later statement failed. Why?
A. PostgreSQL automatically retried the failed statement
B. The rollback undid the entire transaction, including the already-executed first statement — atomicity treats the whole transaction as one unit
C. The first UPDATE was never actually applied to begin with
D. Alice's balance was restored by a background process

**2.** Is "Consistency" in ACID the same concept as "Consistency" in the CAP theorem?
A. Yes, they are exactly the same concept
B. No — ACID Consistency means the database satisfies its own constraints; CAP Consistency means distributed nodes agree on the same data
C. Yes, but only for single-node databases
D. CAP Consistency is a stricter version of ACID Consistency

**3.** What does `SELECT name FROM employees WHERE department = NULL;` actually return?
A. All rows where department has any value
B. Zero rows, always — NULL comparisons with = are never true
C. An error
D. Only rows where department IS actually NULL

**4.** What's the real difference between WHERE and HAVING in a query that uses GROUP BY?
A. HAVING filters rows before grouping; WHERE filters after
B. WHERE filters individual rows before grouping; HAVING filters aggregated groups after grouping
C. They are interchangeable keywords for the same operation
D. WHERE only works with GROUP BY, HAVING works without it

**5.** With the SAME table order (employees, then departments), Heidi (an employee with no department) appeared in a LEFT JOIN result but was absent from a RIGHT JOIN result. Why?
A. It was a database bug
B. LEFT JOIN preserves all rows from the left table (employees); RIGHT JOIN preserves all rows from the right table (departments) instead
C. Heidi's data was corrupted
D. The two joins are supposed to produce identical results always

**6.** Which join type produces a full Cartesian product (every row of table A paired with every row of table B)?
A. INNER JOIN
B. CROSS JOIN
C. FULL OUTER JOIN
D. SELF JOIN

**7.** In the real update-anomaly demonstration on a denormalized orders table, what specific real inconsistency was reproduced?
A. The database crashed
B. An incomplete UPDATE left Bob with two different emails stored simultaneously, since his email was redundantly repeated across multiple order rows
C. A foreign key violation occurred
D. The table's primary key was duplicated

**8.** What specific rule does Third Normal Form (3NF) add beyond Second Normal Form (2NF)?
A. Every column must be atomic (1NF's rule, not 3NF's)
B. No transitive dependency — a non-key column can't depend on another non-key column
C. Composite keys are forbidden
D. Tables must have at least 3 columns

**9.** Why did a range query (>) on a hash-indexed column genuinely fall back to a full Sequential Scan in the real verified test?
A. The index was corrupted
B. Hash indexes only support equality lookups — hashing destroys ordering information, so range queries can't use them at all
C. The table was too small for any index to matter
D. PostgreSQL doesn't support hash indexes

**10.** In `EXPLAIN ANALYZE` output, what's the real difference between the `cost=` values and the `actual time=` values?
A. They are the same thing, just different formatting
B. cost is the planner's pre-execution estimate; actual time is the genuinely measured real execution time
C. cost is always higher than actual time
D. actual time is only shown when using EXPLAIN without ANALYZE

**11.** What real anomaly did the Read Committed isolation level allow (which Repeatable Read then genuinely prevented, using the same real scenario)?
A. Dirty read
B. Non-repeatable read
C. Phantom read
D. Lost update

**12.** What does PostgreSQL genuinely do when its deadlock detector finds a real circular wait between two transactions?
A. It aborts BOTH transactions to be safe
B. It picks one transaction as a "victim", aborts it with a deadlock error, and lets the other proceed normally
C. It pauses the entire database until an administrator intervenes
D. It silently ignores the deadlock and lets both transactions corrupt the data

**13.** In the real verified comparison, what was the actual different outcome between ON DELETE CASCADE and ON DELETE SET NULL when a parent row was deleted?
A. They produce identical results, just different syntax
B. CASCADE genuinely deletes the child rows too; SET NULL keeps the child rows but nulls their foreign key column
C. CASCADE only works with PRIMARY KEY, SET NULL only works with UNIQUE
D. SET NULL deletes MORE data than CASCADE

**14.** Can a column with a UNIQUE constraint (but not PRIMARY KEY) contain multiple NULL values?
A. No, UNIQUE also enforces NOT NULL like PRIMARY KEY does
B. Yes — verified directly, multiple rows can have NULL in a UNIQUE column since NULLs are never considered equal to each other
C. Only one NULL is allowed per table
D. It depends on the database engine, not a general SQL rule

**15.** With a real tie (two employees with the exact same salary), what's the verified difference between how RANK() and DENSE_RANK() number the next DISTINCT value after the tie?
A. RANK and DENSE_RANK always produce identical results
B. RANK skips the next number(s) after a tie (leaving a gap); DENSE_RANK continues with no gap
C. DENSE_RANK skips numbers, RANK does not
D. Neither function handles ties, both would error

**16.** What two parts does a `WITH RECURSIVE` CTE genuinely require to work?
A. Just a single SELECT statement with a LIMIT clause
B. A base case (starting rows) and a recursive case (joining the CTE to itself), combined with UNION ALL
C. A stored procedure written in PL/pgSQL
D. Multiple nested subqueries, one per level of recursion needed

**17.** Why couldn't Redis efficiently answer "find all products where ram_gb=16", the way PostgreSQL's JSONB + GIN index could?
A. Redis crashed when attempting the query
B. Redis has no native secondary index on a stored value's internal fields — it required manually scanning and parsing every key, genuinely O(n)
C. Redis doesn't support storing JSON at all
D. The query worked identically fast in Redis and PostgreSQL

**18.** In practice, what is the REAL trade-off CAP theorem forces during an actual network partition?
A. Between Consistency and Partition tolerance, since Availability is always guaranteed
B. Between Consistency and Availability, since Partition tolerance is effectively mandatory for real distributed systems
C. There is no real trade-off, all three can always be achieved simultaneously
D. Between Availability and Partition tolerance, since Consistency is always guaranteed

**19.** Why might a real, correctly-created index (verified with both a vector HNSW index and a JSONB GIN index in this series) genuinely NOT be used by the query planner?
A. Indexes are only used on tables with fewer than 3 columns
B. On small tables, a sequential scan can genuinely be cheaper than using the index — the planner's decision is cost-based, not automatic
C. An index only activates after 24 hours
D. This never actually happens in PostgreSQL

**20.** What's the real, distinct relationship between ACID's "Isolation" property and ACID's "Consistency" property?
A. They are the exact same ACID property, just described differently
B. Isolation controls what a transaction can see of OTHER concurrent transactions; Consistency ensures a transaction leaves the database satisfying its own constraints
C. Consistency only applies to single-user databases, Isolation only applies to multi-user ones
D. Isolation is a subset of the Consistency property

---

## Scoring Guide

| Score | Assessment |
|---|---|
| 18-20 correct | Strong — you're ready for this section of the gate |
| 14-17 correct | Good foundation — review the specific topics you missed before the exam |
| Below 14 | Revisit the full topic docs for the missed areas, prioritizing whichever topics had multiple misses |

---

## Answer Key & Explanations

| # | Answer | Topic | Explanation |
|---|---|---|---|
| 1 | B | ACID | Atomicity treats the whole transaction as one unit — a rollback undoes already-executed statements too. |
| 2 | B | ACID / CAP | Despite sharing a name, these are formally different concepts — one about a single DB's constraints, one about distributed node agreement. |
| 3 | B | SQL Fundamentals | NULL comparisons with = are never true under SQL's three-valued logic — IS NULL must be used instead. |
| 4 | B | SQL Fundamentals | WHERE runs before grouping; HAVING runs after — verified with genuinely different results from the same data. |
| 5 | B | Joins | LEFT JOIN preserves left-table rows; RIGHT JOIN preserves right-table rows — exact mirror-image results with the same table order. |
| 6 | B | Joins | CROSS JOIN has no join condition — pairs every row with every row, verified as 6×3=18. |
| 7 | B | Normalization | A real, reproduced update anomaly — an incomplete UPDATE left two different emails for the same person. |
| 8 | B | Normalization | 3NF specifically forbids transitive dependencies between non-key columns. |
| 9 | B | Indexing | Hash indexes destroy ordering information — structurally cannot support range queries, verified with a real Seq Scan fallback. |
| 10 | B | Indexing | cost is the planner's pre-execution estimate; actual time is genuinely measured real execution time. |
| 11 | B | Transactions/Isolation | Non-repeatable read — verified with the same query returning different results within one Read Committed transaction. |
| 12 | B | Transactions/Locking | PostgreSQL picks one transaction as a "victim" and aborts it, letting the other proceed — verified with a real live deadlock. |
| 13 | B | Keys & Constraints | CASCADE genuinely deletes child rows; SET NULL keeps them with a nulled FK — verified with real before/after data. |
| 14 | B | Keys & Constraints | UNIQUE genuinely allows multiple NULLs — verified with two separate successful NULL inserts. |
| 15 | B | Aggregates/Window Functions | RANK skips numbers after a tie; DENSE_RANK doesn't — verified with a real salary tie. |
| 16 | B | Aggregates/CTEs | A base case plus a recursive case joined via UNION ALL — verified with a real multi-level org chart traversal. |
| 17 | B | NoSQL vs SQL | Redis has no native secondary index on value internals — verified as requiring a real full key scan. |
| 18 | B | NoSQL/CAP | Partition tolerance is effectively mandatory, so the real trade-off is Consistency vs Availability. |
| 19 | B | Indexing/NoSQL | Verified twice in this series — the planner's index-usage decision is cost-based, not automatic. |
| 20 | B | ACID | Isolation governs visibility of concurrent transactions; Consistency governs constraint satisfaction — two distinct, verified ACID properties. |

---

## Status
20 questions drawn directly from real, verified results across all 9 Database Fundamentals topics — a genuine deadlock, real ACID rollback, real join edge cases, real index-skip behavior, and real constraint enforcement — not generic textbook trivia.

This completes all three MCQ gatekeeper tracks covered so far: GenAI/AI-ML (12 topics), API/Backend Fundamentals (10 topics), and Database Fundamentals (10 topics). The only remaining piece from the original plan is the DSA track (Topics 3–10 still pending, after Topics 1–2 completed earlier). Ready to continue there, or revisit any topic across the three completed tracks.
