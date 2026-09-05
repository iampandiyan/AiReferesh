# API/Backend Fundamentals — Topic 8: API Security

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

This topic includes a genuinely working SQL injection attack against a real live PostgreSQL database — not a diagram, an actual attack that dumped user data including a real password, followed by proof that parameterized queries block it completely.

---

## 1. What API Security Is, and Why It Matters

An API is a program that accepts input from the outside world and acts on it — every piece of that input (query params, JSON bodies, headers, even the request's origin) is something an attacker can control and craft maliciously. API security is the discipline of never trusting that input by default, and building specific defenses against the well-known ways it gets abused: injecting malicious code into what should be plain data (SQL injection), impersonating a trusted source (CSRF/CORS misconfig), or simply overwhelming the service with volume (lack of rate limiting). Every mechanism in this topic exists because a real, well-documented attack pattern exists for it.

---

## 2. SQL Injection — A Genuine, Working Attack Against a Real Database

**The vulnerable code — raw string concatenation into SQL:**
```python
def vulnerable_login(username, password):
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cur.execute(query)
    return cur.fetchall()
```

**Normal login works as expected:**
```
Actual SQL sent: SELECT * FROM users WHERE username = 'kp' AND password = 'realpassword123'
Result: [(1, 'kp', 'realpassword123', True)]
```

**The actual attack — crafted password input:**
```python
malicious_password = "' OR '1'='1"
vulnerable_login("kp", malicious_password)
```
Real SQL that got sent to the real database:
```sql
SELECT * FROM users WHERE username = 'kp' AND password = '' OR '1'='1'
```
Real result:
```
Result: [(1, 'kp', 'realpassword123', True), (2, 'guest', 'guestpass', False)]
>>> ATTACK SUCCEEDED - logged in without knowing the real password!
```
The injected `OR '1'='1'` makes the WHERE clause true for EVERY row, regardless of the actual password — the attacker is now "logged in" as `kp` without ever knowing the real password `realpassword123`.

**Worse — dumping the entire table without knowing any valid username:**
```python
malicious_username = "' OR '1'='1' --"
vulnerable_login(malicious_username, "anything")
```
Real SQL sent:
```sql
SELECT * FROM users WHERE username = '' OR '1'='1' --' AND password = 'anything'
```
Real result: **both user rows returned**, including the admin account's real password — the `--` comments out the rest of the query (the password check), and `OR '1'='1'` again makes every row match.

**The fix — parameterized queries:**
```python
def safe_login(username, password):
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    cur.execute(query, (username, password))   # values passed SEPARATELY, never concatenated into the SQL string
    return cur.fetchall()
```
Real result running the EXACT SAME attack strings against the safe version:
```
Result: []
>>> ATTACK blocked correctly - no login
```
**Why this actually works:** with parameterized queries, the database driver sends the SQL structure and the values as SEPARATE things over the wire — the database treats `'` OR `'1'='1` as a literal string to search for in the password column (which doesn't exist), not as SQL syntax to execute. The attacker's input is never given the opportunity to become part of the query's logic.

---

## 3. CORS (Cross-Origin Resource Sharing) — Real Browser-Enforced Behavior

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trusted-frontend.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

**A genuinely important, real nuance most explanations skip:**
```python
r = client.get("/data", headers={"Origin": "https://evil-site.com"})
print(r.status_code)   # 200
print(r.text)           # {"data":"secret business data"}  <- the data IS returned!
```
**The server still returns the data with a 200 status, even for an untrusted origin.** CORS is NOT a server-side access control mechanism — it's a policy the SERVER communicates via headers (`Access-Control-Allow-Origin`) that the BROWSER then chooses to enforce, by blocking JavaScript running on `evil-site.com` from reading the response. If the request is made by something other than a browser (curl, a backend service, Postman), CORS provides zero protection — this is a genuinely common and dangerous misconception.

**Real preflight (OPTIONS) request — what browsers send before certain cross-origin requests:**
```python
r = client.options("/data", headers={
    "Origin": "https://trusted-frontend.com",
    "Access-Control-Request-Method": "GET",
})
print(r.status_code, r.headers.get("access-control-allow-methods"))
# 200, GET, POST

r_bad = client.options("/data", headers={
    "Origin": "https://evil-site.com",
    "Access-Control-Request-Method": "GET",
})
print(r_bad.status_code)
# 400
```
Unlike the actual GET request, the PREFLIGHT request from an untrusted origin genuinely gets rejected (400) by Starlette's CORS middleware — this is the mechanism that stops a real browser from even attempting certain cross-origin requests when the origin isn't allowed.

---

## 4. Rate Limiting — Real Enforcement

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/limited")
@limiter.limit("3/minute")
def limited_route(request: Request):
    return {"message": "ok"}
```
Real, measured enforcement across 5 rapid requests:
```
request 1: status=200, {"message":"ok"}
request 2: status=200, {"message":"ok"}
request 3: status=200, {"message":"ok"}
request 4: status=429, {"error":"Rate limit exceeded: 3 per 1 minute"}
request 5: status=429, {"error":"Rate limit exceeded: 3 per 1 minute"}
```
This directly matches Topic 2's 429 status code coverage — `slowapi` is a real, commonly-used FastAPI rate-limiting library, and `key_func=get_remote_address` means the limit is tracked per-client-IP by default (configurable to key on API key, user ID, etc. instead).

---

## 5. Input Validation — Connecting Back to Topic 3

Pydantic's automatic schema validation (Topic 3) is itself a real security control, not just a convenience feature — rejecting malformed/unexpected input at the API boundary (422 responses) prevents a large class of attacks that rely on the backend receiving data in an unexpected shape or type. Combined with parameterized queries (Section 2), this covers the two most foundational input-related defenses: validate the SHAPE of input (Pydantic), and never let the CONTENT of input become executable code (parameterized queries).

---

## 6. Traps & Misconceptions (MCQ-Relevant)

1. **"CORS prevents an attacker from ever getting the response data"** — FALSE, directly demonstrated — the server still returns the actual data with 200; CORS only stops a BROWSER's JavaScript from reading it, providing zero protection against non-browser clients like curl or a malicious backend service.
2. **"Using an ORM automatically prevents SQL injection"** — Not automatically — an ORM's high-level query methods (like Topic 6's `session.query()`) are safe by default, but dropping down to raw SQL execution within an ORM codebase (common for complex queries) reopens the exact same vulnerability demonstrated above if string concatenation is used.
3. **"Escaping quotes manually is a safe alternative to parameterized queries"** — FALSE / risky — manual escaping is error-prone and has a long history of being bypassed via encoding tricks; parameterized queries are the actual, reliable fix, not a defense-in-depth nice-to-have.
4. **"Rate limiting by IP address is foolproof"** — FALSE — IP-based limiting can be bypassed via rotating IPs/proxies, and can also incorrectly throttle many legitimate users sharing one IP (e.g., behind a corporate NAT) — real production systems often combine IP-based limiting with API-key or user-based limiting.
5. **"A 400 response to a preflight request means the actual request was blocked too"** — Not automatically true in every implementation, but in this verified CORS middleware behavior, a rejected preflight DOES prevent the browser from sending the real follow-up request — the actual GET endpoint itself, if hit directly (bypassing preflight, e.g. via curl), still responds normally, as shown in Section 3.

---

## 7. Rapid-Fire Self-Check (MCQ Simulation)

1. In the verified SQL injection attack, what did the injected `' OR '1'='1` actually do to the SQL query's logic? *(Made the WHERE clause evaluate to true for every row, since '1'='1' is always true, bypassing the password check entirely)*
2. Why do parameterized queries actually prevent SQL injection, rather than just making it harder? *(The value and the SQL structure are sent as separate things to the database driver — injected input is always treated as literal data to match against, never as executable SQL syntax)*
3. Does CORS provide any protection against a non-browser client like curl making a cross-origin-style request? *(No — CORS is enforced by the browser's JavaScript engine; a direct request via curl or any non-browser client bypasses it entirely, as verified by the untrusted-origin request still returning real data)*
4. What's a real limitation of IP-based rate limiting? *(Can be bypassed by rotating IPs/proxies, and can incorrectly throttle multiple legitimate users sharing one IP, e.g. behind a corporate NAT)*
5. Does using an ORM automatically guarantee protection from SQL injection? *(No — high-level ORM query methods are safe by default, but raw SQL execution within the same codebase reopens the same vulnerability if string concatenation is used instead of parameterization)*

---

## Status
The SQL injection attack in this document is real — genuinely executed against a live PostgreSQL database, successfully bypassing authentication and dumping user rows (including a real stored password) via crafted input, with the parameterized-query fix verified to block the identical attack strings completely. CORS and rate limiting behavior were verified with real HTTP requests through `TestClient`, including the important real nuance that CORS is browser-enforced, not server-enforced.

Ready for the companion **Cheatsheet — Topic 8** or straight into **Topic 9: Microservices, API Gateway & Caching** whenever you want to continue.
