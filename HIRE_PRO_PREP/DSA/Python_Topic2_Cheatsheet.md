# Python Cheatsheet — Topic 2 (Arrays & Strings Libraries)

**Companion to:** Python_DSA_Topic2_Arrays_and_Strings.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

All examples below were executed for real — outputs shown are actual, not invented.

---

## `re` (regular expressions)

**Initialization:**
```python
import re
pattern = re.compile(r'(\w+)@(\w+)\.com')   # compile once, reuse many times for performance
```

**Top methods:**
| Method | Explanation |
|---|---|
| `re.match(pattern, s)` | Matches only at the **start** of the string — returns `None` if the start doesn't match |
| `re.search(pattern, s)` | Finds the pattern **anywhere** in the string, returns first match |
| `re.findall(pattern, s)` | Returns a list of ALL non-overlapping matches |
| `re.sub(pattern, repl, s)` | Replace all matches with `repl` |
| `re.split(pattern, s)` | Split string on a regex pattern (more flexible than `str.split`) |
| `.group(n)` | On a match object, get the full match (`group(0)`) or a specific capture group |

**Verified example:**
```python
print(re.match(r'\d+', 'abc123'))       # None - doesn't match at position 0
print(re.search(r'\d+', 'abc123'))      # <re.Match object; span=(3, 6), match='123'>
print(re.findall(r'\d+', 'a1 b22 c333')) # ['1', '22', '333']
print(re.sub(r'\s+', '_', 'hello   world  foo'))  # hello_world_foo
print(re.split(r'[,;]', 'a,b;c,d'))      # ['a', 'b', 'c', 'd']

pattern = re.compile(r'(\w+)@(\w+)\.com')
m = pattern.match('kp@example.com')
print(m.group(0), m.group(1), m.group(2))  # kp@example.com kp example
```

---

## `str` — Extended Methods (beyond Topic 1's basics)

**Top methods:**
| Method | Explanation |
|---|---|
| `zfill(width)` | Pad with leading zeros to reach `width` — common for formatting IDs/codes |
| `center(width, fillchar)` / `ljust` / `rjust` | Pad and align a string within a fixed width |
| `title()` | Capitalize the first letter of every word |
| `capitalize()` | Capitalize only the first letter of the whole string |
| `count(sub)` | Count non-overlapping occurrences of a substring |
| `rfind(sub)` | Like `find()` but searches from the right — returns last occurrence index |
| `translate(table)` + `str.maketrans()` | Fast bulk character replacement (faster than chained `.replace()` calls) |
| `splitlines()` | Split on line boundaries (`\n`, `\r\n`) without leaving empty trailing entries like `split('\n')` sometimes does |
| `isalpha()` / `isspace()` / `isalnum()` | Character-class checks — common in parsing/validation logic |

**Verified example:**
```python
print("42".zfill(5))                     # 00042
print("hi".center(10, '*'))              # ****hi****
print("hello world".title())             # Hello World
print("mississippi".count("ss"))         # 2
print("hello world hello".rfind("hello")) # 12

table = str.maketrans("abc", "xyz")
print("aabbcc".translate(table))         # xxyyzz

print("line1\nline2\nline3".splitlines()) # ['line1', 'line2', 'line3']
print("abc".isalpha(), "  ".isspace(), "abc123".isalnum())  # True True True
```

---

## `numpy` — Extended Array Operations (beyond Topic 1's basics)

**Top methods:**
| Method | Explanation |
|---|---|
| `np.transpose(arr)` | Flip rows/columns of a 2D array |
| `np.where(condition, x, y)` | Vectorized if/else — element-wise conditional selection |
| `np.unique(arr)` | Sorted unique elements — vectorized dedup |
| `np.concatenate([a, b])` | Join arrays along an existing axis |
| `np.vstack` / `np.hstack` | Stack arrays vertically (new rows) or horizontally (new columns) |
| `np.flip(arr)` | Reverse array along an axis — vectorized equivalent of `arr[::-1]` |

**Verified example:**
```python
import numpy as np

arr2d = np.array([[1,2,3],[4,5,6]])
print(np.transpose(arr2d))
# [[1 4]
#  [2 5]
#  [3 6]]

arr = np.array([1,2,3,4,5])
print(np.where(arr > 2, arr, 0))         # [0 0 3 4 5]
print(np.unique([1,1,2,2,3,3,3]))        # [1 2 3]
print(np.concatenate([np.array([1,2]), np.array([3,4])]))  # [1 2 3 4]
print(np.vstack([[1,2],[3,4]]))          # [[1 2] [3 4]]
print(np.hstack([[1,2],[3,4]]))          # [1 2 3 4]
print(np.flip(np.array([1,2,3,4])))      # [4 3 2 1]
```

---

## `array` (typed arrays — less common, occasionally appears in MCQs)

**Initialization:**
```python
from array import array
a = array('i', [1,2,3,4])   # 'i' = signed int typecode
```

**Top methods:**
| Method | Explanation |
|---|---|
| `append(x)` | Add an element — same interface as `list`, but memory-efficient (fixed C type per element) |
| `.typecode` | The type code string (`'i'` for int, `'d'` for double, etc.) |
| Contrast with `list` | `array` stores homogeneous, fixed-type data more compactly — `list` can hold mixed types but with more overhead per element |

**Verified example:**
```python
a = array('i', [1,2,3,4])
print(a, a.typecode)      # array('i', [1, 2, 3, 4]) i
a.append(5)
print(list(a))            # [1, 2, 3, 4, 5]
```

---

## `string` (module — constants, not methods)

**Top constants:**
| Constant | Explanation |
|---|---|
| `string.ascii_lowercase` | `'abcdefghijklmnopqrstuvwxyz'` — useful for generating/validating alphabets in coding problems |
| `string.digits` | `'0123456789'` |
| `string.punctuation` | All standard punctuation characters — useful for text-cleaning/parsing problems |

**Verified example:**
```python
import string
print(string.ascii_lowercase)   # abcdefghijklmnopqrstuvwxyz
print(string.digits)            # 0123456789
print(string.punctuation)       # !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
```

---

## Status
All 5 entries verified with real executed output. Use alongside the main Topic 2 doc.
