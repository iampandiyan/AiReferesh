# API/Backend Cheatsheet — Topic 6 (SQLAlchemy ORM Libraries)

**Companion to:** API_Topic6_Databases_in_Backend.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry (reused directly from the main doc's real PostgreSQL run)

---

## `sqlalchemy.create_engine`

**Initialization:**
```python
from sqlalchemy import create_engine
engine = create_engine("postgresql://user:pass@localhost/dbname", pool_size=5, max_overflow=10)
```

**Top parameters:**
| Parameter | Explanation |
|---|---|
| `pool_size` | Base number of connections kept open and reused |
| `max_overflow` | Additional temporary connections allowed beyond `pool_size` under load |
| `echo=True` | Logs every SQL statement — useful for debugging, verified as an alternative to manual event listeners |

**Verified example:**
```python
print(engine.pool.size())        # 5
print(engine.pool.checkedout())  # 0 (at startup, before any session opens)
```

---

## `declarative_base`, `Column`, `relationship`

**Initialization:**
```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True)
    books = relationship("Book", back_populates="author")
```

| Part | Explanation |
|---|---|
| `Base.metadata.create_all(engine)` | Creates all defined tables in the real database if they don't exist |
| `relationship(...)` | Defines the Python-level link between related models — backed by the real `ForeignKey` column |
| `back_populates` | Keeps both sides of a relationship (`Author.books` and `Book.author`) in sync |

---

## `sessionmaker` and `Session`

**Initialization:**
```python
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()
```

**Top methods:**
| Method | Explanation |
|---|---|
| `session.query(Model)` | Start a query against a model/table |
| `.all()` | Execute and return all matching rows as objects |
| `session.add(obj)` | Stage a new object for insertion |
| `session.commit()` | Persist staged changes to the real database |
| `session.close()` | Return the connection to the pool — verified to genuinely decrement `checkedout()` |

**Verified example:**
```python
session1 = Session()
session1.execute(text("SELECT 1"))
print(engine.pool.checkedout())   # 1
session1.close()
print(engine.pool.checkedout())   # 0
```

---

## `selectinload` / `joinedload` — N+1 Fixes

**Initialization:**
```python
from sqlalchemy.orm import selectinload, joinedload
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `.options(selectinload(Author.books))` | Verified: reduces total queries from 6 to 2 for 5 authors — one batched extra query regardless of author count |
| `.options(joinedload(Author.books))` | Verified: reduces total queries from 6 to 1 — single SQL JOIN fetches everything at once |

**Verified example:**
```python
authors = session.query(Author).options(selectinload(Author.books)).all()
# TOTAL QUERIES: 2 (vs 6 without eager loading)
```

---

## `event.listens_for` — Real Query Counting/Debugging

**Initialization:**
```python
from sqlalchemy import event

query_log = []

@event.listens_for(engine, "before_cursor_execute")
def log_query(conn, cursor, statement, parameters, context, executemany):
    query_log.append(statement)
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `"before_cursor_execute"` | Fires on every actual SQL statement sent to the database — the exact mechanism used to prove the real N+1 query counts (6 → 2 → 1) in the main doc |
| Alternative for quick debugging | `create_engine(url, echo=True)` prints every SQL statement to stdout without needing a custom listener |

---

## Status
5 entries verified with real executed output against a genuinely running PostgreSQL database, all directly reused from the main Topic 6 verification run.
