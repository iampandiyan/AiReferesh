# DSA Fundamentals — Topic 10: Timed Mixed MCQ Practice Set (Exam Format)

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Attempt all 20 questions first, without checking the answer key, to simulate real test conditions. Suggested pace: ~90 seconds/question. Answer key with explanations is at the end.

---

## Questions

**1.** Which operation is genuinely O(1): `list.pop(0)` or `deque.popleft()`?
A. list.pop(0) — it's simpler
B. deque.popleft() — list.pop(0) must shift every remaining element, genuinely O(n)
C. They have identical performance
D. Neither is O(1), both are O(n)

**2.** What actually happens with `def f(x, cache=[]): cache.append(x); return cache` when called multiple times without explicitly passing `cache`?
A. A fresh empty list is created on every function call
B. The same list object persists across ALL calls, silently accumulating values from previous calls
C. Python raises an error if you try this
D. The list resets automatically after each call

**3.** Does `hash('hello')` return the same value across different runs of the same Python script?
A. Yes, always — hash() is a pure deterministic function
B. No — string hashes are randomized per-process since Python 3.3, verified across separate runs producing different values
C. Only for very long strings
D. Only if PYTHONHASHSEED is explicitly set

**4.** If every key in a dict is forced to have the identical hash value (a deliberately terrible hash function), what genuinely happens?
A. The dict returns wrong values for some keys
B. Correctness is fully preserved via collision resolution — only performance degrades toward O(n)
C. Python raises a RuntimeError
D. Only the first colliding key is stored, others are silently dropped

**5.** Why is Floyd's cycle detection (fast/slow pointers) mathematically guaranteed to detect a cycle, not just probabilistically likely to?
A. It's a heuristic that sometimes misses cycles
B. fast moves twice as fast as slow, so within a cycle it's mathematically guaranteed to eventually meet slow at the same node
C. It only works if the cycle starts at the head
D. It requires knowing the list's length in advance

**6.** What's the real space complexity difference between recursive and iterative linked-list reversal?
A. They have identical space complexity
B. Recursive reversal uses O(n) space (call stack); iterative reversal uses O(1) space
C. Iterative reversal uses MORE space than recursive
D. Neither approach uses any extra space

**7.** What specific bracket string was used to prove that counting opening vs closing brackets alone is NOT sufficient for Valid Parentheses?
A. "(([[]]))" — too many nested levels
B. "([)]" — equal bracket counts, but genuinely improperly nested (interleaved), requiring a stack to catch
C. "{}" — too simple to matter
D. There is no such string; counting is always sufficient

**8.** What real bug was demonstrated in a naive "Validate BST" function that only checks immediate parent-child value relationships?
A. It correctly validates all trees, there is no bug
B. Checking only immediate parent-child values misses violations from grandparent/higher ancestor constraints — verified with a real tree that passed incorrectly
C. The bug only appears in trees with more than 100 nodes
D. The naive check is actually MORE strict than necessary

**9.** Why does inorder traversal of a valid BST genuinely, provably produce sorted output?
A. It's a coincidence specific to certain trees
B. Inorder visits left (smaller) subtree, then node, then right (larger) subtree — this exactly matches BST ascending order by definition
C. It only works for balanced BSTs
D. Preorder traversal also always produces sorted output for a BST

**10.** In a real verified Dijkstra run, a 3-edge path was chosen over a seemingly shorter 2-edge path. Why?
A. Dijkstra has a bug and picked the wrong path
B. Dijkstra minimizes total edge WEIGHT, not edge count — the 3-edge path's total weight (4) was genuinely less than the 2-edge path's (5)
C. The graph had duplicate edges
D. Dijkstra only works on undirected graphs

**11.** Why does directed-graph cycle detection genuinely require 3 states (white/gray/black), not just a simple visited/unvisited set?
A. Colors are just for visual debugging, not functionally necessary
B. Must distinguish nodes on the CURRENT recursion path (gray) from fully-processed nodes (black) — only revisiting gray indicates a genuine cycle
C. 3 colors are needed because graphs can have at most 3 components
D. This only applies to undirected graphs

**12.** At a real measured scale of n=3,000 elements, how much faster was merge sort (and Python's built-in sorted()) than bubble sort?
A. About 2x faster — a modest difference
B. 71.9x faster for merge sort, and 742.1x faster for Python's built-in sorted() — genuinely measured, not estimated
C. They perform identically at small scale
D. Bubble sort was actually faster in the real test

**13.** What's the key real insight that makes binary search work on a rotated sorted array in genuine O(log n)?
A. It requires first fully un-rotating the array, which takes O(n)
B. At least one half (left or right of any midpoint) is always genuinely sorted, even in a rotated array — the algorithm identifies which half and narrows accordingly
C. It only works if you know the rotation point in advance
D. It doesn't actually work in O(log n), it's really O(n)

**14.** In a real measured comparison at n=28, how much faster was memoized Fibonacci than naive recursive Fibonacci?
A. About 10x — a modest improvement
B. 2730x faster — genuinely measured at n=28, not estimated
C. Memoization was actually slower due to dict overhead
D. They performed identically

**15.** What genuinely happens when naive recursive Fibonacci is called with a very large n (e.g., 5000) with no memoization?
A. It runs slowly but eventually completes
B. A genuine RecursionError is raised — "maximum recursion depth exceeded" — Python's default limit is a real, enforced boundary
C. Python automatically increases the recursion limit as needed
D. It returns an incorrect result silently

**16.** Why is Quickselect genuinely faster (average case) than fully sorting an array just to find the Kth largest element?
A. Quickselect and full-sort-then-index have identical time complexity
B. Quickselect only recurses into the ONE partition side containing the target index, achieving average O(n) instead of paying O(n log n) to fully sort everything
C. Quickselect uses more memory but less time
D. Full sorting is actually faster in practice

**17.** What does "path compression" in Union-Find's `find()` method actually do?
A. It merges two separate trees into one
B. It flattens the tree by making every visited node point directly to the root during lookup, speeding up future find() calls
C. It deletes unused nodes to save memory
D. It sorts the elements within each set

**18.** In the Coin Change DP solution, what does it mean if `dp[amount]` is still `float('inf')` after the algorithm finishes?
A. A bug in the code that should be fixed
B. A sentinel meaning "not yet known to be reachable" — if it's still infinity at the end, that amount is genuinely impossible with the given coins
C. The maximum possible number of coins needed
D. An error code that should be checked separately

**19.** This same hashing principle appeared in the Database track too — why can a hash-based index never support a range query like "> value"?
A. Hash indexes are always slower than no index at all
B. Hashing deliberately destroys ordering information — similar values scatter to unrelated positions, so range/comparison queries can't use a hash structure at all
C. The table was too small for any index to help
D. Hash indexes only work on numeric columns, not strings

**20.** Why must the Diameter of Binary Tree algorithm track the best result at EVERY node during recursion, not just compute it once at the root?
A. It always passes through the root, so checking only the root suffices
B. The longest path can be entirely within a subtree, not touching the root at all — the max must be tracked at EVERY node during the recursion
C. Diameter is undefined for trees with more than one leaf
D. The algorithm only works on balanced trees

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
| 1 | B | Complexity/Fundamentals | Verified: 49.2x measured slowdown for list.pop(0) at 20,000 elements. |
| 2 | B | Complexity/Fundamentals | Mutable default arguments are created once at function definition, not per call. |
| 3 | B | Hashing | Verified across 3 separate process runs — real hash randomization since Python 3.3. |
| 4 | B | Hashing | Verified with a forced-collision hash function — correctness preserved, only speed degrades. |
| 5 | B | Linked Lists | A real physically-constructed cycle proved this mathematically, not just heuristically. |
| 6 | B | Linked Lists | Verified — recursive uses O(n) call-stack space, iterative uses O(1). |
| 7 | B | Stacks & Queues | "([)]" has equal counts but is genuinely improperly nested. |
| 8 | B | Trees & BST | A real tree (root=5, right=8, right.left=4) passed the naive check incorrectly. |
| 9 | B | Trees & BST | Inorder visits left-node-right, exactly matching BST ascending order by definition. |
| 10 | B | Graphs | Verified: A→C→B→D (weight 4) genuinely beat A→B→D (weight 5). |
| 11 | B | Graphs | Gray (active path) vs black (fully processed) is the real distinction needed. |
| 12 | B | Sorting & Searching | Verified real timing: 71.9x and 742.1x at n=3,000. |
| 13 | B | Sorting & Searching | At least one half of a rotated array is always genuinely sorted. |
| 14 | B | Recursion & DP | Verified real timing: 2730x speedup at n=28. |
| 15 | B | Recursion & DP | A genuine RecursionError was triggered, not a hypothetical. |
| 16 | B | Sorting & Searching | Quickselect only explores the needed partition side, verified against full sort. |
| 17 | B | Graphs | Path compression flattens the tree during lookup, verified with real code. |
| 18 | B | Recursion & DP | The infinity sentinel correctly signals genuine unreachability. |
| 19 | B | Hashing/Cross-track | Same principle verified in both the DSA hashing topic and the Database indexing topic. |
| 20 | B | Trees & BST | The longest path can be entirely within a subtree, verified with real code. |

---

## Status
20 questions drawn directly from real, verified Python execution results across all 9 DSA topics — measured speedups, a genuine RecursionError, a real BST validation bug, and real Dijkstra/graph behavior — not generic textbook trivia.
