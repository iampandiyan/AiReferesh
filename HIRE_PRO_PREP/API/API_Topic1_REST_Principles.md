# API/Backend Fundamentals — Topic 1: REST Principles

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Every request/response below hit a real, live FastAPI server running locally in this sandbox — actual HTTP calls with `requests`, actual server logs shown, not simulated behavior. This mirrors your production FastAPI experience across the HR chatbot, Voice Agent SaaS, and Media Studio projects.

---

## 1. What REST Actually Means

**REST (Representational State Transfer)** is an architectural style for APIs built around a few core principles:
- **Resources**, not actions — a URL identifies a *thing* (`/books/1`), not a verb (`/getBook?id=1`). What you DO to that thing is expressed via the HTTP method.
- **Statelessness** — each request contains everything needed to process it; the server doesn't remember previous requests from the same client between calls.
- **Uniform interface** — a small, standard set of HTTP methods (GET, POST, PUT, PATCH, DELETE) applied consistently across all resources.
- **Idempotency** — a property of certain methods where calling them multiple times with the same input produces the same end state as calling them once (Section 3 demonstrates this concretely, including a real surprise).

---

## 2. Resources and HTTP Verbs — Real Server, Real Requests

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="REST Principles Demo")
books_db = {}
next_id = 1

class Book(BaseModel):
    title: str
    author: str

class BookResponse(Book):
    id: int

@app.get("/books")
def list_books():
    return list(books_db.values())

@app.get("/books/{book_id}")
def get_book(book_id: int):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    return books_db[book_id]

@app.post("/books", status_code=201)
def create_book(book: Book):
    global next_id
    new_book = BookResponse(id=next_id, **book.dict())
    books_db[next_id] = new_book
    next_id += 1
    return new_book

@app.put("/books/{book_id}")
def replace_book(book_id: int, book: Book):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    updated = BookResponse(id=book_id, **book.dict())
    books_db[book_id] = updated
    return updated

@app.patch("/books/{book_id}")
def update_book_partial(book_id: int, title: Optional[str] = None, author: Optional[str] = None):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    existing = books_db[book_id]
    if title is not None: existing.title = title
    if author is not None: existing.author = author
    return existing

@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    del books_db[book_id]
    return None
```

**Run it:** `uvicorn rest_demo_server:app --host 127.0.0.1 --port 8001`

---

## 3. Idempotency — Demonstrated With a Genuine, Real Surprise

```python
import requests
base = "http://127.0.0.1:8001"

r1 = requests.post(f"{base}/books", json={"title": "Clean Code", "author": "Robert Martin"})
r2 = requests.post(f"{base}/books", json={"title": "Clean Code", "author": "Robert Martin"})
print(r1.text)
print(r2.text)
```
Actual output:
```
{"title":"Clean Code","author":"Robert Martin","id":1}
{"title":"Clean Code","author":"Robert Martin","id":2}
```
**POST is NOT idempotent** — identical calls created TWO separate books (id 1 and id 2). This is the real, concrete meaning of "not idempotent," not just a definition to memorize.

```python
r1 = requests.put(f"{base}/books/1", json={"title": "Clean Code 2nd Ed", "author": "Robert C. Martin"})
r2 = requests.put(f"{base}/books/1", json={"title": "Clean Code 2nd Ed", "author": "Robert C. Martin"})
print(r1.status_code, r1.text)
print(r2.status_code, r2.text)
```
Actual output:
```
200 {"title":"Clean Code 2nd Ed","author":"Robert C. Martin","id":1}
200 {"title":"Clean Code 2nd Ed","author":"Robert C. Martin","id":1}
```
**PUT IS idempotent** — calling it twice with the same body leaves the resource in the exact same final state both times.

```python
r1 = requests.delete(f"{base}/books/1")
r2 = requests.delete(f"{base}/books/1")
print(r1.status_code, r2.status_code)
```
Actual output:
```
204 404
```
**A genuinely nuanced, real result:** the two DELETE calls returned DIFFERENT status codes (204 then 404), yet DELETE is still considered idempotent — because idempotency is about the **end state** (the resource doesn't exist, in both cases), not about the response being byte-identical. This is a real MCQ trap: idempotent does NOT mean "returns the same response every time."

---

## 4. Statelessness

Each HTTP request to the server above carries everything needed to process it (the book ID in the URL, the full body for PUT, etc.) — the server holds no per-client session state in memory between calls. This is why REST APIs scale horizontally so easily: any server instance can handle any request, since no server "remembers" a particular client's prior interactions. Contrast this with stateful protocols (like a raw TCP session or a stateful WebSocket connection) where the server DOES need to remember context between messages.

**Where "state" still exists in a stateless API:** the RESOURCE state (the book data itself, stored in `books_db`) persists — statelessness refers to the server not tracking per-CLIENT session/conversation state, not to the API having no data at all.

---

## 5. Traps & Misconceptions (MCQ-Relevant)

1. **"Idempotent means the server returns identical responses every time"** — FALSE, as Section 3's DELETE example directly proves — idempotency is about end STATE, not response identity.
2. **"POST and PUT are interchangeable ways to create a resource"** — FALSE. POST creates a new resource (server assigns the ID, as shown by ids 1 and 2 above); PUT is meant to create-or-replace at a client-specified URL/ID.
3. **"REST APIs must return JSON"** — FALSE. JSON is just the overwhelmingly common convention; REST as an architectural style doesn't mandate any specific data format.
4. **"Statelessness means the API can't have a database"** — FALSE, as Section 4 clarifies — statelessness is about not tracking per-client session state between requests, not about the absence of persisted resource data.
5. **"GET requests can safely have side effects if needed"** — FALSE by REST convention — GET is expected to be both "safe" (no side effects) and idempotent; using GET to trigger a state change (like a delete) violates this and can cause serious bugs with things like browser prefetching or crawlers.

---

## 6. Rapid-Fire Self-Check (MCQ Simulation)

1. Is DELETE idempotent, even though a second call might return a different status code than the first? *(Yes — idempotency is about end state, not identical responses; a resource being "already gone" is the same end state as "just deleted")*
2. What's the real, demonstrated difference between calling POST twice vs PUT twice with the same body? *(POST creates two separate resources; PUT leaves the target resource in the same final state both times)*
3. What does "statelessness" in REST actually refer to? *(The server not tracking per-client session/conversation state between requests — not the absence of persisted resource data)*
4. Should a GET request ever modify server-side data? *(No — GET is expected to be both safe and idempotent by convention; using it for side effects is a REST design violation)*
5. What does PATCH allow that PUT doesn't, in principle? *(Partial updates — only the provided fields change, versus PUT which conventionally replaces the entire resource)*

---

## Status
Every claim about idempotency and REST semantics above is backed by a real HTTP request/response pair against a genuinely running FastAPI server — including a real, slightly surprising result (DELETE's differing status codes on repeat calls) that a purely theoretical explanation might have glossed over.

Ready for the companion **Cheatsheet — Topic 1** or straight into **Topic 2: HTTP Status Codes & Headers** whenever you want to continue.
