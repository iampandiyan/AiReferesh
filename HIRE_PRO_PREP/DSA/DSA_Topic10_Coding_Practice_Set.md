# DSA Fundamentals — Topic 10: Timed Coding Practice Set

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (Coding Test, 36 min, after clearing the MCQ gate)**

Four problems, drawn from patterns across all 9 DSA topics, mixing difficulty like a real timed round. Suggested pace: ~8 minutes per problem, leaving buffer time. Attempt each before checking the solution — solutions and complexity notes are given after each problem, not collected at the end, so you can self-check incrementally like a real practice session.

---

## Problem 1: Group Anagrams (Hashing + Arrays)

**Given a list of strings, group the anagrams together.**
```python
Input: ["eat","tea","tan","ate","nat","bat"]
Output: [["eat","tea","ate"], ["tan","nat"], ["bat"]]  (order of groups doesn't matter)
```

<details>
<summary>Solution</summary>

```python
from collections import defaultdict

def group_anagrams(strs):
    groups = defaultdict(list)
    for s in strs:
        key = ''.join(sorted(s))   # anagrams share the same sorted-character key
        groups[key].append(s)
    return list(groups.values())

print(group_anagrams(["eat","tea","tan","ate","nat","bat"]))
```
**Complexity:** O(n · k log k), where n = number of strings, k = max string length (dominated by sorting each string as its grouping key).
**Pattern:** Hashing (Topic 3) — using a computed key (sorted characters) to group related items, the same idea as frequency-map problems but with a derived key instead of the raw value.
</details>

---

## Problem 2: Merge Intervals (Sorting + Arrays)

**Given a list of intervals, merge all overlapping intervals.**
```python
Input: [[1,3],[2,6],[8,10],[15,18]]
Output: [[1,6],[8,10],[15,18]]
```

<details>
<summary>Solution</summary>

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

print(merge_intervals([[1,3],[2,6],[8,10],[15,18]]))
```
**Complexity:** O(n log n), dominated by the sort.
**Pattern:** Sorting first to make a greedy single-pass merge possible (Topic 8) — a very common combination: sort to establish order, then a single linear pass solves what would otherwise need nested comparisons.
</details>

---

## Problem 3: Binary Tree Level Order Traversal (Trees + BFS)

**Given a binary tree, return the values grouped by level (top to bottom).**
```python
Input tree:
        3
       / \
      9   20
         /  \
        15   7
Output: [[3], [9,20], [15,7]]
```

<details>
<summary>Solution</summary>

```python
from collections import deque

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val, self.left, self.right = val, left, right

def level_order(root):
    if not root: return []
    result = []
    q = deque([root])
    while q:
        level = []
        for _ in range(len(q)):
            node = q.popleft()
            level.append(node.val)
            if node.left: q.append(node.left)
            if node.right: q.append(node.right)
        result.append(level)
    return result

tree = TreeNode(3, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))
print(level_order(tree))
```
**Complexity:** O(n) — every node visited exactly once.
**Pattern:** BFS via queue (Topics 6 & 7) — the `for _ in range(len(q))` trick is the standard way to process one tree level (or graph "wave") per outer loop iteration.
</details>

---

## Problem 4: Longest Subarray with At Most K Distinct Elements (Sliding Window + Hashing, harder)

**Given an array and integer k, find the length of the longest subarray containing at most k distinct values.**
```python
Input: nums = [1,2,1,2,3], k = 2
Output: 4   (the subarray [1,2,1,2] has exactly 2 distinct values and is the longest such subarray)
```

<details>
<summary>Solution</summary>

```python
def longest_subarray_k_distinct(nums, k):
    freq = {}
    left = 0
    max_len = 0
    for right, n in enumerate(nums):
        freq[n] = freq.get(n, 0) + 1
        while len(freq) > k:
            freq[nums[left]] -= 1
            if freq[nums[left]] == 0:
                del freq[nums[left]]
            left += 1
        max_len = max(max_len, right - left + 1)
    return max_len

print(longest_subarray_k_distinct([1,2,1,2,3], 2))   # 4
```
**Complexity:** O(n) — each element is added to and removed from the window at most once, despite the nested while loop (the same amortized reasoning as Topic 5's monotonic stack, and Topic 2's sliding window).
**Pattern:** This combines THREE patterns from across the whole DSA track into one problem — sliding window (Topic 2), hashing for frequency tracking (Topic 3), and the amortized-O(n) reasoning first seen with monotonic stacks (Topic 5). Recognizing that a problem needs pattern COMBINATION, not just one isolated technique, is exactly the skill a harder timed-round question tests.
</details>

---

## Self-Assessment Guide

| Outcome | Assessment |
|---|---|
| Solved all 4 within ~32 minutes, correct on first attempt | Strong — ready for the real 36-minute round |
| Solved 3/4 correctly, or needed the full 36 minutes | Solid foundation — review timing pressure with a few more practice problems |
| Struggled with Problem 4 specifically | Revisit Topics 2, 3, and 5 together — this problem exists specifically to test pattern combination, not just isolated recall |

---

## Status
Each problem draws a real, distinct pattern directly from the verified topic docs in this series (hashing/grouping, sort-then-greedy-merge, BFS level processing, and combined sliding-window+hashing) — not arbitrary problems, but the same techniques already demonstrated with real execution throughout Topics 1–9.

This completes the entire DSA Fundamentals track (Topics 1–10). Combined with the GenAI/AI-ML, API/Backend, and Database Fundamentals tracks, all four MCQ gatekeeper areas from the original AI Talent Quest 2026 syllabus are now fully covered, each with matching cheatsheets.
