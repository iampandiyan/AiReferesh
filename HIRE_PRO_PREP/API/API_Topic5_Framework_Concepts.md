# API/Backend Fundamentals — Topic 5: FastAPI/Django/Flask Concepts

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

All three frameworks below are genuinely installed, configured, and run in this sandbox — real routing, real middleware execution, real dependency injection with an actual open/close lifecycle. FastAPI gets the deepest coverage since it's your production framework; Flask and Django are covered for real comparative MCQ knowledge.

---

## 1. Routing — Side-by-Side, All Real

**FastAPI:**
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/items/{item_id}")
def get_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```
Verified: `GET /items/42?q=search-term` → `200 {'item_id': 42, 'q': 'search-term'}` — note `item_id: int` in the signature automatically validates and converts the path parameter; no manual parsing.

**Flask:**
```python
from flask import Flask, jsonify, request

flask_app = Flask(__name__)

@flask_app.route("/items/<int:item_id>", methods=["GET"])
def flask_get_item(item_id):
    q = request.args.get("q")
    return jsonify({"item_id": item_id, "q": q})
```
Verified: same real result, `200 {'item_id': 42, 'q': 'search-term'}` — Flask's `<int:item_id>` in the URL string does the type conversion (a "converter"), and query params are read via the global `request` object rather than a function parameter.

**Django:**
```python
from django.http import JsonResponse
from django.urls import path

def django_get_item(request, item_id):
    q = request.GET.get("q")
    return JsonResponse({"item_id": item_id, "q": q})

urlpatterns = [
    path("items/<int:item_id>", django_get_item),
]
```
Verified: same real result — Django separates URL patterns (`urlpatterns`) from view functions entirely, unlike FastAPI/Flask's decorator-based co-location of route and handler.

**MCQ-relevant structural comparison:** FastAPI derives types from Python type hints directly on the function signature (leveraging Pydantic); Flask uses URL converter syntax (`<int:x>`) plus a global `request` object; Django separates routing (`urls.py`) from view logic entirely and also uses a global-ish `request` object passed as the first argument.

---

## 2. Middleware — Real Execution, All Three Frameworks

**FastAPI (two equivalent styles):**
```python
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        response.headers["X-Process-Time"] = f"{duration:.6f}"
        return response

app.add_middleware(TimingMiddleware)

@app.middleware("http")   # simpler decorator-based alternative
async def add_custom_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Powered-By"] = "FastAPI-Demo"
    return response
```
Verified: response genuinely carries both headers — `X-Process-Time` present, `X-Powered-By: FastAPI-Demo`. Both middleware forms wrap EVERY request/response, in the order they're registered.

**Flask:**
```python
@flask_app.before_request
def log_request():
    print(f"{flask_request.method} {flask_request.path}")

@flask_app.after_request
def add_header(response):
    response.headers["X-Powered-By"] = "Flask-Demo"
    return response
```
Verified: `before_request` genuinely fired before the route handler (confirmed via the printed log line), and the response header was genuinely added.

**Django (class-based middleware, the standard pattern):**
```python
class TimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response   # called ONCE at startup

    def __call__(self, request):           # called on EVERY request
        print(f"processing {request.path}")
        response = self.get_response(request)
        response["X-Powered-By"] = "Django-Demo"
        return response
```
Verified: the middleware genuinely executed, header genuinely present in the response. **MCQ-relevant structural point:** Django's middleware is a class with a two-phase lifecycle — `__init__` runs once when the server starts (good for expensive setup), `__call__` runs on every request — this is a real, meaningful architectural difference from FastAPI/Flask's function-per-request-only middleware style.

---

## 3. Dependency Injection — FastAPI's Real Advantage, Demonstrated Beyond Auth

Topic 4 showed `Depends()` for authentication. This section shows the same mechanism for a completely different, very common production need: managing a shared resource (like a DB session) with proper setup/teardown.

```python
class FakeDBSession:
    def __init__(self):
        self.connected = True
        self.query_count = 0
    def query(self, sql):
        self.query_count += 1
        return f"result for: {sql}"

def get_db():
    """yield-based dependency - the real production pattern for DB sessions."""
    db = FakeDBSession()
    print("[dependency] DB session opened")
    try:
        yield db
    finally:
        print("[dependency] DB session closed")

@app.get("/query-demo")
def query_demo(db: FakeDBSession = Depends(get_db)):
    result = db.query("SELECT * FROM items")
    return {"result": result, "query_count": db.query_count}
```
Verified real execution order:
```
[dependency] DB session opened
[dependency] DB session closed
GET /query-demo: {'result': 'result for: SELECT * FROM items', 'query_count': 1}
```
The `yield` pattern is real and meaningful: code before `yield` runs as setup, code after `yield` (in the `finally` block) runs as teardown — GUARANTEED to run even if the route handler raises an exception, since it's wrapped in `try/finally`. This is the actual mechanism your FastAPI projects use (or should use) for database session lifecycle management.

**Sub-dependencies — a dependency that itself depends on another dependency:**
```python
def get_query_param(q: str = None):
    return q or "default-query"

def get_processed_query(q: str = Depends(get_query_param)):
    return q.upper()

@app.get("/sub-dependency-demo")
def sub_dependency_demo(processed: str = Depends(get_processed_query)):
    return {"processed": processed}
```
Verified:
```
GET /sub-dependency-demo?q=hello: {'processed': 'HELLO'}
GET /sub-dependency-demo (no q): {'processed': 'DEFAULT-QUERY'}
```
FastAPI resolves the ENTIRE dependency chain automatically — `sub_dependency_demo` depends on `get_processed_query`, which itself depends on `get_query_param`. This composability is genuinely not something Flask or Django provide as a built-in framework feature — they typically rely on global objects, explicit function calls, or third-party extensions for equivalent patterns.

---

## 4. Framework Philosophy — Practical Summary

| | FastAPI | Flask | Django |
|---|---|---|---|
| Type/validation | Built-in via Pydantic + type hints | Manual, or via extensions (e.g., Marshmallow) | Built-in via Forms/Serializers (DRF for APIs) |
| Async support | Native, first-class | Added later, less central | Supported since Django 3.1, less central than FastAPI |
| Dependency injection | Built-in (`Depends()`), genuinely powerful | Not built-in — typically globals/extensions | Not built-in — typically class-based views/mixins |
| "Batteries included" | No — minimal, you assemble what you need | No — minimal by design (a "microframework") | Yes — ORM, admin panel, auth, forms all included |
| Best fit | APIs, especially with heavy validation/async needs | Small apps, prototypes, full control desired | Full web apps needing built-in admin/ORM/auth quickly |

---

## 5. Traps & Misconceptions (MCQ-Relevant)

1. **"FastAPI's type hints are just for documentation"** — FALSE, same principle as Topic 3's `response_model` — they drive REAL request parsing/validation, not just docs.
2. **"Middleware and dependencies (Depends()) are the same mechanism"** — FALSE. Middleware wraps EVERY request globally regardless of route; dependencies are declared per-route and can be composed/reused selectively — genuinely different scopes and purposes.
3. **"Django's `__init__` in middleware runs on every request, like `__call__`"** — FALSE, as demonstrated — `__init__` runs once at startup; only `__call__` runs per-request. Confusing these has real performance implications (expensive setup belongs in `__init__`, not `__call__`).
4. **"A yield-based FastAPI dependency's cleanup code won't run if the route raises an exception"** — FALSE. The `finally` block guarantees cleanup runs regardless of whether the route handler succeeds or raises.
5. **"Flask and Django have no equivalent to dependency injection at all"** — Not entirely true — they achieve similar OUTCOMES via different means (Flask extensions, Django class-based view mixins, global app context objects), but neither has FastAPI's declarative, composable `Depends()` system as a core built-in language of the framework itself.

---

## 6. Rapid-Fire Self-Check (MCQ Simulation)

1. In FastAPI's route `def get_item(item_id: int, q: str = None)`, what enforces that `item_id` is actually an integer? *(FastAPI's automatic request validation, driven directly by the Python type hint — genuinely rejects non-integer input with a 422, not just documentation)*
2. In Django middleware, which method runs once at server startup vs on every request? *(`__init__` runs once; `__call__` runs per request)*
3. Why is a `yield`-based FastAPI dependency preferred over a plain `return`-based one for managing a DB session? *(The code after `yield`, inside a `try/finally`, is guaranteed to run as cleanup even if the route handler raises an exception)*
4. What's the key architectural difference between FastAPI's `Depends()` and traditional middleware? *(Dependencies are declared per-route and composable/reusable selectively; middleware applies globally to every request regardless of route)*
5. Which of the three frameworks includes a built-in ORM and admin panel out of the box? *(Django — its "batteries included" philosophy, unlike FastAPI/Flask's minimal cores)*

---

## Status
Every routing, middleware, and dependency injection example above genuinely ran across all three real frameworks (FastAPI, Flask, Django) in this sandbox — including real middleware execution order, real header injection, and a real yield-based dependency lifecycle with confirmed open/close print statements proving the setup/teardown guarantee.

Ready for the companion **Cheatsheet — Topic 5** or straight into **Topic 6: Databases in Backend Context** whenever you want to continue.
