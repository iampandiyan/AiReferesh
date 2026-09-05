# API/Backend Cheatsheet — Topic 3 (API Design Libraries)

**Companion to:** API_Topic3_API_Design.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

---

## `fastapi.APIRouter`

**Initialization:**
```python
from fastapi import APIRouter
router = APIRouter(prefix="/v1")
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `prefix="/v1"` | Every route defined on this router is automatically prefixed — the core building block for URL-path API versioning |
| `app.include_router(router)` | Registers all of the router's routes onto the main FastAPI app |
| Also supports `tags=[...]` | Groups routes together in the auto-generated OpenAPI docs |

**Verified example:**
```python
router = APIRouter(prefix="/v1")

@router.get("/ping")
def ping():
    return {"msg": "pong"}

app.include_router(router)
# GET /v1/ping -> {'msg': 'pong'}
```

---

## `fastapi.Query` — Query Parameter Constraints

**Initialization:**
```python
from fastapi import Query
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `Query(default=None)` | Declares an optional query param with a default |
| `Query(min_length=2, max_length=20)` | Enforces string length constraints, automatically validated |
| Violating a constraint | Returns 422, same as any other Pydantic-level validation failure |

**Verified example:**
```python
@app.get("/search")
def search(q: str = Query(min_length=2, max_length=20)):
    return {"q": q}

# ?q=ab -> 200
# ?q=a  -> 422 (too short)
```

---

## `pydantic.Field` — Model Field Constraints

**Initialization:**
```python
from pydantic import BaseModel, Field
```

**Top constraint keywords:**
| Keyword | Explanation |
|---|---|
| `gt=` / `ge=` / `lt=` / `le=` | Greater/less than (or equal) numeric constraints |
| `min_length=` / `max_length=` | String or list length constraints |
| `default=` | Default value if the field is omitted |

**Verified example:**
```python
class Item(BaseModel):
    name: str
    price: float = Field(gt=0, le=1000)
```

---

## `response_model` — Real Output Filtering, Not Just Documentation

**Top usage:**
| Usage | Explanation |
|---|---|
| `@app.post("/items", response_model=ItemOut)` | FastAPI validates the ACTUAL returned data against `ItemOut` and strips any fields not declared in it — genuinely changes the response, not just the docs |

**Verified example (real proof of stripping):**
```python
class ItemOut(BaseModel):
    name: str

@app.post("/items", response_model=ItemOut)
def create(item: Item):
    return {"name": item.name, "extra_field": "should be stripped"}

# actual response: {'name': 'X'}  <- extra_field is genuinely gone, not just hidden in docs
```

---

## `.model_dump()` — Current Pydantic V2 Serialization Method

**Verified example:**
```python
print(Item(name="a", price=5).model_dump())
# {'name': 'a', 'price': 5.0}
```
**Note:** `.dict()` still works but is deprecated and triggers a real warning (confirmed in Topic 3's main doc) — use `.model_dump()` in any current Pydantic V2 codebase.

---

## Status
5 entries verified with real executed output, including direct proof that `response_model` filters actual response data, not just OpenAPI documentation.
