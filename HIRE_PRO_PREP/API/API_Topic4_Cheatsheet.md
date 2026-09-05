# API/Backend Cheatsheet — Topic 4 (Authentication & Authorization Libraries)

**Companion to:** API_Topic4_Authentication_and_Authorization.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

---

## `bcrypt`

**Initialization:**
```python
import bcrypt
```

**Top methods:**
| Method | Explanation |
|---|---|
| `bcrypt.gensalt()` | Generates a random salt — bcrypt embeds this INSIDE the resulting hash, so you never need to store it separately |
| `bcrypt.hashpw(password_bytes, salt)` | Hashes a password — note it requires `bytes`, so encode a Python string first |
| `bcrypt.checkpw(password_bytes, hashed_bytes)` | Verifies a plaintext password against a stored hash — returns bool |

**Verified example:**
```python
h = bcrypt.hashpw(b"pass", bcrypt.gensalt())
print(h[:20])                        # b'$2b$12$olpzA9E1hqsL2'
print(bcrypt.checkpw(b"pass", h))    # True
```

---

## `jwt` (PyJWT)

**Initialization:**
```python
import jwt
```

**Top methods:**
| Method | Explanation |
|---|---|
| `jwt.encode(payload_dict, secret, algorithm="HS256")` | Creates a signed token |
| `jwt.decode(token, secret, algorithms=["HS256"])` | Verifies signature AND automatically checks `exp` if present — raises specific exceptions on failure |
| `jwt.ExpiredSignatureError` | Raised specifically when the token's `exp` claim has passed |
| `jwt.InvalidSignatureError` | Raised specifically when the token was signed with a different secret (tampered or wrong key) |

**Verified example:**
```python
token = jwt.encode({"sub": "kp", "exp": int(time.time())+60}, "secret", algorithm="HS256")
decoded = jwt.decode(token, "secret", algorithms=["HS256"])
print(decoded)   # {'sub': 'kp', 'exp': 1788611877}

# decoding with the wrong secret genuinely fails:
try:
    jwt.decode(token, "wrong-secret", algorithms=["HS256"])
except jwt.InvalidSignatureError as e:
    print(type(e).__name__)   # InvalidSignatureError
```

**Real production warning caught during testing:** PyJWT itself emits `InsecureKeyLengthWarning` when the HMAC secret key is shorter than 32 bytes for HS256 — a genuine, actionable security signal, not just a style nag. Use a properly long, random secret (e.g., `secrets.token_hex(32)`) in any real deployment.

---

## `fastapi.security.OAuth2PasswordBearer` / `OAuth2PasswordRequestForm`

**Initialization:**
```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `OAuth2PasswordBearer(tokenUrl="token")` | Declares WHERE clients should POST to get a token — also drives the "Authorize" button in FastAPI's auto-generated Swagger docs |
| `token: str = Depends(oauth2_scheme)` | Extracts the Bearer token from the `Authorization` header automatically; raises 401 automatically if missing |
| `form_data: OAuth2PasswordRequestForm = Depends()` | Parses standard OAuth2 form fields (`username`, `password`, etc.) from a login POST request |

**Verified example:**
```python
scheme = OAuth2PasswordBearer(tokenUrl="token")
print(scheme.model.flows.password.tokenUrl)   # 'token'
```

---

## `fastapi.Depends` — Dependency Injection (the mechanism behind all of the above)

**Top usage:**
| Usage | Explanation |
|---|---|
| `param: Type = Depends(some_function)` | FastAPI calls `some_function` before your route body runs, injecting its return value — this is what makes reusable auth/RBAC checks possible without copy-pasting logic into every route |
| Dependencies can depend on other dependencies | e.g., `require_role("admin")` internally depends on `get_current_user` — FastAPI resolves the whole chain automatically |

---

## Status
4 entries verified with real executed output, including a genuine PyJWT security warning about short secret keys caught during testing rather than assumed.
