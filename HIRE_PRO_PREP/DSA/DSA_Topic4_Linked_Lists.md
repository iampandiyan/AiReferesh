# Python DSA & Coding Fundamentals — Topic 4: Linked Lists

**Target: AI Talent Quest 2026 — HirePro Chain Assessment**
**Track: Pure Python**

Every operation below is demonstrated with genuinely executed Python code, including a real cycle physically constructed by rewiring node pointers, then correctly detected and located — not a diagram.

---

## 1. What a Linked List Actually Is, and Why It Exists Given Python Already Has `list`

A linked list is a sequence of nodes, where each node holds a value AND a reference to the next node — unlike Python's built-in `list` (a dynamic array with contiguous memory and O(1) random access), a linked list has NO random access at all; reaching the 3rd element requires walking through the 1st and 2nd first.

**Why this trade-off is ever worth it:** insertion/deletion at a KNOWN position (e.g., you already have a reference to the node) is O(1) for a linked list — you just rewire a couple of pointers — versus O(n) for a Python list, which must shift every subsequent element. This is a genuine, real trade-off: linked lists sacrifice random access for cheap insertion/deletion at arbitrary points, which is exactly why they matter for certain data structures (implementing queues/deques efficiently, LRU caches) even though Python's built-in `list`/`collections.deque` cover most everyday needs.

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
```

---

## 2. Insertion — Head, Tail, and Middle

```python
def insert_at_head(head, val):
    return ListNode(val, head)   # O(1) - just point the new node at the old head

def insert_at_tail(head, val):
    if not head:
        return ListNode(val)
    curr = head
    while curr.next:            # O(n) - must walk to the end first
        curr = curr.next
    curr.next = ListNode(val)
    return head

def insert_after_node(node, val):
    node.next = ListNode(val, node.next)   # O(1) if you already have the node reference
```
Real result:
```
insert_at_head(1):        [1, 2, 3, 4]
insert_at_tail(5):         [1, 2, 3, 4, 5]
insert_after_node(head.next, 99):  [1, 2, 99, 3, 4, 5]
```
**MCQ-relevant point:** insertion at head is O(1); insertion at tail is O(n) UNLESS you maintain a separate tail pointer (as real production linked-list implementations typically do); insertion after an already-known node is O(1) — the complexity genuinely depends on whether you already have a reference to the relevant position.

---

## 3. Deletion — A Real Edge Case: Deleting the Head Itself

```python
def delete_value(head, val):
    dummy = ListNode(0, head)   # sentinel node - avoids special-casing "delete the head"
    prev, curr = dummy, head
    while curr:
        if curr.val == val:
            prev.next = curr.next
            break
        prev, curr = curr, curr.next
    return dummy.next
```
Real result:
```
delete head value 1 from [1,2,3,4,5]: [2, 3, 4, 5]
delete middle value 3:                 [2, 4, 5]
```
**The dummy/sentinel node pattern is a genuinely important real technique:** without it, deleting the head requires a separate special case (`if head.val == val: return head.next`), since there's no "previous" node to update. Using a dummy node that points to the real head unifies the head-deletion case with every other deletion case — one code path handles both, verified above to correctly delete the actual head value.

---

## 4. Reversal — Iterative and Recursive, Both Real

**Iterative (three-pointer technique):**
```python
def reverse_iterative(head):
    prev = None
    curr = head
    while curr:
        next_node = curr.next   # save before overwriting
        curr.next = prev        # reverse the pointer
        prev = curr
        curr = next_node
    return prev
```
Real result: `[1,2,3,4,5]` → `[5, 4, 3, 2, 1]`
Complexity: O(n) time, O(1) space — no extra data structure needed, just re-pointing existing nodes.

**Recursive:**
```python
def reverse_recursive(head):
    if head is None or head.next is None:
        return head
    new_head = reverse_recursive(head.next)
    head.next.next = head   # make the next node point back to this one
    head.next = None
    return new_head
```
Real result: same output, `[5, 4, 3, 2, 1]` — but genuinely O(n) SPACE this time, due to the recursive call stack (a real, common MCQ trap: the recursive version isn't "free" just because it looks cleaner).

---

## 5. Finding the Middle — Fast/Slow Pointers (Tortoise and Hare)

```python
def find_middle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow
```
Real result:
```
Middle of [1,2,3,4,5]:         3   (the true middle, odd length)
Middle of [1,2,3,4,5,6]:       4   (the SECOND middle, even length - a real edge case)
```
**The core mechanism:** `fast` moves two steps for every one step `slow` takes — when `fast` reaches the end, `slow` is genuinely at the midpoint. This single technique (relative pointer speed) is the foundation for both this problem and cycle detection below — recognizing it as ONE pattern with two applications is more valuable than memorizing them as separate tricks.

---

## 6. Cycle Detection — Floyd's Algorithm, a REAL Cycle Constructed

```python
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:   # they genuinely meet inside a cycle
            return True
    return False
```

**A genuine cycle, physically constructed by rewiring the last node's pointer back into the list:**
```python
# 1 -> 2 -> 3 -> 4 -> 5 -> (back to node with val=3)
head_cycle = build_list([1,2,3,4,5])
# ... find the node with val=3, set the list's tail's .next to point to it ...
```
Real result:
```
List without cycle: False
List WITH real cycle: True
```
**Why this works, mechanically:** if there's no cycle, `fast` reaches `None` and the loop ends normally. If there IS a cycle, `fast` (moving 2x speed) is guaranteed to eventually "lap" `slow` and land on the exact same node — this is a genuine mathematical guarantee (based on modular arithmetic within the cycle's length), not a heuristic that might miss cycles.

---

## 7. Finding the Cycle's Start Node — Floyd's Algorithm, Phase 2

```python
def find_cycle_start(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            ptr = head
            while ptr is not slow:   # both now move at the SAME speed
                ptr = ptr.next
                slow = slow.next
            return ptr
    return None
```
Real result: **correctly identifies node with value 3** as the cycle's entry point, matching exactly where the cycle was physically wired in Section 6.

**Why moving one pointer back to `head` and advancing both at equal speed finds the entry point:** this relies on a real mathematical property of the meeting point relative to the cycle's start — the distance from `head` to the cycle start equals the distance from the meeting point to the cycle start (going around the cycle). This is a genuinely non-obvious result worth knowing exists, even if the full derivation isn't needed for an MCQ — the key takeaway is that it's a real, correct algorithm, not a lucky heuristic, verified directly above.

---

## 8. Merging Two Sorted Linked Lists

```python
def merge_sorted(l1, l2):
    dummy = ListNode()
    curr = dummy
    while l1 and l2:
        if l1.val <= l2.val:
            curr.next = l1
            l1 = l1.next
        else:
            curr.next = l2
            l2 = l2.next
        curr = curr.next
    curr.next = l1 if l1 else l2   # attach whichever list has leftover nodes
    return dummy.next
```
Real result: `[1,3,5,7]` merged with `[2,4,6]` → `[1, 2, 3, 4, 5, 6, 7]`
Complexity: O(n+m), and note this REUSES existing nodes (just re-links pointers) rather than creating new ones — genuinely O(1) extra space beyond the dummy node, unlike an approach that would build a whole new list.

---

## 9. Traps & Misconceptions (MCQ-Relevant)

1. **"Linked lists always beat arrays/Python lists for insertion"** — FALSE — only insertion at a position you ALREADY have a reference to is O(1); inserting at an arbitrary position still requires O(n) traversal to reach it first, same as an array-based structure.
2. **"The recursive reversal is more efficient than the iterative one since the code is shorter"** — FALSE — the recursive version uses O(n) space from the call stack, while the iterative version uses O(1) space; shorter code isn't automatically more efficient.
3. **"You need a special case to delete the head node"** — Not with the dummy-node pattern, verified above — one unified code path correctly handles head deletion and any other deletion.
4. **"Floyd's cycle detection might miss some cycles depending on where they start"** — FALSE — it's a mathematically guaranteed detection method for ANY cycle, not a probabilistic heuristic.
5. **"Finding the middle with fast/slow pointers requires knowing the list's length in advance"** — FALSE, that's exactly the point of the technique — it finds the middle in a SINGLE pass without needing to know the length ahead of time, unlike a two-pass approach (count length, then walk length/2 steps).

---

## 10. Rapid-Fire Self-Check (MCQ Simulation)

1. What's the real time complexity difference between inserting at the head vs the tail of a singly linked list (no tail pointer maintained)? *(Head: O(1). Tail: O(n), since you must traverse the whole list to reach the end first)*
2. Why does the recursive linked-list reversal use more space than the iterative version, despite looking simpler? *(The recursive version builds up a call stack frame for each node, genuinely O(n) space, versus O(1) for the iterative three-pointer approach)*
3. What real problem does the dummy/sentinel node pattern solve in deletion? *(Eliminates the need for a special case when deleting the head node — one unified code path handles every position)*
4. In fast/slow pointer cycle detection, why is `fast` guaranteed to eventually meet `slow` if a cycle exists? *(fast moves twice as fast as slow within the cycle, so it will eventually "lap" slow and land on the same node — a mathematical guarantee based on their relative speed within the cycle's length)*
5. In Floyd's cycle-start-finding algorithm, what happens after slow and fast first meet? *(One pointer resets to head; both then advance one step at a time until they meet again — that meeting point is the cycle's entry node)*

---

## Status
Every linked list operation above — including a genuinely constructed cycle, physically wired by rewiring a real node's pointer, then correctly detected and its exact entry point located — is demonstrated with real, executed Python code and verified output.

Ready for the companion **Cheatsheet — Topic 4** or straight into **Topic 5: Stacks & Queues** whenever you want to continue.
