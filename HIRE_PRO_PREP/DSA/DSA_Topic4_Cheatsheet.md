# Python Cheatsheet — DSA Topic 4 (Linked Lists)

**Companion to:** DSA_Topic4_Linked_Lists.md
**Format:** Signature → Top usage → One verified runnable example per entry

---

## `ListNode` — The Base Building Block

**Signature:**
```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
```
Every pattern below operates on chains of these — no built-in Python linked list type exists; this class is the standard way to represent one for coding assessments.

---

## Dummy/Sentinel Node Pattern

**Signature:**
```python
dummy = ListNode(0, head)   # or ListNode() for building a new list from scratch
```

| Use case | Why it helps |
|---|---|
| Deletion | Eliminates the special case for deleting the head — verified to correctly handle it via one unified code path |
| Building a new list (merge, filter) | `curr = dummy; ... ; return dummy.next` avoids special-casing the first node appended |

---

## Reversal — Iterative Three-Pointer Template

```python
def reverse_iterative(head):
    prev = None
    curr = head
    while curr:
        next_node = curr.next
        curr.next = prev
        prev = curr
        curr = next_node
    return prev
```
O(n) time, O(1) space — verified: `[1,2,3,4,5]` → `[5,4,3,2,1]`.

---

## Fast/Slow Pointer Template (Middle-Finding AND Cycle Detection)

```python
slow = fast = head
while fast and fast.next:
    slow = slow.next
    fast = fast.next.next
# after the loop: slow is at the middle (if no cycle)
# during the loop: `if slow is fast:` catches a cycle
```

| Application | Verified result |
|---|---|
| Find middle | `[1,2,3,4,5]` → 3; `[1,2,3,4,5,6]` → 4 (second middle, even length) |
| Detect cycle | Real physically-constructed cycle correctly detected as `True` |
| Find cycle start | Reset one pointer to `head`, advance both at equal speed until they meet — verified to correctly locate the real entry node |

---

## Merge Two Sorted Lists Template

```python
dummy = ListNode()
curr = dummy
while l1 and l2:
    if l1.val <= l2.val:
        curr.next, l1 = l1, l1.next
    else:
        curr.next, l2 = l2, l2.next
    curr = curr.next
curr.next = l1 if l1 else l2
return dummy.next
```
Verified: `[1,3,5,7]` + `[2,4,6]` → `[1,2,3,4,5,6,7]`. Reuses existing nodes — O(1) extra space beyond the dummy.

---

## Status
5 core templates verified with real executed output in the main Topic 4 doc, covering deletion, reversal, middle-finding, cycle detection/location, and merging.
