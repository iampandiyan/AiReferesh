# API/Backend Cheatsheet — Topic 9 (Redis Client Library)

**Companion to:** API_Topic9_Microservices_Gateway_Caching.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

The microservices/API gateway patterns in Topic 9 reuse FastAPI/middleware primitives already covered in the Topic 5 cheatsheet — not repeated here. This cheatsheet focuses on the Redis client.

---

## `redis.Redis` — Connection and Basic Key-Value

**Initialization:**
```python
import redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)
```
`decode_responses=True` makes Redis return Python strings instead of raw bytes — almost always what you want.

**Top methods:**
| Method | Explanation |
|---|---|
| `r.set(key, value, ex=seconds)` | Set a key, optionally with an expiration — the current, non-deprecated way to set with a TTL (replaces the deprecated `setex`) |
| `r.get(key)` | Returns the value, or `None` if the key doesn't exist |
| `r.ttl(key)` | Seconds remaining before expiration; `-1` if no expiration set, `-2` if the key doesn't exist |
| `r.exists(key)` | Returns 1 if the key exists, 0 if not |
| `r.delete(key)` | Remove a key |
| `r.expire(key, seconds)` | Set/update a TTL on an already-existing key |
| `r.incr(key)` | Atomically increment a counter — creates the key at 0 first if it doesn't exist |

**Verified example:**
```python
r.set("k", "v", ex=30)
print(r.get("k"), r.ttl("k"), r.exists("k"))   # v 30 1

r.delete("k")
print(r.exists("k"))   # 0

r.incr("counter"); r.incr("counter")
print(r.get("counter"))   # 2

r.expire("counter", 100)
print(r.ttl("counter"))   # 100
```

---

## Redis Data Structures — Beyond Key-Value

**Lists:**
```python
r.lpush("recent_queries", "query1", "query2", "query3")
r.lrange("recent_queries", 0, -1)   # ['query3', 'query2', 'query1'] - lpush inserts at head
```

**Hashes (a dict stored under one key):**
```python
r.hset("user:1", mapping={"name": "KP", "role": "admin"})
r.hgetall("user:1")   # {'name': 'KP', 'role': 'admin'}
```

**Sorted Sets (ranked data, e.g. leaderboards):**
```python
r.zadd("leaderboard", {"alice": 100, "bob": 85, "carol": 95})
r.zrevrange("leaderboard", 0, -1, withscores=True)
# [('alice', 100.0), ('carol', 95.0), ('bob', 85.0)] - highest score first
```

**Sets (unique membership):**
```python
r.sadd("unique_visitors", "user1", "user2", "user1")   # duplicate silently ignored
r.scard("unique_visitors")   # 2
```

---

## Status
Core key-value methods plus all four non-trivial Redis data structure types verified with real executed output.
