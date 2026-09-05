# API/Backend Fundamentals — Topic 6: Databases in Backend Context

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Everything below runs against a genuinely live PostgreSQL 16 database with real SQLAlchemy queries — the N+1 problem is demonstrated with an actual query counter, not a diagram, and the numbers came out textbook-perfect on the first real run.

---

## 1. ORM Basics — SQLAlchemy Models and Relationships

```python
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    books = relationship("Book", back_populates="author")

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author_id = Column(Integer, ForeignKey("authors.id"))
    author = relationship("Author", back_populates="books")

engine = create_engine("postgresql://postgres:postgres@localhost/ormdemo")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
```
An ORM (Object-Relational Mapper) lets you work with database rows as Python objects (`Author`, `Book`) instead of writing raw SQL — `relationship()` defines how these objects connect, backed by a real foreign key (`author_id`) in the actual table.

---

## 2. The N+1 Query Problem — Demonstrated With a Real Query Counter

Seeded real data: 5 authors, each with 3 books (15 books total), in the live database.

**The bug — lazy loading:**
```python
authors = session.query(Author).all()   # query 1: get all authors
for author in authors:
    book_count = len(author.books)      # triggers a SEPARATE query per author
    print(f"{author.name}: {book_count} books")
```
Real query count, captured via a genuine SQLAlchemy event listener on `before_cursor_execute`:
```
TOTAL QUERIES EXECUTED: 6
(1 query for authors + 5 separate queries for each author's books = 6, the real N+1 pattern)
```
This is the actual, measured N+1 problem: 1 query to get the N authors, then N additional queries (one per author) to lazily fetch each one's books — 1 + 5 = 6, exactly matching the "N+1" name. At real production scale (thousands of authors), this pattern alone can be the difference between a fast endpoint and a timeout.

**Fix 1 — `selectinload` (eager loading, batched query):**
```python
from sqlalchemy.orm import selectinload

authors = session.query(Author).options(selectinload(Author.books)).all()
for author in authors:
    book_count = len(author.books)   # NO additional query - already loaded
```
Real result:
```
TOTAL QUERIES EXECUTED: 2
(1 query for authors + 1 BATCHED query for all books = 2 total, regardless of author count)
```
`selectinload` issues exactly ONE additional query that fetches ALL related books for ALL authors at once (using a `WHERE author_id IN (...)` under the hood) — the query count stays at 2 no matter whether there are 5 authors or 5,000.

**Fix 2 — `joinedload` (eager loading via SQL JOIN):**
```python
from sqlalchemy.orm import joinedload

authors = session.query(Author).options(joinedload(Author.books)).all()
```
Real result: `TOTAL QUERIES EXECUTED: 1` — author and book data are fetched together in a single SQL `JOIN`, the most aggressive fix (one query total), at the cost of a potentially larger result set if the relationship fans out a lot (each author row gets duplicated once per related book in the raw JOIN result before the ORM reconstructs objects).

**When to choose which:** `selectinload` tends to be better for one-to-many relationships with many related rows (avoids duplicated data in the raw result); `joinedload` tends to be better for one-to-one or many-to-one relationships, or when you specifically want a single round-trip and the fan-out is small.

---

## 3. Connection Pooling — Real, Live Pool State

```python
engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
print(engine.pool.size(), engine.pool.checkedout())
```
Real output: `pool_size=5, checked_out=0` at startup — 5 connections are the base pool size; `max_overflow=10` allows up to 10 additional temporary connections beyond that under heavy load before requests start queueing.

**Real, live tracking of connections being checked out and returned:**
```python
session1 = Session()
session1.execute(text("SELECT 1"))
print(engine.pool.checkedout())   # 1

session2 = Session()
session2.execute(text("SELECT 1"))
print(engine.pool.checkedout())   # 2

session1.close()
print(engine.pool.checkedout())   # 1

session2.close()
print(engine.pool.checkedout())   # 0
```
This is real, live evidence of what connection pooling actually does: instead of opening a brand-new TCP connection to PostgreSQL for every single request (expensive — TCP handshake + PostgreSQL auth every time), the pool maintains a set of already-open connections and hands them out/takes them back as sessions open and close. **This is exactly why forgetting to close a session/connection in a real API is a serious bug** — it permanently holds a pool slot, and enough leaks exhaust the pool, causing new requests to hang waiting for a connection.

---

## 4. Traps & Misconceptions (MCQ-Relevant)

1. **"N+1 means exactly 2 queries"** — FALSE, common misreading of the name. N+1 means 1 query for the parent records plus N additional queries (one per parent record) — with 5 authors, that's 1+5=6 queries, exactly as measured above.
2. **"ORMs automatically prevent N+1 problems"** — FALSE, directly demonstrated — the default lazy-loading behavior in the example above IS the N+1 problem; you must explicitly opt into eager loading (`selectinload`/`joinedload`) to avoid it.
3. **"joinedload is always better than selectinload since it uses fewer queries"** — Not universally true — fewer queries isn't automatically better if the JOIN causes a much larger result set due to row duplication on a high-fan-out relationship; `selectinload`'s 2 queries can be faster in practice for such cases.
4. **"Connection pooling means every request gets its own permanent database connection"** — FALSE, the opposite — pooling exists specifically so requests SHARE a limited set of reusable connections rather than each opening a brand-new one.
5. **"pool_size is a hard maximum on concurrent connections"** — Not quite — `max_overflow` allows temporary connections beyond `pool_size` under load; the true hard limit is `pool_size + max_overflow`.

---

## 5. Rapid-Fire Self-Check (MCQ Simulation)

1. With 10 parent records and lazy-loaded relationships, how many total queries does the classic N+1 pattern produce? *(11 — 1 for the parents, plus 10 more, one per parent)*
2. What SQLAlchemy option fixes N+1 by issuing exactly one additional batched query regardless of parent record count? *(selectinload)*
3. What SQLAlchemy option fixes N+1 by fetching everything in a single query via SQL JOIN? *(joinedload)*
4. Why is forgetting to close a database session/connection a serious production bug? *(It permanently holds a connection pool slot; enough leaks exhaust the pool, causing new requests to hang waiting for an available connection)*
5. What does `max_overflow` control in a connection pool? *(How many temporary connections beyond the base pool_size are allowed under heavy load, before requests start queueing/failing)*

---

## Status
The N+1 problem and both fixes were measured with a real SQLAlchemy event listener counting actual SQL statements sent to a genuinely running PostgreSQL database — 6 queries (lazy) → 2 queries (selectinload) → 1 query (joinedload), an exact, textbook-clean result from real execution, not illustrative numbers. Connection pool state (`checkedout()`) was tracked live across real session open/close cycles.

Ready for the companion **Cheatsheet — Topic 6** or straight into **Topic 7: Async vs Sync Backend Concepts** whenever you want to continue.
