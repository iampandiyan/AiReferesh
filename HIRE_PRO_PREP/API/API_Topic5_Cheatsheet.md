# API/Backend Cheatsheet — Topic 5 (FastAPI/Flask/Django Framework Primitives)

**Companion to:** API_Topic5_Framework_Concepts.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry (all reused directly from the main doc's verified runs)

---

## `starlette.middleware.base.BaseHTTPMiddleware` (FastAPI)

**Initialization:**
```python
from starlette.middleware.base import BaseHTTPMiddleware

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Custom"] = "value"
        return response

app.add_middleware(TimingMiddleware)
```

| Part | Explanation |
|---|---|
| `dispatch(self, request, call_next)` | Override this — `call_next(request)` runs the rest of the pipeline (other middleware + the route handler) |
| Code before `await call_next` | Runs BEFORE the route handler |
| Code after `await call_next` | Runs AFTER the route handler, can inspect/modify the response |

---

## `@app.middleware("http")` (FastAPI, simpler alternative)

```python
@app.middleware("http")
async def add_custom_header(request, call_next):
    response = await call_next(request)
    response.headers["X-Powered-By"] = "FastAPI-Demo"
    return response
```
Same underlying mechanism as `BaseHTTPMiddleware`, just decorator-based instead of class-based — verified to genuinely inject the header in the main doc.

---

## `fastapi.Depends` — yield-based (Resource Lifecycle)

```python
def get_db():
    db = FakeDBSession()
    try:
        yield db
    finally:
        db_cleanup_code_here()

@app.get("/query-demo")
def query_demo(db = Depends(get_db)):
    ...
```

| Part | Explanation |
|---|---|
| Code before `yield` | Setup — runs before the route handler |
| Code after `yield` (in `finally`) | Teardown — GUARANTEED to run even if the route raises an exception |
| Sub-dependencies | Any `Depends(...)` parameter can itself use `Depends(...)` — FastAPI resolves the whole chain |

---

## Flask `@app.before_request` / `@app.after_request`

```python
from flask import Flask, request

app = Flask(__name__)

@app.before_request
def log_request():
    print(request.method, request.path)

@app.after_request
def add_header(response):
    response.headers["X-Powered-By"] = "Flask-Demo"
    return response
```

| Decorator | Explanation |
|---|---|
| `@app.before_request` | Runs before EVERY route handler in the app |
| `@app.after_request` | Runs after every route handler; must accept and return the `response` object |
| `request` | Flask's global request object — read query params via `request.args.get(...)`, unlike FastAPI's function-parameter style |

---

## Flask Route with Type Converter

```python
@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    q = request.args.get("q")
    return jsonify({"item_id": item_id, "q": q})
```

| Part | Explanation |
|---|---|
| `<int:item_id>` | URL converter syntax — auto-converts the URL segment to `int` |
| `methods=["GET"]` | Explicit list of allowed HTTP methods for this route |

---

## Django Middleware (Class-Based, Two-Phase Lifecycle)

```python
class TimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response   # runs ONCE at server startup

    def __call__(self, request):           # runs on EVERY request
        response = self.get_response(request)
        response["X-Powered-By"] = "Django-Demo"
        return response
```

| Method | When it runs |
|---|---|
| `__init__(self, get_response)` | Once, when the server starts — put expensive one-time setup here |
| `__call__(self, request)` | Once per request — the actual per-request logic goes here |

**Registration** (in `settings.py`, or `settings.configure(MIDDLEWARE=[...])` for programmatic setup):
```python
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "myapp.middleware.TimingMiddleware",
]
```

---

## Django URL Routing (`urls.py`)

```python
from django.urls import path
from django.http import JsonResponse

def get_item(request, item_id):
    q = request.GET.get("q")
    return JsonResponse({"item_id": item_id, "q": q})

urlpatterns = [
    path("items/<int:item_id>", get_item),
]
```

| Part | Explanation |
|---|---|
| `urlpatterns` | The list Django scans to match incoming URLs to view functions |
| `path("items/<int:item_id>", get_item)` | `<int:item_id>` converts the URL segment; the view function receives `request` first, then matched URL params |
| `request.GET.get(...)` | Django's way to read query params — a dict-like object on the request |

---

## Status
7 entries, all directly reused from real, verified execution in the main Topic 5 document across FastAPI, Flask, and Django.
