# Python DSA & Coding Fundamentals — Topic 1: Complexity, Core Idioms & Production Libraries

**Target: AI Talent Quest 2026 — HirePro Chain Assessment**
**Track: Pure Python** (Aptitude MCQ gate → 36-min Python coding test)
**Context: You're Java-strong, Python-for-AI — this doc is built for that transition, not from scratch**

All code below has been executed and verified — outputs are real, not invented.

---

## 1. Why This Matters For You Specifically

You already have the *engineering judgment* from 14 years of Java — correctness, edge cases, complexity reasoning. What's different in Python is:
- Syntax speed (you shouldn't be thinking about syntax during a 36-minute timed test)
- Which built-in library gives you O(1)/O(log n) behavior "for free" that you'd hand-roll in Java
- Idioms that read as "senior Python" vs "Java translated line-by-line into Python" — assessments and interviewers both notice the difference

---

## 2. Time Complexity — Python Built-ins Reference

| Structure | Operation | Complexity | Notes |
|---|---|---|---|
| `list` | index access `lst[i]` | O(1) | |
| `list` | append | O(1) amortized | |
| `list` | insert at front `lst.insert(0, x)` | O(n) | shifts everything |
| `list` | `in` (membership) | O(n) | linear scan |
| `list` | slicing `lst[a:b]` | O(k) | k = slice length, creates a copy |
| `dict` | get/set/delete | O(1) average | insertion-ordered since 3.7 |
| `set` | membership/add/remove | O(1) average | use for fast lookups instead of list |
| `deque` | append/appendleft/pop/popleft | O(1) | use instead of list for queue behavior |
| `heapq` | push/pop | O(log n) | min-heap only, built on a plain list |
| `sorted()` / `.sort()` | | O(n log n) | Timsort — stable, adaptive to partially sorted data |
| `bisect` (binary search) | search/insert | O(log n) | on already-sorted list |

**Interview-relevant fact:** `sorted()` and `.sort()` use Timsort, which is O(n) on already-sorted or nearly-sorted input, not O(n log n) — worth knowing if asked about best-case behavior.

---

## 3. Core Syntax — Speed Reference (Muscle Memory for the Timed Test)

```python
from collections import defaultdict, Counter, deque, OrderedDict
import heapq
import bisect
from itertools import combinations, permutations, product, accumulate
from functools import lru_cache, reduce
from typing import List, Dict, Optional, Tuple

# --- Grid / 2D array (avoid the shallow-copy trap) ---
grid = [[0] * cols for _ in range(rows)]

# --- Stack (just use list) ---
stack = []
stack.append(x)
stack.pop()
stack[-1]  # peek

# --- Queue (use deque, NOT list — list.pop(0) is O(n)) ---
q = deque()
q.append(x)      # enqueue
q.popleft()       # dequeue

# --- Min-heap ---
heap = []
heapq.heappush(heap, x)
heapq.heappop(heap)
heapq.heapify(existing_list)   # O(n), turns a list into a heap in place

# --- Max-heap (no built-in — negate values) ---
heapq.heappush(heap, -x)
top = -heapq.heappop(heap)

# --- Frequency counting ---
freq = Counter(iterable)          # one line, no manual loop
freq.most_common(k)               # top-k frequent elements

# --- Default dict (avoids KeyError / getOrDefault boilerplate) ---
graph = defaultdict(list)
graph[node].append(neighbor)

# --- Binary search on sorted list ---
idx = bisect.bisect_left(sorted_list, target)

# --- Memoization decorator (replaces manual memo dict in many cases) ---
@lru_cache(maxsize=None)
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

# --- Sorting with custom key ---
arr.sort(key=lambda x: x[1])
sorted(intervals, key=lambda x: (x[0], -x[1]))   # multi-key sort

# --- String building (avoid += in a loop) ---
parts = []
parts.append(piece)
result = ''.join(parts)

# --- Enumerate / zip (idiomatic indexing) ---
for i, val in enumerate(arr):
    ...
for a, b in zip(list1, list2):
    ...
```

---

## 4. Java → Python Mental Model Translation

Since you think in Java first, here's the direct mapping so you stop reaching for the wrong tool mid-test:

| Java | Python equivalent | Gotcha |
|---|---|---|
| `ArrayDeque` as stack | `list` with `.append()`/`.pop()` | no gotcha — simpler in Python |
| `ArrayDeque` as queue | `collections.deque` | never use plain `list.pop(0)` — O(n) |
| `HashMap` | `dict` | Python dict preserves insertion order (language guarantee); Java HashMap does not |
| `HashMap.getOrDefault()` | `dict.get(key, default)` or `defaultdict` | `defaultdict` avoids repeated boilerplate |
| `TreeMap` | no direct equivalent — `sorted(dict.items())` on demand, or `SortedDict` from `sortedcontainers` (3rd-party) | Python's stdlib has no built-in sorted-map |
| `PriorityQueue` | `heapq` | Python's is function-based, not object-based — `heapq.heappush(heap, x)` not `heap.push(x)` |
| `StringBuilder` | list + `''.join()` | strings are immutable in both languages |
| `Collections.sort(list, comparator)` | `list.sort(key=...)` | Python uses `key=`, not a full comparator function, in most cases |
| `Integer.MAX_VALUE` | `float('inf')` | Python ints have no fixed max — use `inf` for sentinel values |
| Static typing / generics | `typing` module (`List[int]`, `Optional[str]`) | optional, not enforced at runtime — for readability and IDE support only |

---

## 5. Production Libraries & Keywords Worth Knowing (Beyond Pure DSA)

Since this is a Python-for-AI transition and the assessment covers GenAI/API topics too, here are the libraries and terms that signal production fluency — some may show up as MCQ distractors or in the coding round itself:

**Core language / performance:**
- `dataclasses` — `@dataclass` decorator for clean data-holding classes, replaces Java POJOs/DTOs
- `typing` / `typing_extensions` — type hints, `Protocol`, `TypedDict`, `Generic` — Python's answer to Java generics/interfaces
- `functools.lru_cache` / `functools.cache` — decorator-based memoization
- `itertools` — `combinations`, `permutations`, `groupby`, `accumulate`, `chain` — common in coding-test shortcuts
- `enum.Enum` — Python's typed constants, direct equivalent of Java enums
- `contextlib` — `@contextmanager`, used for resource management (Python's `try-with-resources` equivalent)
- `asyncio` — async/await concurrency model (different from Java's thread-based concurrency you're used to)

**Data / numerical (relevant to AI-ML MCQs):**
- `numpy` — vectorized array operations; **know that a vectorized numpy operation is O(n) but with much lower constant factor than a Python for-loop** — a common "why is this faster" MCQ pattern
- `pandas` — DataFrame operations, `.groupby()`, `.apply()` vs vectorized `.loc`/`.iloc` performance difference
- `pydantic` — data validation via type hints, ubiquitous in modern Python APIs (you've already used this in your FastAPI projects)

**Web/API (you already have hands-on experience — just needs MCQ-framing):**
- `FastAPI` — async-first, Pydantic-based request/response validation, automatic OpenAPI docs
- `uvicorn`/`gunicorn` — ASGI/WSGI servers
- REST concepts: idempotency, status codes, statelessness — likely MCQ material given "API fundamentals" is an explicit topic

**GenAI/AI-ML (maps directly to your RAG lab work):**
- `LangChain` / `LangGraph` — orchestration, chains, agents, retrievers
- Embeddings, vector similarity (cosine similarity, L2 distance), vector stores (FAISS, pgvector)
- `transformers` (Hugging Face) — tokenizers, model loading patterns
- RAG-specific terms: chunking, retrieval, re-ranking, hallucination, grounding, context window

---

## 6. Verified Practice Problems (All Tested — Real Output Below)

### Problem 1: Two Sum (hashing pattern)
```python
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        complement = target - n
        if complement in seen:
            return [seen[complement], i]
        seen[n] = i
    return []

two_sum([2,7,11,15], 9)
```
**Verified output:** `[0, 1]`
**Complexity:** O(n) time, O(n) space — one pass, hash lookup instead of nested loop.

---

### Problem 2: Group Anagrams (hashing + sorting as key)
```python
from collections import defaultdict

def group_anagrams(strs):
    groups = defaultdict(list)
    for s in strs:
        key = ''.join(sorted(s))
        groups[key].append(s)
    return list(groups.values())

group_anagrams(["eat","tea","tan","ate","nat","bat"])
```
**Verified output:** `[['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']]`
**Complexity:** O(n · k log k) where k = max string length — sorting each string as the grouping key.

---

### Problem 3: Longest Substring Without Repeating Characters (sliding window)
```python
def longest_unique_substring(s):
    seen = {}
    left = 0
    max_len = 0
    for right, c in enumerate(s):
        if c in seen and seen[c] >= left:
            left = seen[c] + 1
        seen[c] = right
        max_len = max(max_len, right - left + 1)
    return max_len

longest_unique_substring("abcabcbb")
```
**Verified output:** `3` (the substring `"abc"`)
**Complexity:** O(n) time — classic sliding window, single pass with a dict tracking last-seen index.

---

### Problem 4: Kth Largest Element (heap pattern)
```python
import heapq

def kth_largest(nums, k):
    heap = []
    for n in nums:
        heapq.heappush(heap, n)
        if len(heap) > k:
            heapq.heappop(heap)
    return heap[0]

kth_largest([3,2,1,5,6,4], 2)
```
**Verified output:** `5`
**Complexity:** O(n log k) — maintain a min-heap of size k; the root is always the kth largest.

---

### Problem 5: Merge Intervals (sort + greedy)
```python
def merge_intervals(intervals):
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged

merge_intervals([[1,3],[2,6],[8,10],[15,18]])
```
**Verified output:** `[[1, 6], [8, 10], [15, 18]]`
**Complexity:** O(n log n) — dominated by the sort.

---

### Problem 6: BFS on a Graph (adjacency list + deque)
```python
from collections import deque

def bfs(graph, start):
    visited = {start}
    order = []
    q = deque([start])
    while q:
        node = q.popleft()
        order.append(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                q.append(neighbor)
    return order

g = {0:[1,2], 1:[0,3], 2:[0,3], 3:[1,2]}
bfs(g, 0)
```
**Verified output:** `[0, 1, 2, 3]`
**Complexity:** O(V + E) — every vertex and edge visited once.

---

### Problem 7: Top-K Elements via Max-Heap Trick
```python
import heapq

def top_k_max(nums, k=3):
    heap = [-n for n in nums]
    heapq.heapify(heap)
    result = []
    for _ in range(k):
        result.append(-heapq.heappop(heap))
    return result

top_k_max([5,1,9,3,7,2], 3)
```
**Verified output:** `[9, 7, 5]`
**Note:** Python's `heapq` is min-heap only — negating values is the standard idiom for max-heap behavior. This is a very common MCQ/coding-test trap for people coming from Java's `PriorityQueue` (which supports a comparator directly).

---

### Problem 8: Climbing Stairs — Memoized Recursion (DP pattern)
```python
def climb_stairs(n, memo=None):
    if memo is None:
        memo = {}
    if n <= 2:
        return n
    if n in memo:
        return memo[n]
    memo[n] = climb_stairs(n-1, memo) + climb_stairs(n-2, memo)
    return memo[n]

climb_stairs(10)
```
**Verified output:** `89`
**Note:** deliberately uses `memo=None` + initialize-inside pattern, not `memo={}` as a default argument — see the mutable-default-argument trap below.

---

### Problem 9: Anagram Check via Counter
```python
from collections import Counter

def is_anagram(s1, s2):
    return Counter(s1) == Counter(s2)

is_anagram("listen", "silent")
```
**Verified output:** `True`
**Complexity:** O(n) — `Counter` equality compares frequency dicts directly.

---

## 7. Python-Specific Traps to Actively Watch For (MCQ + Coding Test Both)

1. **Mutable default arguments** — `def f(x, cache={}):` reuses the same dict across ALL calls. Always use `cache=None` and initialize inside the function (see Problem 8).
2. **List slicing is not free** — `arr[1:]` is O(n) time and space. Repeated slicing inside a loop silently turns O(n) into O(n²).
3. **`is` vs `==`** — `is` checks identity. Small cached integers (-5 to 256) can make `is` appear to "work" for equality — never rely on it for value comparison.
4. **Late-binding closures in loops** — `[lambda: i for i in range(3)]` returns `2, 2, 2`, not `0, 1, 2`, because `i` is looked up at call time. Fix with a default argument: `lambda i=i: i`.
5. **`/` vs `//`** — `/` always returns a float. Use `//` for integer/floor division — easy to trip on in DP index math or midpoint calculations (`mid = (low + high) // 2`).
6. **Shallow copy of nested structures** — `matrix[:]` or `list(matrix)` only copies the outer list; inner lists remain shared references. Use `[row[:] for row in matrix]` or `copy.deepcopy()`.
7. **`list.pop(0)` is O(n)** — a very common accidental performance bug when someone treats a `list` as a queue instead of using `deque`.
8. **Dict/set iteration order and mutation** — modifying a dict/set while iterating over it raises `RuntimeError: dictionary changed size during iteration`. Iterate over a copy (`list(d.keys())`) if you need to mutate during iteration.

---

## 8. Rapid-Fire Self-Check (MCQ Simulation)

1. What does `heapq.heappop([3,1,2])` return if the list wasn't heapified first? *(Undefined/incorrect behavior — you must call `heapq.heapify()` first, or only build the heap via `heappush`)*
2. Time complexity of `x in my_set` vs `x in my_list` for n elements? *(O(1) average vs O(n))*
3. What's wrong with `def f(arr=[]): arr.append(1); return arr` called multiple times? *(Mutable default argument bug — the list persists and grows across calls)*
4. Fastest way to count character frequency in a string? *(`Counter(s)`)*
5. Why is `numpy` faster than a Python `for` loop for the same O(n) operation? *(Vectorized operations run in compiled C under the hood, avoiding per-element Python interpreter overhead — same Big-O, much smaller constant factor)*

---

## Status
This replaces the earlier Java+Python dual-track Topic 1 with a pure-Python version, deeper practice coverage, and production library context. All 9 practice problems verified with real terminal output above.

Ready for **Topic 2: Arrays & Strings (pure Python)** whenever you want to continue — same format: idioms → production keywords → verified practice problems → traps → rapid-fire MCQs.
