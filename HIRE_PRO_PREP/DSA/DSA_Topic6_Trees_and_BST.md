# Python DSA & Coding Fundamentals — Topic 6: Trees & Binary Search Trees

**Target: AI Talent Quest 2026 — HirePro Chain Assessment**
**Track: Pure Python**

This topic includes a genuine bug caught live: a naive "Validate BST" implementation that checks only immediate parent-child relationships incorrectly says an invalid tree is valid — proven with real code, then fixed with a correct range-tracking version.

---

## 1. What a Tree Actually Is, and Why a BST Is a Special Case

A **tree** is a hierarchical structure of nodes, where each node has at most a fixed number of children (a "binary tree" allows at most 2 — left and right) and there's exactly one path from the root to any given node (no cycles, unlike a general graph). A **Binary Search Tree (BST)** adds one crucial ordering rule: for every node, everything in its LEFT subtree is smaller, and everything in its RIGHT subtree is larger. This single rule is what makes search, insertion, and deletion all O(h) — where h is the tree's height — instead of O(n): at each node, you can discard an entire half of the remaining tree, the same divide-and-conquer principle behind binary search on a sorted array.

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
```

**Sample tree used throughout:**
```
        5
       / \
      3   8
     / \   \
    1   4   9
```

---

## 2. The Three DFS Traversal Orders — Real, Distinct Results

```python
def preorder(node, result=None):
    if result is None: result = []
    if node:
        result.append(node.val)      # visit BEFORE children
        preorder(node.left, result)
        preorder(node.right, result)
    return result

def inorder(node, result=None):
    if result is None: result = []
    if node:
        inorder(node.left, result)
        result.append(node.val)      # visit BETWEEN children
        inorder(node.right, result)
    return result

def postorder(node, result=None):
    if result is None: result = []
    if node:
        postorder(node.left, result)
        postorder(node.right, result)
        result.append(node.val)      # visit AFTER children
    return result
```
Real results on the sample tree:
```
preorder:  [5, 3, 1, 4, 8, 9]
inorder:   [1, 3, 4, 5, 8, 9]
postorder: [1, 4, 3, 9, 8, 5]
```

---

## 3. Real Proof: Inorder Traversal of a BST Is Genuinely Sorted

```python
print(inorder(tree) == sorted(inorder(tree)))
```
Real output: `True`

This isn't a coincidence — it's a direct, provable CONSEQUENCE of the BST ordering property: inorder visits left subtree (all smaller values) → node → right subtree (all larger values), which for a valid BST always produces ascending order. **This fact is genuinely useful, not just trivia:** it's the standard technique for validating a BST (compare inorder output to its sorted version) and for converting a BST to a sorted array in O(n).

---

## 4. Level-Order Traversal (BFS) — Using a Real Queue

```python
from collections import deque

def level_order(root):
    if not root: return []
    result = []
    q = deque([root])
    while q:
        level = []
        for _ in range(len(q)):   # process exactly one LEVEL at a time
            node = q.popleft()
            level.append(node.val)
            if node.left: q.append(node.left)
            if node.right: q.append(node.right)
        result.append(level)
    return result

print(level_order(tree))   # [[5], [3, 8], [1, 4, 9]]
```
Note `deque` (Topic 5), not `list` — a queue is the natural fit for BFS, exploring nodes in the order they're discovered, level by level.

---

## 5. Iterative Inorder — Real Stack-Based, No Recursion

```python
def inorder_iterative(root):
    result = []
    stack = []
    curr = root
    while curr or stack:
        while curr:
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()
        result.append(curr.val)
        curr = curr.right
    return result

print(inorder_iterative(tree) == inorder(tree))   # True - genuinely matches the recursive version
```
This is a real, direct application of Topic 5's stack concept to tree traversal — the explicit `stack` here literally replaces what the RECURSIVE version's call stack was doing implicitly, useful when recursion depth is a genuine concern (very deep/unbalanced trees can hit Python's recursion limit).

---

## 6. BST Search — O(h), Not O(n)

```python
def bst_search(root, target):
    curr = root
    while curr:
        if curr.val == target:
            return True
        curr = curr.left if target < curr.val else curr.right
    return False

print(bst_search(tree, 4))   # True
print(bst_search(tree, 7))   # False
```
At each step, the BST ordering property eliminates an entire subtree from consideration — genuinely O(h) where h is tree height (O(log n) for a balanced tree, but O(n) worst case for a degenerate, unbalanced "linked-list-shaped" tree, a real MCQ-relevant caveat).

---

## 7. Validate BST — A Real Bug Caught and Fixed

**The WRONG, naive approach — only checks immediate parent-child relationships:**
```python
def is_valid_bst_WRONG(node):
    if not node:
        return True
    if node.left and node.left.val >= node.val:
        return False
    if node.right and node.right.val <= node.val:
        return False
    return is_valid_bst_WRONG(node.left) and is_valid_bst_WRONG(node.right)
```

**A tree constructed to expose the bug:** root=5, right child=8, right child's LEFT grandchild=4. Locally, `4 < 8` looks fine to the naive check — but the BST rule requires EVERYTHING in the root's right subtree to be greater than 5, and 4 genuinely isn't.

```python
trap_tree = TreeNode(5, TreeNode(3), TreeNode(8, TreeNode(4), TreeNode(9)))
print(is_valid_bst_WRONG(trap_tree))
```
Real output: **`True`** — the naive check genuinely, incorrectly says this invalid tree is valid.

**The CORRECT approach — tracks a valid (low, high) range for every node, not just its immediate parent:**
```python
def is_valid_bst_CORRECT(node, low=float('-inf'), high=float('inf')):
    if not node:
        return True
    if not (low < node.val < high):
        return False
    return (is_valid_bst_CORRECT(node.left, low, node.val) and
            is_valid_bst_CORRECT(node.right, node.val, high))

print(is_valid_bst_CORRECT(trap_tree))
```
Real output: **`False`** — correctly catches the violation, because the `4` is checked against the range `(5, 8)` inherited from BOTH its parent (8) AND grandparent (5) constraints, not just its immediate parent alone.

**This is a genuinely important, real interview trap:** checking only immediate parent-child relationships is a very common WRONG first instinct for this exact problem — the fix requires realizing that BST validity is a property of the ENTIRE subtree's range, not just adjacent node pairs.

---

## 8. Max Depth (Height)

```python
def max_depth(node):
    if not node:
        return 0
    return 1 + max(max_depth(node.left), max_depth(node.right))

print(max_depth(tree))   # 3
```

---

## 9. Diameter of Binary Tree — A Real Subtlety

```python
def diameter(root):
    result = [0]
    def depth(node):
        if not node:
            return 0
        left_depth = depth(node.left)
        right_depth = depth(node.right)
        result[0] = max(result[0], left_depth + right_depth)   # path THROUGH this node
        return 1 + max(left_depth, right_depth)
    depth(root)
    return result[0]

print(diameter(tree))   # 4
```
**The real subtlety:** the longest path in a tree doesn't necessarily pass through the ROOT — it could be entirely within a subtree. This solution correctly handles that by tracking the best diameter found AT EVERY NODE (via the `result[0] = max(...)` line inside the recursive helper), not just computing it once at the top level.

---

## 10. Lowest Common Ancestor in a BST — Uses the Ordering Property

```python
def lca_bst(root, p, q):
    curr = root
    while curr:
        if p < curr.val and q < curr.val:
            curr = curr.left
        elif p > curr.val and q > curr.val:
            curr = curr.right
        else:
            return curr.val
    return None

print(lca_bst(tree, 1, 4))   # 3
print(lca_bst(tree, 1, 9))   # 5
print(lca_bst(tree, 1, 3))   # 3 - real edge case: one value IS the ancestor of the other
```
This is genuinely simpler and faster than the general-tree LCA algorithm — it exploits the BST ordering: if both targets are smaller than the current node, the LCA must be in the left subtree; if both larger, the right subtree; otherwise, the current node IS the split point (the LCA), verified correctly even in the edge case where one target is itself an ancestor of the other.

---

## 11. Invert Binary Tree — A Real Mirror Swap

```python
def invert_tree(node):
    if not node:
        return None
    node.left, node.right = invert_tree(node.right), invert_tree(node.left)
    return node
```
Real result:
```
before invert (preorder): [5, 3, 1, 4, 8, 9]
after invert (preorder):  [5, 8, 9, 3, 4, 1]
```
Every node's left and right children are genuinely swapped, recursively — a real, complete mirror image of the original tree.

---

## 12. Traps & Misconceptions (MCQ-Relevant)

1. **"Checking that a node's left child is smaller and right child is larger is sufficient to validate a BST"** — FALSE, genuinely proven above with real code — this misses violations from grandparent/higher ancestor constraints; a full range-tracking approach is required.
2. **"BST search is always O(log n)"** — FALSE — it's O(h), and h can be O(n) for a degenerate, unbalanced tree (e.g., a tree built by inserting already-sorted values, which produces a linked-list shape).
3. **"The diameter of a tree always passes through the root"** — FALSE, a real subtlety this section addresses directly — the longest path can be entirely within one subtree, requiring the max to be tracked at every node, not just computed once at the top.
4. **"Iterative traversal is fundamentally different from recursive traversal"** — Not really — the iterative version's explicit stack does the SAME job as the recursive version's implicit call stack, verified to produce identical output.
5. **"Inorder traversal always produces sorted output for any binary tree"** — FALSE — this is specifically a BST property, arising from the ordering rule; a plain (non-BST) binary tree's inorder traversal has no such guarantee.

---

## 13. Rapid-Fire Self-Check (MCQ Simulation)

1. What real bug did the naive BST validation function have, and what specific tree exposed it? *(It only checked immediate parent-child relationships; a tree with root=5, right child=8, and 8's left child=4 passed the naive check since 4<8 locally, but genuinely violated the rule that everything in the root's right subtree must exceed 5)*
2. Why does inorder traversal of a valid BST always produce sorted output? *(Inorder visits left subtree, then node, then right subtree — for a BST, this exactly matches ascending value order by definition of the BST ordering rule)*
3. What real-world tree shape causes BST search to degrade from O(log n) to O(n)? *(A degenerate/unbalanced tree, e.g., one built by inserting already-sorted values — it becomes shaped like a linked list)*
4. Why must the Diameter of Binary Tree solution track the best result at EVERY node, not just the root? *(The longest path in the tree might be entirely within a subtree, not passing through the root at all)*
5. Why is the BST-specific Lowest Common Ancestor algorithm simpler than the general-tree version? *(It directly exploits the BST ordering property to decide which subtree to descend into, rather than needing to search both subtrees as a general tree's LCA algorithm would)*

---

## Status
Every traversal, BST operation, and tree algorithm above is demonstrated with real, executed Python code — most notably a genuine bug in a naive BST validator, proven to incorrectly return `True` on an actual invalid tree, immediately followed by a correct range-tracking fix that properly returns `False` on the identical tree.

Ready for the companion **Cheatsheet — Topic 6** or straight into **Topic 7: Graphs** whenever you want to continue.
