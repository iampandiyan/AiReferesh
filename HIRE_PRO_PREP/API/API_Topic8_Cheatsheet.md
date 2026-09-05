# API/Backend Cheatsheet — Topic 8 (API Security Libraries)

**Companion to:** API_Topic8_API_Security.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry (all reused directly from the main doc's real verified runs)

---

## Parameterized Queries (`psycopg2`, and the general pattern)

**The pattern (applies across virtually all DB drivers/ORMs, not just psycopg2):**
```python
# VULNERABLE - never do this
query = f"SELECT * FROM users WHERE username = '{username}'"
cur.execute(query)

# SAFE - values passed separately from SQL structure
query = "SELECT * FROM users WHERE username = %s"
cur.execute(query, (username,))
```

| Driver/ORM | Placeholder syntax |
|---|---|
| `psycopg2` (PostgreSQL) | `%s` |
| `sqlite3` | `?` |
| SQLAlchemy Core/ORM | `:name` or automatic via query builder methods (Topic 6) |

**Verified real proof (from the main doc):** identical malicious input (`' OR '1'='1`) succeeded in dumping user data against the string-concatenation version, and returned an empty result (correctly blocked) against the parameterized version — same database, same attack string, only the query construction method differed.

---

## `fastapi.middleware.cors.CORSMiddleware`

**Initialization:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trusted-frontend.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

**Top parameters:**
| Parameter | Explanation |
|---|---|
| `allow_origins` | List of origins allowed to make cross-origin requests — `["*"]` allows any origin (use cautiously) |
| `allow_methods` | Which HTTP methods are permitted cross-origin |
| `allow_headers` | Which request headers are permitted |
| `allow_credentials` | Whether cookies/auth headers are allowed cross-origin (not shown above — defaults to False) |

**Verified example:**
```python
r = client.get("/data", headers={"Origin": "https://trusted-frontend.com"})
print(r.headers.get("access-control-allow-origin"))   # https://trusted-frontend.com

r = client.get("/data", headers={"Origin": "https://evil-site.com"})
print(r.headers.get("access-control-allow-origin"))   # None - header omitted for untrusted origin
print(r.status_code)   # 200 - but data is still returned; browser is what blocks reading it
```

---

## `slowapi.Limiter` — Rate Limiting

**Initialization:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `key_func=get_remote_address` | Rate-limits per client IP by default — swap for a custom function to key on API key/user ID instead |
| `@limiter.limit("3/minute")` | Decorator applied per-route, sets the actual limit |
| `_rate_limit_exceeded_handler` | Pre-built handler that returns a proper 429 response when the limit is hit |

**Verified example:**
```python
@app.get("/limited")
@limiter.limit("3/minute")
def limited_route(request: Request):
    return {"message": "ok"}

# requests 1-3: 200 ok
# requests 4-5: 429 {"error":"Rate limit exceeded: 3 per 1 minute"}
```

---

## Status
3 entries verified with real executed output — including a genuine, successful SQL injection attack against a real database and its parameterized-query fix, both confirmed with identical attack strings.
