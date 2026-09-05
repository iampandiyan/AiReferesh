# Python DSA & Coding Fundamentals — Topic 2: Arrays & Strings

**Target: AI Talent Quest 2026 — HirePro Chain Assessment**
**Track: Pure Python**

Every pattern and trap below has its own small runnable example, actually executed, with real output shown.

---

## 1. Core Patterns for Arrays & Strings

These five patterns cover the large majority of array/string coding-test questions. Recognizing which pattern applies is often the real skill being tested, not the syntax.

### Pattern 1: Two-pointer
Used when you need to scan from both ends or track two positions moving toward/away from each other — reversal, palindrome checks, pair-sum problems on sorted arrays.

**Reverse an array in place:**
```python
def reverse_in_place(arr):
    l, r = 0, len(arr) - 1
    while l < r:
        arr[l], arr[r] = arr[r], arr[l]
        l += 1; r -= 1
    return arr

print(reverse_in_place([1,2,3,4,5]))
```
Output: `[5, 4, 3, 2, 1]`
Complexity: O(n) time, O(1) extra space.

**Valid palindrome (ignoring case and non-alphanumeric characters):**
```python
def is_palindrome(s):
    s = ''.join(c.lower() for c in s if c.isalnum())
    l, r = 0, len(s) - 1
    while l < r:
        if s[l] != s[r]: return False
        l += 1; r -= 1
    return True

print(is_palindrome("A man, a plan, a canal: Panama"))
print(is_palindrome("hello"))
```
Output:
```
True
False
```

---

### Pattern 2: Sliding window
Used for "contiguous subarray/substring satisfying some condition" problems — fixed-size or variable-size windows.

**Max sum subarray of fixed size k:**
```python
def max_sum_subarray(arr, k):
    window_sum = sum(arr[:k])
    max_sum = window_sum
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i-k]
        max_sum = max(max_sum, window_sum)
    return max_sum

print(max_sum_subarray([2,1,5,1,3,2], 3))
```
Output: `9`
Complexity: O(n) — each element enters and leaves the window once, avoiding recomputation.

---

### Pattern 3: Prefix sum
Used when you need repeated range-sum queries — precompute once, answer each query in O(1).

```python
def build_prefix(arr):
    prefix = [0] * (len(arr) + 1)
    for i, x in enumerate(arr):
        prefix[i+1] = prefix[i] + x
    return prefix

def range_sum(prefix, l, r):
    return prefix[r+1] - prefix[l]

p = build_prefix([1,2,3,4,5])
print(p, "| sum(1,3):", range_sum(p, 1, 3))
```
Output: `[0, 1, 3, 6, 10, 15] | sum(1,3): 9`
Complexity: O(n) to build, O(1) per query — versus O(n) per query with no precomputation.

---

### Pattern 4: Kadane's algorithm (running max/local decision)
Used for "best contiguous subarray" problems — maximum subarray sum, max profit.

**Maximum subarray sum:**
```python
def max_subarray(nums):
    curr = best = nums[0]
    for x in nums[1:]:
        curr = max(x, curr + x)
        best = max(best, curr)
    return best

print(max_subarray([-2,1,-3,4,-1,2,1,-5,4]))
```
Output: `6`

**Best time to buy/sell stock (single pass, same underlying idea):**
```python
def max_profit(prices):
    min_price = float('inf')
    profit = 0
    for p in prices:
        min_price = min(min_price, p)
        profit = max(profit, p - min_price)
    return profit

print(max_profit([7,1,5,3,6,4]))
```
Output: `5`
Complexity: O(n) for both — track a running minimum/maximum instead of checking every pair (which would be O(n²)).

---

### Pattern 5: In-place array modification
Used when the interviewer explicitly wants O(1) extra space — write-pointer technique.

**Move zeroes to the end, preserving relative order of non-zero elements:**
```python
def move_zeroes(nums):
    insert_pos = 0
    for x in nums:
        if x != 0:
            nums[insert_pos] = x
            insert_pos += 1
    for i in range(insert_pos, len(nums)):
        nums[i] = 0
    return nums

print(move_zeroes([0,1,0,3,12]))
```
Output: `[1, 3, 12, 0, 0]`
Complexity: O(n) time, O(1) extra space.

---

## 2. Array/String-Specific Syntax — One Example Per Idiom

**Rotate array using slicing (concise, not the O(1)-space in-place version, but interview-acceptable unless they specifically forbid extra space):**
```python
def rotate(nums, k):
    k %= len(nums)
    return nums[-k:] + nums[:-k] if k else nums

print(rotate([1,2,3,4,5,6,7], 3))
```
Output: `[5, 6, 7, 1, 2, 3, 4]`

**Matrix rotate 90° clockwise, in place (transpose then reverse each row):**
```python
def rotate_matrix(matrix):
    n = len(matrix)
    for i in range(n):
        for j in range(i+1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    for row in matrix:
        row.reverse()
    return matrix

print(rotate_matrix([[1,2,3],[4,5,6],[7,8,9]]))
```
Output: `[[7, 4, 1], [8, 5, 2], [9, 6, 3]]`

**Spiral matrix traversal:**
```python
def spiral_order(matrix):
    result = []
    while matrix:
        result += matrix.pop(0)
        if matrix and matrix[0]:
            for row in matrix:
                result.append(row.pop())
        if matrix:
            result += matrix.pop()[::-1]
        if matrix and matrix[0]:
            for row in matrix[::-1]:
                result.append(row.pop(0))
    return result

print(spiral_order([[1,2,3],[4,5,6],[7,8,9]]))
```
Output: `[1, 2, 3, 6, 9, 8, 7, 4, 5]`

**Longest common prefix (shrink-from-the-right approach):**
```python
def longest_common_prefix(strs):
    if not strs: return ""
    prefix = strs[0]
    for s in strs[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix: return ""
    return prefix

print(longest_common_prefix(["flower","flow","flight"]))
```
Output: `fl`

**Product of array except self, without division (prefix × suffix products):**
```python
def product_except_self(nums):
    n = len(nums)
    result = [1] * n
    left = 1
    for i in range(n):
        result[i] = left
        left *= nums[i]
    right = 1
    for i in range(n-1, -1, -1):
        result[i] *= right
        right *= nums[i]
    return result

print(product_except_self([1,2,3,4]))
```
Output: `[24, 12, 8, 6]`
Complexity: O(n) time, O(1) extra space (excluding the output array) — the "no division" constraint is a common MCQ/interview trap since the naive solution (total product ÷ nums[i]) breaks on zeros.

---

## 3. Traps Specific to Arrays & Strings — Each Demonstrated Live

**Trap 1: Off-by-one in loop/index bounds**
```python
arr = [1,2,3]
try:
    print(arr[len(arr)])
except IndexError as e:
    print("IndexError as expected:", e)

print("correct last index:", arr[len(arr)-1])
```
Output:
```
IndexError as expected: list index out of range
correct last index: 3
```

**Trap 2: Strings are immutable — can't assign to an index**
```python
s = "hello"
try:
    s[0] = 'H'
except TypeError as e:
    print("TypeError as expected:", e)

s = 'H' + s[1:]   # correct way — build a new string
print("correct way:", s)
```
Output:
```
TypeError as expected: 'str' object does not support item assignment
correct way: Hello
```

**Trap 3: Negative slicing confusion**
```python
arr = [1,2,3,4,5]
print("arr[-2:]:", arr[-2:])     # last 2 elements
print("arr[:-2]:", arr[:-2])     # all except last 2
print("arr[::-1]:", arr[::-1])   # reversed
```
Output:
```
arr[-2:]: [4, 5]
arr[:-2]: [1, 2, 3]
arr[::-1]: [5, 4, 3, 2, 1]
```

**Trap 4: Modifying a list while iterating over it directly (silently wrong, no exception!)**
```python
nums = [1,2,3,4,5]
for i, x in enumerate(nums):
    if x == 3:
        nums.remove(x)   # mutating during iteration - skips the next element silently
print("buggy result (no exception, but wrong):", nums)
```
Output: `buggy result (no exception, but wrong): [1, 2, 4, 5]`
**This is the most dangerous trap of the four** — unlike dict mutation (which raises `RuntimeError`), removing from a list while iterating over it doesn't crash. It silently skips an element because the indices shift underneath the iterator. Fix: iterate over a copy (`for x in nums[:]`) or build a new list with a comprehension instead of mutating in place.

---

## 4. Verified Practice Problems Summary Table

All problems above are complete, verified solutions. Quick reference for review:

| Problem | Pattern | Time | Space |
|---|---|---|---|
| Reverse array in place | Two-pointer | O(n) | O(1) |
| Valid palindrome | Two-pointer | O(n) | O(1) |
| Max sum subarray (size k) | Sliding window | O(n) | O(1) |
| Range sum queries | Prefix sum | O(n) build, O(1) query | O(n) |
| Max subarray sum | Kadane's | O(n) | O(1) |
| Best time to buy/sell stock | Kadane's variant | O(n) | O(1) |
| Move zeroes | In-place write-pointer | O(n) | O(1) |
| Rotate array | Slicing | O(n) | O(n) |
| Rotate matrix 90° | Transpose + reverse | O(n²) | O(1) |
| Spiral traversal | Boundary peeling | O(n·m) | O(n·m) output |
| Longest common prefix | Shrink from right | O(S) where S = total chars | O(1) |
| Product except self | Prefix × suffix | O(n) | O(1) extra |

---

## 5. Rapid-Fire Self-Check (MCQ Simulation)

1. Why does removing an element from a list while iterating over it not raise an error, unlike doing the same with a dict? *(Lists don't track a "size changed" state the way dicts do during iteration — the iterator just walks by index, so shifted elements get silently skipped instead of triggering `RuntimeError`)*
2. What's the time complexity of the naive "check every pair" approach to max subarray sum vs Kadane's algorithm? *(O(n²) naive vs O(n) with Kadane's — the key insight is that a running max eliminates redundant re-summation)*
3. Why can't you do `s[0] = 'X'` on a Python string? *(Strings are immutable — any modification requires building a new string object)*
4. What breaks the naive "total product ÷ nums[i]" approach to Product of Array Except Self? *(Division by zero if any element is 0 — the prefix/suffix product approach avoids division entirely)*
5. What does `arr[::-1]` do, and what's its time/space complexity? *(Returns a reversed copy of the list — O(n) time and O(n) space, since slicing always creates a new list, not a view)*

---

## Status
All patterns, syntax examples, traps, and practice problems verified with real executed output above. Same format as Topic 1.

Ready for the companion **Cheatsheet — Topic 2** (array/string-relevant library methods: `re`, extended `str` methods, extended `numpy` array operations) whenever you want it, or straight into **Topic 3** if you'd rather prioritize breadth given the 2 days left before the assessment.
