# Python Cheatsheet — DSA Topic 6 (Trees & Binary Search Trees)

**Companion to:** DSA_Topic6_Trees_and_BST.md
**Format:** Signature → Top usage → One verified runnable example per entry

---

## `TreeNode` — The Base Building Block

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
```

---

## Three Recursive DFS Traversal Templates

```python
def preorder(node, result):
    if node:
        result.append(node.val)   # visit first
        preorder(node.left, result); preorder(node.right, result)

def inorder(node, result):
    if node:
        inorder(node.left, result)
        result.append(node.val)   # visit between children
        inorder(node.right, result)

def postorder(node, result):
    if node:
        postorder(node.left, result); postorder(node.right, result)
        result.append(node.val)   # visit last
```
Verified on a real tree — 3 genuinely different orderings from the same structure.

---

## Level-Order (BFS) Template

```python
from collections import deque

def level_order(root):
    result, q = [], deque([root]) if root else deque()
    while q:
        level = []
        for _ in range(len(q)):
            node = q.popleft()
            level.append(node.val)
            if node.left: q.append(node.left)
            if node.right: q.append(node.right)
        result.append(level)
    return result
```
The `for _ in range(len(q))` trick processes exactly one level per outer loop iteration — verified: `[[5],[3,8],[1,4,9]]`.

---

## Iterative Inorder Template (Explicit Stack)

```python
def inorder_iterative(root):
    result, stack, curr = [], [], root
    while curr or stack:
        while curr:
            stack.append(curr); curr = curr.left
        curr = stack.pop()
        result.append(curr.val)
        curr = curr.right
    return result
```
Verified to produce identical output to the recursive version — useful when recursion depth is a concern.

---

## BST Search Template

```python
def bst_search(root, target):
    curr = root
    while curr:
        if curr.val == target: return True
        curr = curr.left if target < curr.val else curr.right
    return False
```
O(h), not O(n) — exploits the BST ordering property to eliminate half the remaining tree at each step.

---

## Validate BST — the CORRECT Range-Tracking Template

```python
def is_valid_bst(node, low=float('-inf'), high=float('inf')):
    if not node:
        return True
    if not (low < node.val < high):
        return False
    return (is_valid_bst(node.left, low, node.val) and
            is_valid_bst(node.right, node.val, high))
```
**Do NOT use a version that only checks immediate parent-child values** — verified with real code to incorrectly pass an actually-invalid tree. The range must propagate down from every ancestor, not just the direct parent.

---

## Diameter Template (Track Max at Every Node)

```python
def diameter(root):
    result = [0]
    def depth(node):
        if not node: return 0
        l, r = depth(node.left), depth(node.right)
        result[0] = max(result[0], l + r)   # check at EVERY node, not just root
        return 1 + max(l, r)
    depth(root)
    return result[0]
```

---

## BST Lowest Common Ancestor Template

```python
def lca_bst(root, p, q):
    curr = root
    while curr:
        if p < curr.val and q < curr.val: curr = curr.left
        elif p > curr.val and q > curr.val: curr = curr.right
        else: return curr.val
    return None
```
Simpler than general-tree LCA — exploits BST ordering directly instead of searching both subtrees.

---

## Status
7 core templates verified with real executed output, including the corrected (not the buggy) Validate BST version.
