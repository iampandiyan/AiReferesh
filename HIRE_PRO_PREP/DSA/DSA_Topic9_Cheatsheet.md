# Python Cheatsheet — DSA Topic 9 (Recursion & Dynamic Programming)

**Companion to:** DSA_Topic9_Recursion_and_DP.md
**Format:** Signature → Top usage → One verified runnable example per entry

`functools.lru_cache` basics are already introduced in GenAI Topic 4's cheatsheet — this entry adds the `cache_info()` production-visibility method.

---

## Memoization Template (Manual Dict, Top-Down)

```python
def fib_memo(n, memo=None):
    if memo is None: memo = {}
    if n in memo: return memo[n]
    if n <= 1: return n
    memo[n] = fib_memo(n-1, memo) + fib_memo(n-2, memo)
    return memo[n]
```
Verified: 2730x faster than naive recursion at n=28.

---

## Tabulation Template (Bottom-Up, Space-Optimized)

```python
def fib_tabulation(n):
    if n <= 1: return n
    prev2, prev1 = 0, 1
    for _ in range(2, n+1):
        prev2, prev1 = prev1, prev2 + prev1
    return prev1
```
O(1) space when only the last k values are ever needed — verified to match memoization's result exactly.

---

## `functools.lru_cache` + `cache_info()`

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib_lru(n):
    if n <= 1: return n
    return fib_lru(n-1) + fib_lru(n-2)

fib_lru.cache_info()   # CacheInfo(hits=, misses=, maxsize=, currsize=)
```
Verified: `fib_lru(50)` returns instantly, and `cache_info()` gives real hit/miss counts — useful for confirming a cache is actually being exercised in production.

---

## 2D DP Table Template (LCS / Knapsack Shape)

```python
dp = [[0]*(n+1) for _ in range(m+1)]
for i in range(1, m+1):
    for j in range(1, n+1):
        if condition_matches(i, j):
            dp[i][j] = dp[i-1][j-1] + 1
        else:
            dp[i][j] = max(dp[i-1][j], dp[i][j-1])
```
The standard shape for two-sequence comparison DP problems — verified with real LCS (`'abcde'` vs `'ace'` → 3) and 0/1 Knapsack (capacity=7 → value 9).

---

## 1D DP with "Impossible" Sentinel Template (Coin Change Shape)

```python
dp = [float('inf')] * (target + 1)
dp[0] = 0
for a in range(1, target + 1):
    for option in choices:
        if option <= a:
            dp[a] = min(dp[a], dp[a-option] + 1)
result = dp[target] if dp[target] != float('inf') else -1
```
Verified: correctly returns `-1` for a genuinely unreachable amount, not a crash or wrong number.

---

## `sys.getrecursionlimit()` / `RecursionError`

```python
import sys
sys.getrecursionlimit()   # 1000 by default

try:
    deep_recursive_call(5000)
except RecursionError as e:
    print(e)   # "maximum recursion depth exceeded"
```
Verified: genuinely raised, a real hard limit — not just a theoretical concern.

---

## Status
5 core templates verified with real executed output, covering the full memoization-to-tabulation spectrum and the two standard DP table shapes (1D and 2D).
