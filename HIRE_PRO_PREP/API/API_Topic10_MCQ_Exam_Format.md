# API/Backend Fundamentals — Topic 10: Timed Mixed MCQ Practice Set (Exam Format)

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Attempt all 20 questions first, without checking the answer key, to simulate real test conditions. Suggested pace: ~90 seconds/question. Answer key with explanations is at the end.

---

## Questions

**1.** Is DELETE idempotent, even if a second call returns a different status code (e.g. 404) than the first (e.g. 204)?
A. No — different status codes mean it's not idempotent
B. Yes — idempotency is about end state, not identical responses
C. Only if both calls return 204
D. DELETE is never idempotent

**2.** What's the real, demonstrated difference between calling POST twice vs PUT twice with the same request body?
A. They behave identically
B. POST created two separate resources; PUT left the resource in the same final state both times
C. PUT is never safe to call twice
D. POST is always idempotent, PUT never is

**3.** What is FastAPI's actual, verified default status code for `RedirectResponse` (with no explicit `status_code` argument)?
A. 302
B. 307
C. 301
D. 303

**4.** Why does sending a non-integer value to a FastAPI endpoint expecting an `int` return 422, even though the route has custom logic that would raise 400 for a bad value?
A. FastAPI has a bug
B. Pydantic schema validation happens automatically before the function body runs, rejecting type mismatches with 422 first
C. 400 and 422 are interchangeable, it's random
D. 422 only happens on POST requests

**5.** Why is cursor-based pagination generally preferred over offset/limit for frequently-changing datasets?
A. Cursor-based pagination is always faster to implement
B. It avoids the skip/duplicate problem that occurs when data changes between offset-based page requests
C. Offset/limit doesn't work with databases
D. There is no real difference, just naming preference

**6.** Does FastAPI's `response_model` parameter only affect documentation, or does it change the actual response data?
A. It only affects the auto-generated OpenAPI documentation
B. It changes the actual response — FastAPI validates and strips fields not declared in the schema
C. It has no effect unless combined with status_code
D. It only works with GET requests

**7.** Are JWT payloads encrypted by default?
A. Yes, fully encrypted end to end
B. No — only base64-encoded and signed; anyone can decode and read the payload
C. Only the header is encrypted
D. Encryption is optional and enabled by default

**8.** What FastAPI mechanism lets authentication logic live in one reusable place instead of being duplicated across every protected route?
A. Global variables
B. Dependency injection via Depends()
C. Copy-pasting the auth check into every route
D. Environment variables

**9.** In Django class-based middleware, which method runs once at server startup, and which runs on every incoming request?
A. `__call__` once at startup, `__init__` per request
B. `__init__` once at startup, `__call__` per request
C. Both run once at startup
D. Both run on every request

**10.** Why is a yield-based FastAPI dependency preferred over a plain return-based one for managing a database session?
A. It's faster to write
B. Code after `yield` (in a finally block) is guaranteed to run as cleanup, even if the route raises an exception
C. It avoids needing a database entirely
D. It's required by FastAPI, there's no alternative

**11.** With 10 parent records and lazy-loaded relationships, how many total SQL queries does the classic N+1 pattern produce?
A. 2
B. 11
C. 10
D. 1

**12.** Which SQLAlchemy loading option fixes N+1 by issuing exactly one additional BATCHED query, regardless of the number of parent records?
A. lazy=True
B. selectinload
C. eager=True
D. There is no fix, N+1 is unavoidable

**13.** In a real measured test, an `async def` route using `time.sleep()` produced the SAME slow "staircase" timing pattern as a fully synchronous, single-threaded Flask server. Why?
A. FastAPI doesn't actually support async def properly
B. time.sleep() blocks the entire event loop; async def routes run directly on the loop with no threadpool protection, unlike plain def routes
C. The server had too little RAM
D. It was a random fluke, not reproducible

**14.** Is async/await always beneficial for performance, even for CPU-bound work (heavy computation with no I/O waiting)?
A. Yes, always, for any kind of workload
B. No — async's benefit is specifically for I/O-bound work where the program is waiting; CPU-bound work gains no benefit
C. Only if using FastAPI specifically
D. Async is always slower than sync

**15.** In the real, verified SQL injection demonstration, why did parameterized queries actually prevent the attack rather than just making it harder?
A. They just escape quotes automatically, nothing more
B. The value and the SQL structure are sent as separate things to the database driver, so injected input is always treated as literal data, never executable SQL
C. They encrypt the query
D. Parameterized queries don't actually prevent injection, only reduce it

**16.** Does CORS provide any real protection against a non-browser client (like curl) making a request from an untrusted origin?
A. Yes, CORS blocks all cross-origin requests at the server
B. No — CORS is enforced by the browser's JavaScript engine; a direct request via curl bypasses it entirely, as verified by real data still being returned
C. Only if using HTTPS
D. curl requests are always blocked by firewalls

**17.** What's the core, real benefit of centralizing auth/rate-limiting/logging at an API Gateway instead of each microservice implementing them separately?
A. It makes services run faster automatically
B. Cross-cutting concerns like auth, rate limiting, and logging are implemented once and automatically apply to every routed service
C. It eliminates the need for a database
D. It removes the need for HTTPS

**18.** Why does choosing a longer cache TTL improve hit rate but risk data correctness?
A. Longer TTL has no downsides at all
B. Cached data can be stale for longer before it's refreshed, even after the real underlying data has changed
C. Longer TTL makes Redis crash
D. TTL doesn't actually affect correctness, only speed

**19.** Why might a codebase using an ORM still be vulnerable to SQL injection?
A. ORMs are always 100% immune to SQL injection no matter what
B. Raw SQL built via string concatenation bypasses the ORM's built-in protection entirely, reopening the same vulnerability
C. SQL injection only affects NoSQL databases
D. ORMs prevent injection by encrypting all queries

**20.** What's the practical difference between concurrency and parallelism?
A. They are exactly the same thing
B. Concurrency is interleaving progress on multiple tasks (possible on one core); parallelism is literally simultaneous execution (requires multiple cores)
C. Parallelism is always slower than concurrency
D. Concurrency requires multiple CPU cores, parallelism doesn't

---

## Scoring Guide

| Score | Assessment |
|---|---|
| 18-20 correct | Strong — you're ready for this section of the gate |
| 14-17 correct | Good foundation — review the specific topics you missed before the exam |
| Below 14 | Revisit the full topic docs for the missed areas, prioritizing whichever topics had multiple misses |

---

## Answer Key & Explanations

| # | Answer | Topic | Explanation |
|---|---|---|---|
| 1 | B | REST Principles | Idempotency is about end state, not identical responses — a real DELETE test returned 204 then 404, same end state both times. |
| 2 | B | REST Principles | Verified with real requests — POST created two separate resources; PUT left the same final state both times. |
| 3 | B | Status Codes & Headers | A real surprise caught in testing — FastAPI's RedirectResponse defaults to 307, not the commonly assumed 302. |
| 4 | B | Status Codes & Headers | Pydantic schema validation happens before the function body runs — type mismatches never reach custom business logic. |
| 5 | B | API Design | Cursor-based pagination anchors to a specific item, avoiding the skip/duplicate problem when data changes between page requests. |
| 6 | B | API Design | Verified directly — an undeclared extra field was genuinely stripped from the real response, not just hidden in docs. |
| 7 | B | Authentication & Authorization | JWT payloads are only base64-encoded (trivially reversible), not encrypted — only the signature is cryptographically protected. |
| 8 | B | Authentication & Authorization | FastAPI's Depends() dependency injection lets auth logic live in one place and be reused across routes. |
| 9 | B | Framework Concepts | Verified with real print statements — __init__ runs once at startup, __call__ runs per request. |
| 10 | B | Framework Concepts | Code in a finally block after yield is guaranteed to run as cleanup, even on an exception — verified directly. |
| 11 | B | Databases in Backend | N+1 = 1 query for parents + N queries (one per parent) = 1+10=11, matching the real measured 1+5=6 pattern for 5 authors. |
| 12 | B | Databases in Backend | selectinload verified to reduce 6 queries to exactly 2, regardless of parent record count. |
| 13 | B | Async vs Sync | time.sleep() blocks the whole event loop; async def routes get no automatic threadpool protection, unlike plain def routes — verified with real matching timing (5.01s both cases). |
| 14 | B | Async vs Sync | Async's benefit is specifically for I/O-bound waiting; CPU-bound work gains nothing from it. |
| 15 | B | API Security | Verified with a real attack — parameterized queries send the value separately from SQL structure, so injected input is always literal data, never executable SQL. |
| 16 | B | API Security | Verified directly — an untrusted-origin request still got real data back with 200; CORS is browser-enforced only. |
| 17 | B | Microservices/Gateway/Caching | Verified in a real gateway demo — cross-cutting concerns implemented once at the gateway apply automatically to every routed service. |
| 18 | B | Microservices/Gateway/Caching | Longer TTL means cached data can be stale for longer before refreshing — a real, deliberate freshness-vs-speed trade-off. |
| 19 | B | API Security / Databases | Raw SQL built via string concatenation bypasses the ORM's own protection, reopening the same vulnerability demonstrated in Topic 8. |
| 20 | B | Async vs Sync | Concurrency = interleaving on possibly one core; parallelism = literal simultaneous execution requiring multiple cores — async/await achieves concurrency, not parallelism. |

---

## Status
20 questions drawn directly from real, verified results across all 9 API/Backend Fundamentals topics — including a genuine SQL injection attack, real N+1 query counts, real measured async/sync timing, and real CORS/JWT behavior — not generic textbook trivia.

This completes the API/Backend Fundamentals track (Topics 1–10). Combined with the GenAI/AI-ML track (Topics 1–12), that's two of the four MCQ gatekeeper areas fully covered. Ready to move to **Database Fundamentals**, or back to the pending **DSA topics (3–10)**, whenever you want to continue.
