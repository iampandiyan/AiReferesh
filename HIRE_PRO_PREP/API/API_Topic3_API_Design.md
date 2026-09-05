# API/Backend Fundamentals — Topic 3: API Design

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Every example below runs against a real FastAPI app via `TestClient`, with genuine responses shown — including a real Pydantic V2 deprecation warning caught and fixed during verification (`.dict()` → `.model_dump()`), which matters if your own codebase still uses the older syntax.

---

## 1. API Versioning — URL Path Strategy

```python
from fastapi import FastAPI, APIRouter

app = FastAPI()
v1_router = APIRouter(prefix="/v1")
v2_router = APIRouter(prefix="/v2")

@v1_router.get("/users/{user_id}")
def get_user_v1(user_id: int):
    """v1: flat response shape."""
    return {"id": user_id, "name": "KP", "email": "kp@example.com"}

@v2_router.get("/users/{user_id}")
def get_user_v2(user_id: int):
    """v2: nested response shape - a real breaking change between versions."""
    return {"id": user_id, "profile": {"name": "KP", "email": "kp@example.com"}}

app.include_router(v1_router)
app.include_router(v2_router)
```
Verified real responses:
```
GET /v1/users/1: {"id":1,"name":"KP","email":"kp@example.com"}
GET /v2/users/1: {"id":1,"profile":{"name":"KP","email":"kp@example.com"}}
```
**MCQ-relevant point:** URL path versioning (`/v1/`, `/v2/`) is explicit and cache-friendly (different URLs = different cache entries automatically), but means maintaining parallel route definitions — exactly what `APIRouter` with a `prefix` is designed to organize cleanly, as shown above.

---

## 2. API Versioning — Header-Based Strategy

```python
from fastapi import Header

@app.get("/users-header/{user_id}")
def get_user_header_versioned(user_id: int, api_version: str = Header(default="1")):
    if api_version == "2":
        return {"id": user_id, "profile": {"name": "KP", "email": "kp@example.com"}}
    return {"id": user_id, "name": "KP", "email": "kp@example.com"}
```
Verified:
```
GET /users-header/1 (no header, defaults v1): {"id":1,"name":"KP","email":"kp@example.com"}
GET /users-header/1 (Api-Version: 2): {"id":1,"profile":{"name":"KP","email":"kp@example.com"}}
```
**Trade-off vs URL path versioning:** the URL stays clean/stable (`/users-header/1` never changes), but the version isn't visible in browser history, isn't naturally cacheable per-version by URL-based caches/CDNs, and requires every client to remember to set the header correctly.

---

## 3. Pagination — Offset/Limit

```python
all_items = [{"id": i, "name": f"item-{i}"} for i in range(1, 101)]

@app.get("/items")
def list_items_paginated(offset: int = 0, limit: int = 10):
    page = all_items[offset:offset + limit]
    return {
        "items": page,
        "offset": offset,
        "limit": limit,
        "total": len(all_items),
        "has_more": offset + limit < len(all_items),
    }
```
Verified:
```
GET /items?offset=0&limit=5: 5 items returned, has_more=true
GET /items?offset=95&limit=10: items 96-100, has_more=false
```
**Real weakness of offset/limit (worth knowing, not just the syntax):** if items are inserted/deleted between page requests, offset-based pagination can skip or duplicate items — the "page 3" the client requests is defined by POSITION, which shifts as the underlying data changes.

---

## 4. Pagination — Cursor-Based

```python
@app.get("/items-cursor")
def list_items_cursor(cursor: int = None, limit: int = 10):
    start_idx = 0
    if cursor is not None:
        start_idx = next((i for i, item in enumerate(all_items) if item["id"] == cursor), 0) + 1
    page = all_items[start_idx:start_idx + limit]
    next_cursor = page[-1]["id"] if page and (start_idx + limit) < len(all_items) else None
    return {"items": page, "next_cursor": next_cursor}
```
Verified:
```python
r1 = client.get("/items-cursor", params={"limit": 3})
# {"items": [item-1, item-2, item-3], "next_cursor": 3}

r2 = client.get("/items-cursor", params={"cursor": 3, "limit": 3})
# {"items": [item-4, item-5, item-6], "next_cursor": 6}
```
Cursor-based pagination anchors to a specific ITEM (`cursor=3` means "after the item with id 3"), not a position — this avoids the skip/duplicate problem above, which is exactly why most large-scale production APIs (social media feeds, etc.) use cursors instead of offset/limit.

---

## 5. Filtering and Sorting via Query Parameters

```python
from typing import Optional
from fastapi import Query

@app.get("/products")
def list_products(
    category: Optional[str] = None,
    min_price: Optional[float] = Query(default=None),
    max_price: Optional[float] = Query(default=None),
    sort_by: str = "id",
    order: str = "asc",
):
    results = products
    if category:
        results = [p for p in results if p["category"] == category]
    if min_price is not None:
        results = [p for p in results if p["price"] >= min_price]
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]
    results = sorted(results, key=lambda p: p[sort_by], reverse=(order == "desc"))
    return {"results": results, "count": len(results)}
```
Verified:
```
GET /products?category=tools: 2 tools returned
GET /products?min_price=15&sort_by=price&order=desc:
  [{"name":"Hammer","price":24.99}, {"name":"Gadget","price":19.99}]
```
Multiple filters compose naturally as sequential list comprehensions here — in a real database-backed API, these would translate to `WHERE` clauses and an `ORDER BY`, ideally built with an ORM's query builder rather than string concatenation (which risks SQL injection — see Topic 8).

---

## 6. Request/Response Schema Separation — A Core Production Pattern

```python
from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    """Input schema - what the CLIENT sends. No id, no computed fields."""
    name: str
    price: float = Field(gt=0)
    category: str

class ProductOut(BaseModel):
    """Output schema - what the SERVER returns. Includes server-assigned fields."""
    id: int
    name: str
    price: float
    category: str
    price_with_tax: float

@app.post("/products", response_model=ProductOut)
def create_product(product: ProductCreate):
    new_id = max(p["id"] for p in products) + 1
    price_with_tax = round(product.price * 1.08, 2)
    return ProductOut(id=new_id, price_with_tax=price_with_tax, **product.model_dump())
```
**A real deprecation caught during verification:** the initial version used `product.dict()`, which triggered `PydanticDeprecatedSince20`. Pydantic V2 renamed this to `.model_dump()` — the code above reflects the current, non-deprecated call.

Verified:
```python
r = client.post("/products", json={"name": "Drill", "price": 49.99, "category": "tools"})
print(r.json())
# {"id":5,"name":"Drill","price":49.99,"category":"tools","price_with_tax":53.99}
```
Notice the client never sent `id` or `price_with_tax` — those are server-computed/assigned. Separating `ProductCreate` (input) from `ProductOut` (output) is the correct production pattern: it prevents clients from supplying fields they shouldn't control, and `response_model=ProductOut` gives FastAPI automatic response validation and accurate OpenAPI docs.

**Validation is real and enforced:**
```python
r = client.post("/products", json={"name": "Bad", "price": -5, "category": "tools"})
print(r.status_code, r.json())
# 422 {"detail":[{"type":"greater_than","loc":["body","price"],"msg":"Input should be greater than 0", ...}]}
```
`Field(gt=0)` genuinely rejects a negative price at the schema level, before any business logic runs.

---

## 7. Nested Schemas

```python
class Address(BaseModel):
    city: str
    country: str

class UserWithAddress(BaseModel):
    name: str
    address: Address

@app.post("/users-nested")
def create_user_nested(user: UserWithAddress):
    return user
```
Verified:
```python
r = client.post("/users-nested", json={"name": "KP", "address": {"city": "Chennai", "country": "India"}})
print(r.json())
# {"name":"KP","address":{"city":"Chennai","country":"India"}}
```
Pydantic validates the nested `Address` object recursively — an invalid or missing nested field produces a 422 with a `loc` path pointing into the nested structure (e.g., `["body", "address", "city"]`), same principle as the flat validation above.

---

## 8. Traps & Misconceptions (MCQ-Relevant)

1. **"Offset/limit and cursor-based pagination are interchangeable"** — FALSE. Offset/limit can skip or duplicate items if data changes between requests; cursor-based pagination anchors to a specific item and avoids this.
2. **"API versioning in the URL and in headers are equally cacheable"** — FALSE. URL-based versioning is naturally cache-friendly since different versions have different URLs; header-based versioning requires cache configuration aware of the header (`Vary` header), or caching breaks silently.
3. **"response_model is just documentation, it doesn't affect behavior"** — FALSE. FastAPI actually validates and filters the returned data against `response_model` — if your function accidentally returns extra fields not in the schema, they get stripped from the actual response.
4. **"Pydantic's `.dict()` method is still the current way to serialize a model"** — FALSE as of Pydantic V2 — `.model_dump()` is the current method; `.dict()` is deprecated and will be removed in V3, confirmed by a real warning during this doc's verification.
5. **"Query parameter filtering is inherently safe from injection risks"** — Not automatically — if filter values are ever interpolated directly into a raw SQL string instead of using parameterized queries/ORM methods, this reintroduces SQL injection risk (Topic 8) despite looking like "just filtering."

---

## 9. Rapid-Fire Self-Check (MCQ Simulation)

1. Why is cursor-based pagination generally preferred over offset/limit for high-traffic APIs with frequently changing data? *(Cursor-based pagination anchors to a specific item's position, avoiding the skip/duplicate problem that occurs when items are inserted/deleted between offset-based page requests)*
2. What's a real trade-off of header-based API versioning compared to URL-path versioning? *(Requires explicit cache configuration, e.g. a Vary header, since the URL alone doesn't distinguish versions for caches/CDNs)*
3. Why should a `Create` input schema and an `Out` output schema typically be separate Pydantic models? *(Prevents clients from supplying server-controlled fields like IDs or computed values, and lets response_model validate/filter what's actually returned)*
4. What is the current, non-deprecated Pydantic V2 method for converting a model instance to a dict? *(.model_dump(), replacing the deprecated .dict())*
5. Does `response_model` in FastAPI only affect API documentation, or does it change actual response behavior? *(It changes actual behavior — FastAPI validates and filters the real response data against the schema, stripping any fields not declared in the model)*

---

## Status
Every versioning strategy, pagination pattern, filter/sort combination, and schema example above ran against a real FastAPI app via `TestClient` — including a genuine Pydantic V2 deprecation warning (`.dict()`) caught during verification and fixed to reflect current production practice, not left in a doc meant to teach up-to-date patterns.

Ready for the companion **Cheatsheet — Topic 3** or straight into **Topic 4: Authentication & Authorization** whenever you want to continue.
