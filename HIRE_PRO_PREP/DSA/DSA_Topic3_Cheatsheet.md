# Python Cheatsheet — DSA Topic 3 (Hashing)

**Companion to:** DSA_Topic3_Hashing.md
**Format:** Initialization/Signature → Top usage → One verified runnable example per entry

`dict`, `set`, and `Counter` core methods are already covered in the DSA Topic 1 cheatsheet — not repeated here.

---

## `hash()` — Built-in Hash Function

**Signature:**
```python
hash(obj)
```

**Top behavior:**
| Behavior | Explanation |
|---|---|
| Works on immutable types | int, float, str, tuple (if contents are hashable), frozenset |
| Raises `TypeError` on mutable types | list, dict, set — verified directly |
| Randomized for strings per-process | Since Python 3.3, security defense — verified across separate runs producing different values for the identical string |

**Verified example:**
```python
print(hash(42))         # 42
print(hash((1,2,3)))    # some large int, hashable
try:
    hash([1,2,3])
except TypeError as e:
    print(e)             # unhashable type: 'list'
```

---

## `__hash__` and `__eq__` — Making a Custom Class Hashable

**Signature:**
```python
class MyClass:
    def __hash__(self):
        return hash(self.some_field)   # must return an int
    def __eq__(self, other):
        return self.some_field == other.some_field
```

| Rule | Explanation |
|---|---|
| Both must be defined together | Defining `__eq__` alone makes a class unhashable by default (Python sets `__hash__ = None`) |
| Equal objects MUST have equal hashes | The reverse isn't required — different objects CAN share a hash (a collision), verified to still work correctly, just slower |

**Verified example (forced worst-case collision, still correct):**
```python
class BadHash:
    def __init__(self, val): self.val = val
    def __hash__(self): return 1          # everything collides
    def __eq__(self, other): return self.val == other.val

d = {}
for i in range(5):
    d[BadHash(i)] = i
print(d)   # all 5 entries present and correct, despite identical hashes
```

---

## Reusable Pattern: Frequency Map (One-Pass Build, Second-Pass Lookup)

```python
freq = {}
for item in iterable:
    freq[item] = freq.get(item, 0) + 1
# or equivalently: freq = Counter(iterable)
```
Used in: first non-repeating character, anagram checks, top-k frequent elements.

---

## Reusable Pattern: Complement Lookup ("Two Sum" style)

```python
seen = {}
for i, val in enumerate(nums):
    complement = target - val
    if complement in seen:
        return [seen[complement], i]
    seen[val] = i
```
O(n) instead of O(n²) — the single highest-yield hashmap pattern for timed assessments.

---

## Reusable Pattern: Prefix Sum + Hashmap (Subarray Sum Problems)

```python
seen = {0: 1}   # empty prefix counts as one occurrence of sum=0
prefix_sum = 0
count = 0
for n in nums:
    prefix_sum += n
    if prefix_sum - k in seen:
        count += seen[prefix_sum - k]
    seen[prefix_sum] = seen.get(prefix_sum, 0) + 1
```
Verified: `subarray_sum_equals_k([1,1,1], 2)` → `2`. The `{0: 1}` seed is essential — it correctly counts subarrays that start from index 0.

---

## Status
2 core built-in mechanisms plus 3 reusable hashmap pattern templates, all verified with real executed output in the main Topic 3 doc.
