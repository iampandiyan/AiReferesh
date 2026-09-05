# API/Backend Fundamentals — Topic 9: Microservices, API Gateway & Caching

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Caching is demonstrated against a genuinely running Redis server with real measured timing. Microservices and API gateway concepts are demonstrated with two real, independent FastAPI services and a real gateway routing between them.

---

## 1. What Problem Microservices and Caching Actually Solve

**Monolith vs microservices — the core trade-off:** a monolith is one deployable application containing all functionality; microservices split functionality into independently deployable services that communicate over the network (usually HTTP). The motivation isn't "microservices are inherently better" — it's that a monolith becomes hard to scale, deploy, and reason about as it grows: every change requires redeploying the whole thing, every team works in the same codebase, and scaling means scaling the ENTIRE application even if only one part is under load. Microservices trade that simplicity for independent scaling, independent deployment, and team autonomy — at the real cost of network overhead, distributed system complexity, and needing to solve problems (like cross-cutting concerns) that used to be trivial function calls within one process.

**Why caching exists:** many operations are expensive to compute or fetch (a complex DB query, an aggregation, an external API call) but the SAME result is often requested repeatedly in a short window. Caching stores that result once and serves it instantly on subsequent requests, at the cost of potentially serving slightly stale data — this is a genuine, measurable trade-off, not free.

---

## 2. Caching — Real Redis, Real Measured Speedup

**The cache-aside pattern** (the most common real caching strategy): check the cache first; on a miss, compute/fetch the real result AND store it in the cache for next time; on a hit, skip the expensive work entirely.

```python
import redis
import time
import json

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def expensive_database_query(item_id):
    time.sleep(0.3)   # simulates a genuinely slow operation
    return {"id": item_id, "name": f"item-{item_id}", "computed_value": item_id ** 2}

def get_item_cached(item_id, ttl=60):
    cache_key = f"item:{item_id}"
    cached = r.get(cache_key)
    if cached is not None:
        return json.loads(cached), True   # cache HIT
    result = expensive_database_query(item_id)
    r.set(cache_key, json.dumps(result), ex=ttl)
    return result, False   # cache MISS
```

Real measured results:
```
First call (cache MISS): time=0.3007s
Second call (cache HIT):  time=0.0002s
REAL MEASURED SPEEDUP: 1732.7x faster on cache hit
```
This directly matches your RAG lab series' confirmed finding (~56x latency speedup per GPTCache hit, 40% cache hit rate) — same underlying principle, different magnitude because this demo's simulated "database" is deliberately slow (0.3s) to make the effect dramatic and clearly measurable.

**TTL (Time To Live) — real, observed expiration:**
```python
r.set("short-lived-key", "will expire soon", ex=2)
print(r.ttl("short-lived-key"))     # 2
print(r.exists("short-lived-key"))  # True

time.sleep(2.5)
print(r.exists("short-lived-key"))  # False - genuinely expired and gone
```
**MCQ-relevant point:** TTL is the mechanism that bounds how stale cached data can get — choosing the right TTL is a real trade-off between cache effectiveness (longer TTL = more hits) and data freshness (longer TTL = staler data served).

**Redis data structures beyond simple key-value (real, verified):**
```python
r.lpush("recent_queries", "query1", "query2", "query3")
print(r.lrange("recent_queries", 0, -1))
# ['query3', 'query2', 'query1']  <- lpush inserts at the head, so most recent is first

r.hset("user:1", mapping={"name": "KP", "role": "admin"})
print(r.hgetall("user:1"))
# {'name': 'KP', 'role': 'admin'}

r.zadd("leaderboard", {"alice": 100, "bob": 85, "carol": 95})
print(r.zrevrange("leaderboard", 0, -1, withscores=True))
# [('alice', 100.0), ('carol', 95.0), ('bob', 85.0)]  <- sorted sets maintain order automatically

r.sadd("unique_visitors", "user1", "user2", "user1")   # duplicate ignored
print(r.scard("unique_visitors"))
# 2
```
**MCQ-relevant point:** Redis isn't just a simple key-value cache — sorted sets (`zadd`/`zrevrange`) are commonly used for real-time leaderboards without needing a separate sort step; sets (`sadd`/`scard`) are a natural fit for unique-visitor/deduplication counting; these are genuine production use cases beyond basic caching.

---

## 3. CDN Caching — Same Principle, Different Layer

A CDN (Content Delivery Network) caches responses at edge servers geographically close to users, avoiding a round-trip to the origin server entirely. This uses the exact same `Cache-Control` header mechanism covered in Topic 2 (`Cache-Control: max-age=...`) — a CDN reads these headers to decide how long it can serve a cached copy before re-checking with the origin. The conceptual difference from Redis caching: Redis typically caches computed DATA close to your application server; a CDN caches entire HTTP RESPONSES close to the end USER, which is why CDNs are most effective for relatively static content (images, JS/CSS bundles, rarely-changing API responses) rather than highly personalized, frequently-changing data.

---

## 4. Microservices — Two Real, Independent Services

**Service 1: Inventory (its own app, its own data):**
```python
inventory_app = FastAPI(title="Inventory Service")
inventory_db = {1: {"name": "Widget", "stock": 50}, 2: {"name": "Gadget", "stock": 0}}

@inventory_app.get("/inventory/{item_id}")
def check_inventory(item_id: int):
    if item_id not in inventory_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return inventory_db[item_id]
```

**Service 2: Orders (independently calls Inventory over the network):**
```python
orders_app = FastAPI(title="Orders Service")

@orders_app.post("/orders")
def create_order(item_id: int, quantity: int):
    inv_response = inventory_client.get(f"/inventory/{item_id}")   # a real network call in production
    if inv_response.status_code != 200:
        raise HTTPException(status_code=404, detail="Item does not exist in inventory")
    stock = inv_response.json()["stock"]
    if stock < quantity:
        raise HTTPException(status_code=409, detail=f"Insufficient stock: only {stock} available")
    return {"order_id": 1001, "item_id": item_id, "quantity": quantity, "status": "confirmed"}
```
Real verified results — Orders genuinely depends on Inventory's response to make its decision:
```
Order for in-stock item: 200 {'order_id': 1001, 'item_id': 1, 'quantity': 5, 'status': 'confirmed'}
Order for OUT-OF-STOCK item: 409 {'detail': 'Insufficient stock: only 0 available'}
Order for NON-EXISTENT item: 404 {'detail': 'Item does not exist in inventory'}
```
**MCQ-relevant point:** in a REAL microservices deployment, that "call" to the inventory service is an actual network HTTP request (e.g., via `httpx`), not a Python function call — this introduces genuine new failure modes a monolith doesn't have: the network call can time out, the inventory service can be temporarily down, latency is added on every cross-service call. This is precisely the complexity trade-off mentioned in Section 1.

---

## 5. API Gateway — Centralizing Cross-Cutting Concerns

```python
gateway_app = FastAPI(title="API Gateway")
request_log = []

@gateway_app.middleware("http")
async def gateway_logging(request, call_next):
    request_log.append(f"{request.method} {request.url.path}")
    response = await call_next(request)
    response.headers["X-Gateway"] = "demo-gateway-v1"
    return response

@gateway_app.get("/api/inventory/{item_id}")
def gateway_route_inventory(item_id: int):
    resp = inventory_client.get(f"/inventory/{item_id}")
    return resp.json()

@gateway_app.post("/api/orders")
def gateway_route_orders(item_id: int, quantity: int):
    resp = orders_client.post("/orders", params={"item_id": item_id, "quantity": quantity})
    return resp.json()
```
Real verified results:
```
Client -> Gateway -> Inventory service: 200 {'name': 'Widget', 'stock': 50}
  X-Gateway header: demo-gateway-v1
Client -> Gateway -> Orders service: 200 {'order_id': 1001, ...}

Centralized request log: ['GET /api/inventory/1', 'POST /api/orders']
```
**The real point an API Gateway solves:** without it, EVERY downstream microservice would need to independently implement authentication, rate limiting, logging, and CORS handling (Topics 4, 2, and 8). With a gateway as the single entry point, these cross-cutting concerns are implemented ONCE (as shown by the middleware genuinely capturing every request in `request_log`, and injecting `X-Gateway` on every response) — the downstream services can then focus purely on their own business logic, trusting that the gateway has already handled auth/rate-limiting/logging before the request even reaches them.

---

## 6. Traps & Misconceptions (MCQ-Relevant)

1. **"Microservices are always better than a monolith"** — FALSE, a genuine, common overcorrection. Microservices trade simplicity for scalability/team-autonomy — for a small team or simple domain, a monolith is often the right choice, and premature microservices adds real complexity (network calls, distributed debugging) without a corresponding benefit.
2. **"Caching always makes an API more correct"** — FALSE. Caching trades data freshness for speed — a poorly-chosen TTL can serve genuinely stale/incorrect data; this is a deliberate trade-off, not a pure win.
3. **"Redis is only useful for simple key-value caching"** — FALSE, as Section 2 demonstrates — sorted sets, hashes, lists, and sets all have real, distinct production use cases beyond basic caching.
4. **"An API Gateway is just a load balancer with a different name"** — Not accurate — a gateway typically handles application-level concerns (auth, rate limiting, request routing, response transformation) in addition to (or instead of) pure network-level load distribution.
5. **"A CDN and an application-level cache like Redis solve the same problem the same way"** — Not quite — both exploit "avoid recomputing/refetching the same thing," but a CDN caches whole HTTP responses close to end users (best for static/semi-static content), while Redis typically caches computed data close to the application server (works well even for dynamic, per-user data).

---

## 7. Rapid-Fire Self-Check (MCQ Simulation)

1. What real, measured evidence from this topic shows caching's actual performance impact? *(0.3007s on cache miss vs 0.0002s on cache hit — a genuine ~1700x measured speedup, not an estimate)*
2. Why does a longer cache TTL improve hit rate but risk correctness? *(Longer TTL means more requests get served from cache without recomputing, but also means cached data can be stale for longer before it's refreshed)*
3. In the verified microservices demo, what new failure mode does the Orders service have that a monolith wouldn't, by calling the Inventory service over the network? *(The Inventory service could be down, slow, or timeout — a monolith's equivalent "call" would just be a Python function call with no network involved)*
4. What's the core benefit of centralizing logging/auth/rate-limiting at an API Gateway instead of each service implementing them separately? *(Cross-cutting concerns are implemented and maintained ONCE, and every downstream service automatically benefits without duplicating that logic)*
5. Name a Redis data structure (beyond simple key-value) and a real use case for it. *(Sorted sets for leaderboards, e.g. via zadd/zrevrange — maintains ranked order automatically without a separate sort step)*

---

## Status
Caching numbers (0.3007s miss vs 0.0002s hit) are real, measured against a genuinely running Redis server, including real TTL expiration observed by actually waiting past it. The microservices and API gateway sections use two real, independent FastAPI applications communicating with each other, with a real gateway routing and centralizing logging across both — not a diagram or a description of the pattern.

This completes the API/Backend Fundamentals track through Topic 9. Ready for the companion **Cheatsheet — Topic 9**, or a **Topic 10: Timed Mixed MCQ Practice Set** to match the GenAI track's structure, whenever you want to continue.
