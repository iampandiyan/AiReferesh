# API/Backend Cheatsheet — Topic 7 (Async/Sync Concurrency Tools)

**Companion to:** API_Topic7_Async_vs_Sync.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

---

## `asyncio.sleep` vs `time.sleep` — The Core Distinction

**Usage:**
```python
import asyncio, time

await asyncio.sleep(1)   # non-blocking - yields to the event loop
time.sleep(1)             # blocking - freezes the entire thread
```

| Function | Explanation |
|---|---|
| `asyncio.sleep(seconds)` | Must be `await`-ed; pauses the current coroutine WITHOUT blocking the event loop — other coroutines keep running during the wait |
| `time.sleep(seconds)` | Blocks the entire thread — inside an `async def` route, this freezes the WHOLE event loop for everyone (the real bug demonstrated in Topic 7, Section 3, Scenario 4) |

---

## `asyncio.gather` — Run Multiple Coroutines Concurrently

**Initialization:**
```python
import asyncio
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `await asyncio.gather(coro1, coro2, coro3)` | Runs all given coroutines concurrently, waits for all to finish, returns results in order |

**Verified example:**
```python
async def demo():
    start = time.time()
    await asyncio.gather(asyncio.sleep(1), asyncio.sleep(1), asyncio.sleep(1))
    print(round(time.time()-start, 2))

asyncio.run(demo())
# 1.0  <- three 1-second sleeps ran concurrently, not sequentially (would be 3.0 otherwise)
```

---

## `concurrent.futures.ThreadPoolExecutor` — Used to Fire Real Concurrent Test Requests

**Initialization:**
```python
import concurrent.futures
executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
```

**Top methods:**
| Method | Explanation |
|---|---|
| `.submit(func, *args)` | Schedule a function call, returns a `Future` immediately (non-blocking) |
| `.map(func, iterable)` | Apply `func` to each item concurrently, returns results in order once all complete |
| `future.result()` | Block until that specific future's result is ready |

**Verified example (this is the exact tool used to fire concurrent HTTP requests in Topic 7's real measurements):**
```python
def task(n):
    time.sleep(1)
    return n * 2

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
    results = list(ex.map(task, [1, 2, 3]))
print(results)   # [2, 4, 6], completed in ~1.01s total (concurrent, not 3s sequential)
```

---

## FastAPI Route Declaration — Sync vs Async

| Declaration | Behavior |
|---|---|
| `def route():` | Plain sync function — Starlette automatically runs it in a background threadpool |
| `async def route():` | Coroutine — runs directly on the event loop; MUST only contain non-blocking (`await`-able) operations to stay safe |

**Rule of thumb, directly proven in Topic 7:** if unsure whether every operation inside a route is truly non-blocking, using plain `def` is SAFER than `async def` — Starlette's automatic threadpool offload protects you, whereas a blocking call inside `async def` silently stalls every concurrent request with no error raised.

---

## Status
3 entries verified with real executed output, directly matching the tools used in Topic 7's real concurrency measurements.
