# API/Backend Cheatsheet — Topic 2 (Status Codes & Headers Libraries)

**Companion to:** API_Topic2_Status_Codes_and_Headers.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

`requests` is already covered in the Topic 1 cheatsheet — not repeated here.

---

## `fastapi.responses.RedirectResponse`

**Initialization:**
```python
from fastapi.responses import RedirectResponse
RedirectResponse(url="/new-path")                    # defaults to 307, NOT 302
RedirectResponse(url="/new-path", status_code=301)    # explicit permanent redirect
```

**Top usage:**
| Usage | Explanation |
|---|---|
| Default (no `status_code`) | Returns **307 Temporary Redirect** — confirmed by testing, not the commonly-assumed 302 |
| `status_code=301` | Permanent redirect — clients/search engines may cache this long-term |
| `status_code=302` | Also valid to set explicitly if you specifically want classic "Found" semantics |

**Verified example:**
```python
r = RedirectResponse(url="/x", status_code=301)
print(r.status_code)   # 301
```

---

## `fastapi.Header`

**Initialization:**
```python
from fastapi import Header
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `param: str = Header(default=None)` | Declares a function parameter that FastAPI auto-extracts from an incoming request header — FastAPI converts the header name automatically (`user_agent` param reads the `User-Agent` header) |

**Verified example:**
```python
@app.get("/h")
def h(user_agent: str = Header(default=None)):
    return {"ua": user_agent}

# calling with headers={"User-Agent": "MyClient/1.0"} returns {"ua": "MyClient/1.0"}
```

---

## `fastapi.Response` (Manual Status/Headers Control)

**Initialization:**
```python
from fastapi import Response
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `response: Response` as a function parameter | FastAPI injects a mutable response object you can modify before returning |
| `response.status_code = 202` | Override the default status code |
| `response.headers["X-Custom"] = "value"` | Set a custom response header |
| **Caveat (real bug caught in Topic 2):** | This does NOT work if you then `raise HTTPException` — the exception builds its own response, discarding anything set here |

**Verified example:**
```python
@app.get("/resp")
def resp(response: Response):
    response.status_code = 202
    response.headers["X-Custom"] = "hello"
    return {"ok": True}

# result: status=202, headers['x-custom']='hello'
```

---

## `fastapi.HTTPException` — Correct Way to Set Headers on an Error Response

**Initialization:**
```python
from fastapi import HTTPException
raise HTTPException(status_code=429, detail="Too many requests", headers={"Retry-After": "10"})
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `headers=` argument | The CORRECT way to attach custom headers to an error response — passing them here (not via a separate `Response` object) is what actually works, per the real bug found and fixed in Topic 2 |

---

## `starlette.testclient.TestClient` — Testing Without a Real Running Server

**Initialization:**
```python
from starlette.testclient import TestClient
client = TestClient(app)
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `client.get(path, headers=...)` / `.post()` / etc. | Same interface as `requests`, but calls the FastAPI app directly in-process — no actual network socket, no server startup race conditions |
| When to use this vs `uvicorn` + `requests` | `TestClient` is ideal for quick verification/unit tests; a real running `uvicorn` server (Topics 1-2's main demos) is closer to production behavior and necessary for testing actual network behavior |

**Verified example:**
```python
client = TestClient(app)
r = client.get("/h", headers={"User-Agent": "MyClient/1.0"})
print(r.json())   # {'ua': 'MyClient/1.0'}
```

---

## `hashlib.md5` (ETag Generation)

**Verified example:**
```python
import hashlib
print(hashlib.md5(b"test content").hexdigest())   # 9473fdd0d880a43c21b7778d34872157
```
Used to fingerprint resource content for ETag-based caching (Topic 2, Section 4) — note `hashlib` needs bytes, not a string, hence `.encode()` when hashing a Python string.

---

## Status
6 entries verified with real executed output, including `TestClient` as a faster alternative to the full server-startup pattern used in the main topic docs.
