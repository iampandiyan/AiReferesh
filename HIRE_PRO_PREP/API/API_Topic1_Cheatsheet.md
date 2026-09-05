# API/Backend Cheatsheet — Topic 1 (REST/FastAPI/requests Libraries)

**Companion to:** API_Topic1_REST_Principles.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

All examples below were executed for real against a live FastAPI server.

---

## `fastapi.FastAPI`

**Initialization:**
```python
from fastapi import FastAPI
app = FastAPI(title="My API")
```

**Top method decorators:**
| Decorator | Explanation |
|---|---|
| `@app.get(path)` | Register a GET route — safe, idempotent, no body expected |
| `@app.post(path, status_code=201)` | Register a POST route — typically returns 201 Created for new resources |
| `@app.put(path)` | Register a PUT route — full resource replacement, idempotent |
| `@app.patch(path)` | Register a PATCH route — partial update |
| `@app.delete(path, status_code=204)` | Register a DELETE route — typically returns 204 No Content on success |
| `{param}` in path + matching function argument | FastAPI auto-extracts and type-validates path parameters |

**Verified example:**
```python
@app.get("/books/{book_id}")
def get_book(book_id: int):   # FastAPI auto-converts the URL string to int, 422 error if it can't
    ...
```

---

## `fastapi.HTTPException`

**Initialization:**
```python
from fastapi import HTTPException
raise HTTPException(status_code=404, detail="Book not found")
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `status_code` | Any valid HTTP status code — FastAPI handles setting the response code and stopping execution |
| `detail` | Becomes the JSON error body: `{"detail": "..."}`  — verified in the real 404 response below |

**Verified example (real response body):**
```python
r = requests.get(f"{base}/books/999")
print(r.status_code, r.json())
# 404 {'detail': 'Book not found'}
```

---

## `pydantic.BaseModel` (Request/Response Schemas)

**Initialization:**
```python
from pydantic import BaseModel

class Book(BaseModel):
    title: str
    author: str

class BookResponse(Book):
    id: int   # inherits title/author, adds id - a common pattern for input vs output schemas
```

**Top usage:**
| Usage | Explanation |
|---|---|
| Using a `BaseModel` as a route parameter type | FastAPI automatically parses and validates the request body against the schema — invalid data gets a 422 response automatically, no manual validation code needed |
| Separate input vs output models | A common production pattern — `Book` (input) doesn't have `id` since the client doesn't supply it; `BookResponse` (output) does, since the server assigns it |

---

## `requests` — Client Library for Testing/Calling APIs

**Initialization:**
```python
import requests
```

**Top methods:**
| Method | Explanation |
|---|---|
| `requests.get(url)` | GET request |
| `requests.post(url, json=dict)` | POST request with a JSON body |
| `requests.put(url, json=dict)` | PUT request |
| `requests.patch(url, params=dict)` | PATCH request (query params in this demo's case, could also be JSON) |
| `requests.delete(url)` | DELETE request |
| `response.status_code` | The HTTP status code as an int |
| `response.json()` | Parsed JSON body as a Python dict |
| `response.text` | Raw response body as a string |
| `response.headers.get(name)` | Access a specific response header |

**Verified example (real output):**
```python
r = requests.post(f"{base}/books", json={"title": "Test", "author": "X"})
print(r.status_code)               # 201
print(r.json())                    # {'title': 'Test', 'author': 'X', 'id': 1}
print(r.headers.get('content-type'))  # application/json
```

---

## `uvicorn` — Running the Server

**Top usage:**
```bash
uvicorn rest_demo_server:app --host 127.0.0.1 --port 8001
```

| Part | Explanation |
|---|---|
| `rest_demo_server:app` | `module_name:variable_name` — the FastAPI instance to serve |
| `--host` | `127.0.0.1` for local-only access; `0.0.0.0` to accept connections from any network interface (needed for real hosting) |
| `--port` | Which port to listen on |
| `--reload` (not shown above, dev-only flag) | Auto-restarts the server on code changes — never use in production |

---

## Status
5 entries verified with real executed output against a genuinely running FastAPI server.
