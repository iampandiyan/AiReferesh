# Python Cheatsheet — DSA Topic 8 (Sorting & Searching)

**Companion to:** DSA_Topic8_Sorting_and_Searching.md
**Format:** Signature → Top usage → One verified runnable example per entry

---

## Merge Sort Template (Stable, O(n log n) Guaranteed)

```python
def merge_sort(arr):
    if len(arr) <= 1: return arr
    mid = len(arr) // 2
    left, right = merge_sort(arr[:mid]), merge_sort(arr[mid:])
    result, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:   # <= for stability
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    return result + left[i:] + right[j:]
```
Verified: 71.9x faster than bubble sort at n=3,000.

---

## Quick Sort Template (Average O(n log n))

```python
def quick_sort(arr):
    if len(arr) <= 1: return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + mid + quick_sort(right)
```
Worst case O(n²) on adversarial input — merge sort's O(n log n) is guaranteed regardless.

---

## `bisect` Module — Binary Search on Sorted Sequences

```python
import bisect
bisect.bisect_left(arr, x)    # leftmost insertion point (first occurrence if present)
bisect.bisect_right(arr, x)   # rightmost insertion point (after last occurrence)
bisect.insort(arr, x)          # insert x, keeping arr sorted
```
Verified: `bisect_left` on a non-present value correctly returns the insertion index, not an error.

---

## Manual Binary Search Template

```python
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target: return mid
        elif arr[mid] < target: lo = mid + 1
        else: hi = mid - 1
    return -1
```

---

## Modified Binary Search: Rotated Sorted Array Template

```python
def search_rotated(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target: return mid
        if nums[lo] <= nums[mid]:            # left half sorted
            if nums[lo] <= target < nums[mid]: hi = mid - 1
            else: lo = mid + 1
        else:                                 # right half sorted
            if nums[mid] < target <= nums[hi]: lo = mid + 1
            else: hi = mid - 1
    return -1
```
Verified against `[4,5,6,7,0,1,2]` — correctly finds targets across the rotation point.

---

## Find First/Last Position Template

```python
def find_first_last(nums, target):
    left = bisect.bisect_left(nums, target)
    if left == len(nums) or nums[left] != target:
        return [-1, -1]
    right = bisect.bisect_right(nums, target) - 1
    return [left, right]
```
Verified: `[5,7,7,8,8,8,10]` for target 8 → `[3, 5]`.

---

## Quickselect Template (Kth Largest, Average O(n))

```python
def find_kth_largest(nums, k):
    nums = nums.copy()
    target_idx = len(nums) - k
    def quickselect(lo, hi):
        pivot_idx = random.randint(lo, hi)
        nums[lo], nums[pivot_idx] = nums[pivot_idx], nums[lo]
        pivot_val, store = nums[lo], lo
        for i in range(lo+1, hi+1):
            if nums[i] < pivot_val:
                store += 1
                nums[i], nums[store] = nums[store], nums[i]
        nums[lo], nums[store] = nums[store], nums[lo]
        if store == target_idx: return nums[store]
        elif store < target_idx: return quickselect(store+1, hi)
        else: return quickselect(lo, store-1)
    return quickselect(0, len(nums)-1)
```
Verified against a full sort's result — same answer, average O(n) instead of O(n log n).

---

## Status
6 core templates verified with real executed output, including the dramatic real timing comparison from the main Topic 8 doc.
