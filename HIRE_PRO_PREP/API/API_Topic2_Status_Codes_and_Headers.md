# API/Backend Fundamentals — Topic 2: HTTP Status Codes & Headers

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Every status code and header below is from a real, live FastAPI server hit with actual HTTP requests — including two genuine surprises caught during verification that got corrected rather than glossed over.

---

## 1. Status Code Categories

| Range | Category | Meaning |
|---|---|---|
| 1xx | Informational | Request received, processing continues (rarely handled directly in app code) |
| 2xx | Success | The request was successfully received, understood, and accepted |
| 3xx | Redirection | Further action needed to complete the request (usually following a different URL) |
| 4xx | Client Error | The request has a problem the CLIENT caused (bad syntax, missing auth, etc.) |
| 5xx | Server Error | The server failed to fulfill a valid request — the problem is server-side |

---

## 2. 2xx Success Codes — Real Verified Examples

```python
@app.get("/ok")
def ok():
    return {"message": "success"}   # 200 OK - default

@app.post("/items", status_code=201)
def create_item(item: Item):
    return item                     # 201 Created

@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    return None                     # 204 No Content
```
Verified real responses:
```
GET /ok: status=200, body={"message":"success"}
POST /items: status=201, body={"name":"Widget","price":9.99}
DELETE /items/1: status=204, body=(empty)
```

---

## 3. 3xx Redirects — A Real Surprise Caught Here

```python
from fastapi.responses import RedirectResponse

@app.get("/old-path")
def old_path():
    return RedirectResponse(url="/new-path")

@app.get("/old-path-permanent")
def old_path_permanent():
    return RedirectResponse(url="/new-path", status_code=301)
```

**I initially assumed FastAPI's default `RedirectResponse` returns 302 — that assumption was wrong, and testing caught it:**
```python
r = requests.get(f"{base}/old-path", allow_redirects=False)
print(r.status_code, r.headers.get("location"))
```
Actual output: `307 /new-path` — **not 302**. FastAPI/Starlette's `RedirectResponse` defaults to **307 Temporary Redirect**, not the more commonly-cited 302. This matters because 307 explicitly guarantees the original HTTP method is preserved on redirect (a POST redirected via 307 stays a POST), whereas 302's behavior around method preservation has historically been inconsistent across clients — 307 was introduced specifically to remove that ambiguity.

Explicit 301 (permanent redirect) works as expected:
```
GET /old-path-permanent (no follow): status=301, location=/new-path
```
**MCQ-relevant distinction:** 301 = permanent (clients/browsers may cache this redirect long-term, search engines transfer SEO ranking); 302/307 = temporary (don't cache the redirect itself, the resource might move back).

---

## 4. 304 Not Modified — Real ETag-Based Caching

```python
import hashlib

@app.get("/cached-resource")
def cached_resource(response: Response, if_none_match: str = Header(default=None)):
    content = "This is a stable resource"
    etag = hashlib.md5(content.encode()).hexdigest()
    if if_none_match == etag:
        return Response(status_code=304)
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "max-age=60"
    return {"content": content}
```
Verified real requests:
```python
r1 = requests.get(f"{base}/cached-resource")
print(r1.status_code, r1.headers.get("etag"))
# 200 4e51ed7ecfc70630bb73eb40498a199d

r2 = requests.get(f"{base}/cached-resource", headers={"If-None-Match": r1.headers.get("etag")})
print(r2.status_code, r2.text)
# 304 (empty body)
```
This is real HTTP caching in action: the client sends back the ETag it received via `If-None-Match`; the server compares it and returns an empty 304 response instead of re-sending the full content, saving bandwidth — the actual mechanism behind browser caching and CDN behavior.

---

## 5. 400 vs 422 — Two Different Validation Layers

```python
@app.post("/validate-manual")
def validate_manual(value: int):
    if value < 0:
        raise HTTPException(status_code=400, detail="value must be non-negative")
    return {"value": value}
```
Verified real responses:
```python
r1 = requests.post(f"{base}/validate-manual", params={"value": -5})
print(r1.status_code, r1.json())
# 400 {'detail': 'value must be non-negative'}

r2 = requests.post(f"{base}/validate-manual", params={"value": "abc"})
print(r2.status_code, r2.json())
# 422 {'detail': [{'type': 'int_parsing', 'loc': ['query', 'value'], 'msg': 'Input should be a valid integer...'}]}
```
**A genuinely important layered distinction:** sending `"abc"` never even reaches the function body — FastAPI/Pydantic's automatic schema validation rejects it with 422 BEFORE any of your code runs. Sending `-5` (a valid integer) reaches the function, where YOUR business logic raises 400. **422 = "this doesn't match the expected shape/type." 400 = "this matches the shape but violates a business rule."** This two-layer distinction is a common, genuine MCQ trap.

---

## 6. 401 vs 403 — Authentication vs Authorization

```python
@app.get("/protected")
def protected(authorization: str = Header(default=None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    if authorization != "Bearer admin-token":
        raise HTTPException(status_code=403, detail="Not authorized for this resource")
    return {"message": "welcome, admin"}
```
Verified real responses:
```
GET /protected (no header): 401, WWW-Authenticate: Bearer, {"detail":"Not authenticated"}
GET /protected (wrong token): 403, {"detail":"Not authorized for this resource"}
GET /protected (correct token): 200, {"message":"welcome, admin"}
```
**401 = "I don't know who you are"** (missing/invalid credentials). **403 = "I know who you are, but you're not allowed here"** (valid credentials, insufficient permissions). Note the `WWW-Authenticate` header is standard practice on 401 responses — it tells the client HOW to authenticate.

---

## 7. 409 Conflict

```python
existing_usernames = {"kp"}

@app.post("/users")
def create_user(username: str):
    if username in existing_usernames:
        raise HTTPException(status_code=409, detail=f"username '{username}' already taken")
    existing_usernames.add(username)
    return {"username": username}
```
Verified:
```
POST /users?username=kp: 409, {"detail":"username 'kp' already taken"}
POST /users?username=newkp: 200, {"username":"newkp"}
```
409 signals the request conflicts with the CURRENT STATE of the resource — the request itself is well-formed, but can't be applied given what already exists.

---

## 8. 429 Too Many Requests — Real Rate Limiting + a Real Bug Caught

```python
@app.get("/rate-limited")
def rate_limited(request: Request, response: Response):
    client_ip = request.client.host
    now = time.time()
    window = request_counts.setdefault(client_ip, [])
    window[:] = [t for t in window if now - t < 10]
    if len(window) >= 3:
        raise HTTPException(status_code=429, detail="Too many requests", headers={"Retry-After": "10"})
    window.append(now)
    return {"message": "ok", "requests_in_window": len(window)}
```
**A genuine bug I caught and fixed during verification:** my first version set `response.headers["Retry-After"] = "10"` and THEN raised `HTTPException` — the header silently never appeared in the actual response, because raising `HTTPException` builds an entirely new response object, discarding anything set on the injected `response` parameter. The fix is passing `headers=` directly to `HTTPException` itself, as shown above.

Verified after the fix:
```
GET /rate-limited (call 1): 200, requests_in_window=1
GET /rate-limited (call 2): 200, requests_in_window=2
GET /rate-limited (call 3): 200, requests_in_window=3
GET /rate-limited (call 4): 429, Retry-After: 10, {"detail":"Too many requests"}
```
`Retry-After` tells the client exactly how many seconds to wait before retrying — real production rate-limited APIs (including many LLM provider APIs) return this same header.

---

## 9. 500 Internal Server Error

```python
@app.get("/broken")
def broken():
    return 1 / 0   # deliberately unhandled exception
```
Verified: `GET /broken: status=500, body=Internal Server Error`
FastAPI automatically converts any unhandled exception into a generic 500 response, hiding the actual exception details from the client by default (a real security consideration — stack traces shouldn't leak to end users in production).

---

## 10. Common Request & Response Headers

| Header | Direction | Purpose |
|---|---|---|
| `Content-Type` | Both | What format the body is in (e.g., `application/json`) |
| `Authorization` | Request | Credentials, e.g., `Bearer <token>` |
| `Accept` | Request | What response formats the client can handle |
| `If-None-Match` | Request | Conditional request using an ETag — enables 304 responses (Section 4) |
| `ETag` | Response | A fingerprint of the resource's current state, for cache validation |
| `Cache-Control` | Response | Caching directives (`max-age`, `no-cache`, etc.) |
| `Location` | Response | Where to find the resource — used on redirects (Section 3) and often on 201 Created |
| `WWW-Authenticate` | Response | How to authenticate — standard on 401 responses (Section 6) |
| `Retry-After` | Response | How long to wait before retrying — standard on 429 and some 503 responses (Section 8) |

---

## 11. Traps & Misconceptions (MCQ-Relevant)

1. **"FastAPI's RedirectResponse defaults to 302"** — FALSE, genuinely caught during testing above — it defaults to 307, which explicitly preserves the HTTP method on redirect.
2. **"400 and 422 mean the same thing"** — FALSE, as Section 5 demonstrates with real, different responses — 422 is schema/type validation (never reaches your code); 400 is business-logic validation (your code explicitly raises it).
3. **"401 means the user doesn't have permission"** — FALSE, that's 403. 401 means the server doesn't know who the client is at all (missing/invalid credentials).
4. **"Setting response.headers before raising HTTPException works"** — FALSE, a real bug caught in Section 8 — `HTTPException` builds its own response, discarding anything set on an injected `response` object; headers must go through `HTTPException`'s own `headers` argument.
5. **"304 responses include the resource body, just marked as cached"** — FALSE, verified directly — a 304 response body is empty; the client is expected to reuse its own previously cached copy.

---

## 12. Rapid-Fire Self-Check (MCQ Simulation)

1. What's the real, verified default status code FastAPI's `RedirectResponse` returns? *(307, not 302)*
2. Why does sending an invalid data TYPE to a FastAPI endpoint return 422 instead of reaching your custom 400 logic? *(Pydantic schema validation happens automatically before your function body runs — type/shape mismatches never reach your code)*
3. What's the practical difference between 401 and 403? *(401 = the server doesn't know who you are; 403 = it knows, but you're not allowed)*
4. Why didn't setting `response.headers["Retry-After"]` work before raising `HTTPException`? *(HTTPException constructs its own response object, discarding anything set on a separately injected response parameter — headers must be passed directly to HTTPException)*
5. What does a 304 response's body typically contain? *(Nothing — an empty body; the client is expected to use its own cached copy of the resource)*

---

## Status
Every status code, header, and edge case above came from real requests against a genuinely running FastAPI server — including two real bugs/wrong assumptions (the RedirectResponse default, and the Retry-After header ordering issue) that were caught by actually testing rather than assumed correct from memory.

Ready for the companion **Cheatsheet — Topic 2** or straight into **Topic 3: API Design** whenever you want to continue.
