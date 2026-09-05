# API/Backend Fundamentals — Topic 4: Authentication & Authorization

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Every hash, token, and access-control check below is real: genuine bcrypt hashing, genuine JWT signing/decoding with real expiration behavior, and genuine RBAC enforcement — verified end-to-end via `TestClient`.

---

## 1. Authentication vs Authorization — Not the Same Thing

**Authentication** answers "who are you?" — verifying identity (password check, token validation).
**Authorization** answers "what are you allowed to do?" — checking permissions/roles AFTER identity is established.

This maps directly to Topic 2's 401 vs 403 distinction: a failed authentication → 401; a successful authentication but insufficient permission → 403.

---

## 2. Password Hashing — Never Store Plaintext

```python
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())
```
Verified:
```python
hashed = hash_password("mysecret")
print(hashed[:30])   # $2b$12$yyMd2JwfPq2IIf5oCih4K.t...
print(verify_password("mysecret", hashed))    # True
print(verify_password("wrongpass", hashed))   # False
```
**Why bcrypt specifically:** it includes a built-in random salt (visible in the hash format itself) and is deliberately slow (configurable work factor via `gensalt()`), making brute-force attacks computationally expensive — unlike fast general-purpose hashes (MD5, SHA-256) which are wrong tools for password storage precisely because they're too fast.

---

## 3. API Key Authentication — Simple, Real

```python
API_KEYS = {"key-abc-123": "service-A", "key-xyz-789": "service-B"}

@app.get("/api-key-protected")
def api_key_protected(x_api_key: str = Header(default=None)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return {"message": f"Hello, {API_KEYS[x_api_key]}"}
```
Verified:
```
GET /api-key-protected (no key): 401, {"detail":"Invalid or missing API key"}
GET /api-key-protected (valid key): 200, {"message":"Hello, service-A"}
GET /api-key-protected (invalid key): 401, {"detail":"Invalid or missing API key"}
```
API keys are simple but have real limitations: no built-in expiration, no embedded claims (role/permissions), and if leaked, must be manually revoked and rotated — this is why they're typically used for service-to-service auth rather than end-user sessions.

---

## 4. JWT Creation and Verification — Real Signing, Real Decoding

```python
import jwt
import time

SECRET_KEY = "demo-secret-key-not-for-production"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_in_seconds: int = 3600):
    to_encode = data.copy()
    to_encode["exp"] = int(time.time()) + expires_in_seconds
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```
Verified — a real token, genuinely signed and decoded:
```python
token = create_access_token({"sub": "kp", "role": "admin"})
print(token[:50])
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJrc...

decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
print(decoded)
# {'sub': 'kp', 'role': 'admin', 'exp': 1788614105}
```
**MCQ-relevant structural fact:** a JWT has three dot-separated parts — header, payload, signature. The header and payload are just base64-encoded (NOT encrypted — anyone can decode and read them without the secret key). The signature is what's cryptographically protected, and it's what prevents tampering: change the payload without the secret key, and the signature won't match on verification. This is a very common MCQ trap: **JWTs are not encrypted by default, just signed.**

**Real expired-token behavior:**
```python
expired_token = create_access_token({"sub": "kp", "role": "admin"}, expires_in_seconds=-10)
# decode_access_token(expired_token) genuinely raises jwt.ExpiredSignatureError -> 401
```
Verified: `GET /me (expired token): status=401, {"detail":"Token has expired"}` — the `exp` claim and PyJWT's automatic expiration check are real, not just documented behavior.

---

## 5. OAuth2 Password Flow — Real FastAPI Pattern

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    username = payload.get("sub")
    user = fake_users_db.get(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.get("/me")
def read_current_user(current_user: dict = Depends(get_current_user)):
    return {"username": current_user["username"], "role": current_user["role"]}
```
Verified, full real login flow:
```python
r_fail = client.post("/token", data={"username": "kp", "password": "wrongpass"})
# 401 {"detail":"Incorrect username or password"}

r_ok = client.post("/token", data={"username": "kp", "password": "mysecret"})
# 200 {"access_token": "eyJ...", "token_type": "bearer"}

token = r_ok.json()["access_token"]
r_me = client.get("/me", headers={"Authorization": f"Bearer {token}"})
# 200 {"username":"kp","role":"admin"}

r_no_token = client.get("/me")
# 401 {"detail":"Not authenticated"}   <- FastAPI's OAuth2PasswordBearer generates this automatically

r_garbage = client.get("/me", headers={"Authorization": "Bearer garbage.token.here"})
# 401 {"detail":"Invalid token"}
```
**Key architectural point:** `Depends(get_current_user)` is FastAPI's dependency injection system — any route that needs an authenticated user just declares this dependency, and FastAPI handles extracting the token, calling `get_current_user`, and either injecting the resulting user object or short-circuiting with the 401 raised inside the dependency. This pattern is what lets auth logic live in ONE place instead of being copy-pasted into every protected route.

---

## 6. RBAC (Role-Based Access Control) — Real Enforcement

```python
def require_role(required_role: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise HTTPException(status_code=403, detail=f"Requires '{required_role}' role")
        return current_user
    return role_checker

@app.get("/admin-only")
def admin_only(user: dict = Depends(require_role("admin"))):
    return {"message": f"Welcome admin {user['username']}"}
```
Verified with two real users of different roles:
```python
admin_token = ...  # kp, role=admin
guest_token = ...  # guest_user, role=viewer

client.get("/admin-only", headers={"Authorization": f"Bearer {admin_token}"})
# 200 {"message":"Welcome admin kp"}

client.get("/admin-only", headers={"Authorization": f"Bearer {guest_token}"})
# 403 {"detail":"Requires 'admin' role"}

client.get("/me", headers={"Authorization": f"Bearer {guest_token}"})
# 200 {"username":"guest_user","role":"viewer"}  <- guest CAN access /me, just not /admin-only
```
`require_role(...)` is a **dependency factory** — a function that returns a dependency, letting you parameterize role requirements per-route (`require_role("admin")`, `require_role("editor")`, etc.) while reusing the same underlying `get_current_user` authentication check. This composability (auth dependency wrapped by an authorization dependency) is the real production pattern behind RBAC in FastAPI, not just a conceptual diagram.

---

## 7. Traps & Misconceptions (MCQ-Relevant)

1. **"JWTs are encrypted, so sensitive data is safe inside them"** — FALSE, a critical security misconception. JWT payloads are only base64-ENCODED (trivially reversible by anyone), not encrypted. Never put secrets/sensitive data directly in a JWT payload.
2. **"API keys and JWTs serve the same purpose"** — Not quite — API keys are typically static, long-lived, and carry no embedded claims; JWTs are typically short-lived, self-contained (carry claims like role/expiration), and don't require a database lookup to validate (just signature verification).
3. **"A failed login should return 403"** — FALSE, as verified above — a wrong username/password is an authentication failure (401), not an authorization failure.
4. **"Once a JWT is issued, there's no way to check if it's expired without hitting the database"** — FALSE, as demonstrated — expiration (`exp` claim) is checked locally during decoding, no database round-trip needed, which is precisely why JWTs are attractive for scalable stateless auth.
5. **"RBAC checks should happen before authentication"** — FALSE, order matters — you must establish WHO the user is (authentication) before you can meaningfully check WHAT they're allowed to do (authorization) — reflected directly in the dependency chain (`require_role` depends on `get_current_user`, not the other way around).

---

## 8. Rapid-Fire Self-Check (MCQ Simulation)

1. Why is bcrypt preferred over MD5/SHA-256 for password hashing? *(Bcrypt is deliberately slow and includes a built-in random salt, making brute-force attacks computationally expensive; MD5/SHA-256 are fast general-purpose hashes, wrong tools for this job)*
2. Are JWT payloads encrypted by default? *(No — only base64-encoded and cryptographically signed; anyone can decode and read the payload, but can't forge a valid signature without the secret key)*
3. What FastAPI mechanism lets authentication logic live in one place instead of being duplicated across every protected route? *(Dependency injection via `Depends()` — declaring a dependency like `get_current_user` on any route automatically runs that logic)*
4. In the verified RBAC demo, why could the guest/viewer token access `/me` but not `/admin-only`? *(`/me` only requires authentication (any valid user); `/admin-only` requires both authentication AND the specific "admin" role via the `require_role` dependency)*
5. What does the `exp` claim in a JWT control, and where is it checked? *(Token expiration time; verified locally during decoding via the JWT library, no database lookup required)*

---

## Status
Every authentication and authorization mechanism above is real, executed code: genuine bcrypt password hashing/verification, genuine JWT signing/decoding with real expiration enforcement, and genuine RBAC access control tested with two different real user roles producing correctly different outcomes (200 vs 403) against the same endpoint.

Ready for the companion **Cheatsheet — Topic 4** or straight into **Topic 5: FastAPI/Django/Flask Concepts** whenever you want to continue.
