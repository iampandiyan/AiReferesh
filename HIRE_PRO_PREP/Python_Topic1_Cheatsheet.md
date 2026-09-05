# Python Cheatsheet — Topic 1 (Built-ins + Production Libraries)

**Companion to:** Python_DSA_Topic1_Complexity_and_Fundamentals.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry
**Scope:** Core built-ins (list, dict, set, str) + every library used in Topic 1

All examples below were executed for real — outputs shown are actual, not invented.

---

## `list`

**Initialization:**
```python
lst = []
lst = [1,2,3]
lst = list(range(5))
```

**Top methods:**
| Method | Explanation |
|---|---|
| `append(x)` | Add one item to the end — O(1) amortized |
| `insert(i, x)` | Insert `x` at index `i` — O(n), shifts elements |
| `pop()` / `pop(i)` | Remove and return last item, or item at index `i` |
| `remove(x)` | Remove first occurrence of value `x` — O(n) |
| `extend(iterable)` | Append all items from another iterable |
| `sort(key=, reverse=)` | In-place sort — O(n log n), stable (Timsort) |
| `reverse()` | Reverse in place — O(n) |
| `index(x)` | Return index of first occurrence of `x` |
| `count(x)` | Count occurrences of `x` |
| `copy()` | Shallow copy — same as `lst[:]` |
| `clear()` | Remove all elements |

**Verified example:**
```python
lst = [3,1,2]
lst.append(4); print(lst)          # [3, 1, 2, 4]
lst.insert(0, 0); print(lst)       # [0, 3, 1, 2, 4]
lst.pop(); print(lst)              # [0, 3, 1, 2]
lst.remove(1); print(lst)          # [0, 3, 2]
lst.extend([9,9]); print(lst)      # [0, 3, 2, 9, 9]
lst.sort(key=lambda x: -x); print(lst)  # [9, 9, 3, 2, 0]
lst.reverse(); print(lst)          # [0, 2, 3, 9, 9]
print(lst.index(0), lst.count(9))  # 0 2
```

---

## `dict`

**Initialization:**
```python
d = {}
d = {"a": 1, "b": 2}
d = dict(zip(["a","b"], [1,2]))
```

**Top methods:**
| Method | Explanation |
|---|---|
| `get(key, default)` | Safe lookup — returns `default` instead of raising `KeyError` |
| `setdefault(key, default)` | Get value, or set-and-return `default` if key missing |
| `keys()` / `values()` / `items()` | Views for iteration — insertion-ordered |
| `pop(key)` | Remove key and return its value |
| `popitem()` | Remove and return the last-inserted (key, value) pair |
| `update(other_dict)` | Merge another dict in, overwriting existing keys |
| `fromkeys(iterable, value)` | Build a new dict with all keys set to the same value |

**Verified example:**
```python
d = {"a":1, "b":2}
print(d.get("c", "default"))       # default
d.setdefault("c", 3); print(d)     # {'a': 1, 'b': 2, 'c': 3}
print(list(d.items()))             # [('a', 1), ('b', 2), ('c', 3)]
print(d.pop("a"), d)               # 1 {'b': 2, 'c': 3}
d.update({"z":99}); print(d)       # {'b': 2, 'c': 3, 'z': 99}
print(dict.fromkeys(["x","y"], 0)) # {'x': 0, 'y': 0}
```

---

## `set`

**Initialization:**
```python
s = set()
s = {1, 2, 3}
s = set([1,2,2,3])   # dedupes automatically
```

**Top methods:**
| Method | Explanation |
|---|---|
| `add(x)` | Add single element — O(1) average |
| `discard(x)` | Remove element if present, no error if missing (vs `remove(x)` which raises) |
| `union(other)` / `\|` | All elements from both sets |
| `intersection(other)` / `&` | Elements common to both |
| `difference(other)` / `-` | Elements in this set but not the other |
| `issubset(other)` | Check if this set is fully contained in `other` |

**Verified example:**
```python
s1 = {1,2,3}; s2 = {2,3,4}
s1.add(5); print(s1)               # {1, 2, 3, 5}
s1.discard(100); print(s1)         # {1, 2, 3, 5} - no error even though 100 wasn't there
print(s1 | s2)                     # {1, 2, 3, 4, 5}
print(s1 & s2)                     # {2, 3}
print(s1 - s2)                     # {1, 5}
print({1,2}.issubset(s1))          # True
```

---

## `str`

**Initialization:**
```python
s = "hello"
s = 'hello'
s = f"{name} is {age}"
```

**Top methods:**
| Method | Explanation |
|---|---|
| `strip()` | Remove leading/trailing whitespace (or given chars) |
| `split(sep)` | Break into a list on a separator |
| `join(iterable)` | Combine a list of strings using this string as separator |
| `replace(old, new)` | Replace all occurrences |
| `find(sub)` | Index of first occurrence, or -1 if not found |
| `startswith(x)` / `endswith(x)` | Boolean prefix/suffix check |
| `upper()` / `lower()` | Case conversion |
| `isdigit()` | Check if all characters are digits |

**Verified example:**
```python
text = "  Hello,World,Foo  "
print(repr(text.strip()))              # 'Hello,World,Foo'
print(text.strip().split(","))         # ['Hello', 'World', 'Foo']
print("-".join(["a","b","c"]))         # a-b-c
print(text.find("World"))              # 8
print("123".isdigit())                 # True
name, age = "KP", 37
print(f"{name} is {age}")              # KP is 37
```

---

## `collections.deque`

**Initialization:**
```python
from collections import deque
dq = deque()
dq = deque([1,2,3])
dq = deque(maxlen=5)   # bounded - auto-evicts oldest when full
```

**Top methods:**
| Method | Explanation |
|---|---|
| `append(x)` | Add to right end — O(1) |
| `appendleft(x)` | Add to left end — O(1) |
| `pop()` | Remove/return rightmost — O(1) |
| `popleft()` | Remove/return leftmost — O(1) |
| `extend(iterable)` | Append multiple items to the right |
| `rotate(n)` | Rotate `n` steps right (negative = left) |
| `clear()` | Remove all elements |

**Verified example:**
```python
dq = deque([1,2,3])
dq.append(4); dq.appendleft(0)
print(list(dq))          # [0, 1, 2, 3, 4]
dq.rotate(1); print(list(dq))    # [4, 0, 1, 2, 3]
dq.rotate(-2); print(list(dq))   # [1, 2, 3, 4, 0]

bounded = deque(maxlen=3)
for x in [1,2,3,4,5]: bounded.append(x)
print(list(bounded))     # [3, 4, 5]
```

---

## `collections.Counter`

**Initialization:**
```python
from collections import Counter
c = Counter("aabbbcc")
c = Counter([1,1,2,3])
c = Counter({"a": 2, "b": 1})
```

**Top methods:**
| Method | Explanation |
|---|---|
| `most_common(k)` | Top-k `(item, count)` pairs by frequency |
| `subtract(other)` | Subtract counts from another Counter/iterable in place |
| `elements()` | Iterator yielding each element repeated by its count |
| `+`, `-`, `&`, `\|` | Arithmetic between Counters (add, subtract, min, max counts) |

**Verified example:**
```python
c = Counter("aabbbcc")
print(c)                        # Counter({'b': 3, 'a': 2, 'c': 2})
print(c.most_common(2))         # [('b', 3), ('a', 2)]
c.subtract(Counter("ab"))
print(c)                        # Counter({'b': 2, 'c': 2, 'a': 1})
print(list(Counter("aab").elements()))  # ['a', 'a', 'b']
```

---

## `collections.defaultdict`

**Initialization:**
```python
from collections import defaultdict
dd = defaultdict(int)     # missing keys default to 0
dd = defaultdict(list)    # missing keys default to []
dd = defaultdict(set)     # missing keys default to set()
```

**Top methods:**
| Method | Explanation |
|---|---|
| (all standard `dict` methods) | Behaves exactly like `dict` for get/set/items etc. |
| auto-vivification on missing key | Accessing a missing key creates it with the default factory's value instead of raising `KeyError` |

**Verified example:**
```python
dd = defaultdict(int)
for ch in "aab":
    dd[ch] += 1
print(dict(dd))                 # {'a': 2, 'b': 1}

dd_list = defaultdict(list)
dd_list["x"].append(1)
print(dict(dd_list))            # {'x': [1]}
```

---

## `heapq`

**Initialization:**
```python
import heapq
heap = []
heap = [5,1,3]; heapq.heapify(heap)   # turn existing list into a heap in place, O(n)
```

**Top methods:**
| Method | Explanation |
|---|---|
| `heappush(heap, x)` | Push `x` — O(log n) |
| `heappop(heap)` | Pop and return smallest — O(log n) |
| `heapify(list)` | Convert a list into a valid heap in place — O(n) |
| `nlargest(k, iterable)` | Top-k largest without fully sorting |
| `nsmallest(k, iterable)` | Top-k smallest without fully sorting |
| `heappushpop(heap, x)` | Push then pop in one call — more efficient than separate calls |

**Verified example:**
```python
heap = [5,1,3]
heapq.heapify(heap); print(heap)          # [1, 5, 3]
heapq.heappush(heap, 0); print(heap)      # [0, 1, 3, 5]
print(heapq.heappop(heap))                # 0
print(heapq.nlargest(2, [5,1,9,3]))       # [9, 5]
print(heapq.nsmallest(2, [5,1,9,3]))      # [1, 3]
```

---

## `bisect`

**Initialization:**
```python
import bisect
sl = [1,3,3,5,7]   # must already be sorted
```

**Top methods:**
| Method | Explanation |
|---|---|
| `bisect_left(list, x)` | Leftmost insertion index to keep list sorted |
| `bisect_right(list, x)` | Rightmost insertion index to keep list sorted |
| `insort(list, x)` | Insert `x` in sorted position — O(n) due to shifting, but avoids a full re-sort |

**Verified example:**
```python
sl = [1,3,3,5,7]
print(bisect.bisect_left(sl, 3))    # 1
print(bisect.bisect_right(sl, 3))   # 3
bisect.insort(sl, 4)
print(sl)                           # [1, 3, 3, 4, 5, 7]
```

---

## `itertools`

**Initialization:**
```python
from itertools import combinations, permutations, product, chain, groupby, accumulate, islice
```

**Top methods:**
| Function | Explanation |
|---|---|
| `combinations(iterable, r)` | All r-length combinations, order doesn't matter |
| `permutations(iterable, r)` | All r-length orderings, order matters |
| `product(a, b)` | Cartesian product of input iterables |
| `chain(a, b)` | Flatten multiple iterables into one sequence |
| `groupby(iterable)` | Group consecutive equal elements (input must be pre-sorted for full grouping) |
| `accumulate(iterable)` | Running totals (prefix sums) |
| `islice(iterable, start, stop)` | Slice an iterator without materializing the whole thing |

**Verified example:**
```python
print(list(combinations([1,2,3], 2)))     # [(1, 2), (1, 3), (2, 3)]
print(list(permutations([1,2], 2)))       # [(1, 2), (2, 1)]
print(list(product([1,2],[3,4])))         # [(1, 3), (1, 4), (2, 3), (2, 4)]
print(list(chain([1,2],[3,4])))           # [1, 2, 3, 4]
print(list(accumulate([1,2,3,4])))        # [1, 3, 6, 10]
print(list(islice(range(10), 2, 6)))      # [2, 3, 4, 5]
```

---

## `functools`

**Initialization:**
```python
from functools import lru_cache, reduce, partial
```

**Top methods:**
| Function | Explanation |
|---|---|
| `@lru_cache(maxsize=None)` | Memoize a function's results — turns exponential recursion into linear |
| `reduce(func, iterable)` | Cumulatively apply a function to reduce an iterable to a single value |
| `partial(func, *args)` | Pre-fill some arguments of a function, get a new callable |

**Verified example:**
```python
@lru_cache(maxsize=None)
def fib(n): return n if n<=1 else fib(n-1)+fib(n-2)
print(fib(20))                                    # 6765

print(reduce(lambda a,b: a+b, [1,2,3,4]))         # 10

add5 = partial(lambda a,b: a+b, 5)
print(add5(10))                                   # 15
```

---

## `dataclasses`

**Initialization:**
```python
from dataclasses import dataclass, field, asdict

@dataclass
class Point:
    x: int
    y: int = 0
    tags: list = field(default_factory=list)   # mutable defaults MUST use default_factory, not a bare []
```

**Top methods/features:**
| Feature | Explanation |
|---|---|
| Auto-generated `__init__`, `__repr__`, `__eq__` | No boilerplate constructor/printing code needed |
| `field(default_factory=...)` | Correct way to give a mutable default (list/dict) — avoids the mutable-default-argument trap |
| `asdict(instance)` | Convert a dataclass instance to a plain dict |
| `frozen=True` (class option) | Makes instances immutable, like a Java record |

**Verified example:**
```python
p = Point(1)
p.tags.append("origin")
print(p)              # Point(x=1, y=0, tags=['origin'])
print(asdict(p))       # {'x': 1, 'y': 0, 'tags': ['origin']}
```

---

## `enum`

**Initialization:**
```python
from enum import Enum, auto

class Status(Enum):
    PENDING = auto()
    DONE = auto()
```

**Top methods:**
| Feature | Explanation |
|---|---|
| `.value` | The underlying value of the member |
| `.name` | The string name of the member |
| Iterating the class | `for member in Status:` yields all members in definition order |
| `auto()` | Auto-assigns incrementing values, so you don't hardcode 1, 2, 3... |

**Verified example:**
```python
print(Status.PENDING.value, Status.PENDING.name)   # 1 PENDING
print([s.name for s in Status])                    # ['PENDING', 'DONE']
```

---

## `contextlib`

**Initialization:**
```python
from contextlib import contextmanager, suppress
```

**Top methods:**
| Feature | Explanation |
|---|---|
| `@contextmanager` | Turn a generator function into a `with`-usable context manager, without writing a full class |
| `suppress(ExceptionType)` | Silently ignore a specific exception type inside a `with` block |

**Verified example:**
```python
@contextmanager
def ctx():
    print("enter"); yield "resource"; print("exit")

with ctx() as r:
    print("using:", r)
# Output: enter / using: resource / exit

with suppress(ZeroDivisionError):
    1/0
print("suppress worked, no crash")
```

---

## `asyncio`

**Initialization:**
```python
import asyncio

async def worker(n):
    await asyncio.sleep(0.01)
    return n * 2
```

**Top methods:**
| Function | Explanation |
|---|---|
| `asyncio.run(coro)` | Entry point — runs a top-level coroutine to completion |
| `asyncio.gather(*coros)` | Run multiple coroutines concurrently, collect all results |
| `asyncio.sleep(seconds)` | Non-blocking sleep — yields control instead of freezing the event loop |
| `asyncio.create_task(coro)` | Schedule a coroutine to run concurrently, get a handle to it |

**Verified example:**
```python
async def main():
    results = await asyncio.gather(worker(1), worker(2), worker(3))
    return results

print(asyncio.run(main()))     # [2, 4, 6]
```

---

## `numpy`

**Initialization:**
```python
import numpy as np
arr = np.array([1,2,3,4])
```

**Top methods:**
| Method | Explanation |
|---|---|
| `np.arange(start, stop, step)` | Like `range()` but returns a numpy array |
| `np.zeros(n)` / `np.ones(n)` | Pre-filled arrays |
| `.reshape(rows, cols)` | Change array dimensions without copying data |
| `.sum(axis=)` / `.mean(axis=)` | Aggregate along a specific dimension |
| Boolean indexing `arr[arr > x]` | Filter elements matching a condition — vectorized, no loop needed |
| Vectorized arithmetic (`arr * 2`) | Element-wise operation in compiled C, much faster than a Python loop |

**Verified example:**
```python
arr = np.array([1,2,3,4])
print(np.arange(0,10,2))                       # [0 2 4 6 8]
print(np.arange(6).reshape(2,3))               # [[0 1 2] [3 4 5]]
print(np.arange(6).reshape(2,3).sum(axis=0))   # [3 5 7]
print(arr[arr > 2])                            # [3 4]
print(arr * 2)                                 # [2 4 6 8]
```

---

## `pandas`

**Initialization:**
```python
import pandas as pd
df = pd.DataFrame({"a": [1,2,3], "b": [4,5,6]})
```

**Top methods:**
| Method | Explanation |
|---|---|
| `df.head(n)` | First n rows |
| `df.loc[condition]` | Row filtering by boolean condition |
| `df.groupby(col)` | Group rows by column value for aggregation |
| `df.apply(func)` | Apply a function to each element/row/column (slower than vectorized ops — know this trade-off) |
| `df.sort_values(col)` | Sort rows by a column |
| `df.fillna(value)` | Replace missing (`NaN`) values |

**Verified example:**
```python
df = pd.DataFrame({"a":[1,2,3], "b":[4,5,6]})
print(df.loc[df["a"]>1])
#    a  b
# 1  2  5
# 2  3  6

df["c"] = df["a"].apply(lambda x: x*10)
print(df.sort_values("a", ascending=False))
#    a  b   c
# 2  3  6  30
# 1  2  5  20
# 0  1  4  10
```

---

## `pydantic`

**Initialization:**
```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str
    age: int = Field(gt=0)   # constraint: age must be greater than 0
```

**Top methods:**
| Feature | Explanation |
|---|---|
| Automatic validation on instantiation | Raises `ValidationError` if types/constraints don't match — this is enforced, unlike plain `typing` hints |
| `.model_dump()` | Convert model instance to a plain dict |
| `Field(gt=, lt=, min_length=, ...)` | Declarative constraints beyond just type |
| Nested models | A `BaseModel` field can itself be another `BaseModel` — validated recursively |

**Verified example:**
```python
u = User(name="KP", age=37)
print(u)                    # name='KP' age=37
print(u.model_dump())       # {'name': 'KP', 'age': 37}

try:
    User(name="Bad", age=-1)
except Exception as e:
    print(type(e).__name__)  # ValidationError
```

---

## `typing`

**Initialization:**
```python
from typing import List, Dict, Optional, Union
```

**Top usages:**
| Construct | Explanation |
|---|---|
| `List[int]`, `Dict[str, int]` | Generic type hints for collections — readability/IDE only, not enforced at runtime |
| `Optional[int]` | Shorthand for `Union[int, None]` — signals a value may be absent |
| `Union[int, str]` | Value can be one of several types |
| (Contrast with `pydantic`) | `typing` hints are NOT enforced at runtime — `pydantic` is what actually validates |

**Verified example:**
```python
def f(x: Optional[int] = None) -> Union[int, str]:
    return x if x is not None else "none"

print(f(), f(5))            # none 5

nums: List[int] = [1,2,3]
mapping: Dict[str, int] = {"a":1}
print(nums, mapping)        # [1, 2, 3] {'a': 1}
```

---

## Status
All 19 entries (4 built-ins + 15 libraries) verified with real executed output. This is a standalone reference — use it alongside the main Topic 1 doc for quick lookup during practice, not as a replacement for the fuller explanations there.
