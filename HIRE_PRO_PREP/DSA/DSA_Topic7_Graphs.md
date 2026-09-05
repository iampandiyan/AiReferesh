# Python DSA & Coding Fundamentals — Topic 7: Graphs

**Target: AI Talent Quest 2026 — HirePro Chain Assessment**
**Track: Pure Python**

Every algorithm below is demonstrated with genuinely executed Python code — including Dijkstra's algorithm real proof that it found a genuinely shorter multi-hop path over a shorter-looking direct edge, and a real cycle detected and correctly used to invalidate a topological sort.

---

## 1. What a Graph Actually Is, and the Representation That Matters Most

A graph is a set of nodes (vertices) connected by edges — more general than a tree (Topic 6), since a graph can have cycles and a node can have any number of connections, not just a fixed "left/right" structure. The standard representation for coding assessments is the **adjacency list** — a dict mapping each node to a list of its neighbors:
```python
graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D'],
    'C': ['A', 'D'],
    'D': ['B', 'C', 'E'],
    'E': ['D']
}
```
This is space-efficient for SPARSE graphs (most real-world graphs) — O(V + E) space, versus an adjacency MATRIX's O(V²), which only makes sense for genuinely dense graphs.

---

## 2. BFS and DFS — Real Traversal, Both Verified

```python
from collections import deque

def bfs(graph, start):
    visited = {start}
    order = []
    q = deque([start])
    while q:
        node = q.popleft()
        order.append(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                q.append(neighbor)
    return order

print(bfs(graph, 'A'))   # ['A', 'B', 'C', 'D', 'E']
```
```python
def dfs_recursive(graph, node, visited=None, order=None):
    if visited is None: visited = set()
    if order is None: order = []
    visited.add(node)
    order.append(node)
    for neighbor in graph[node]:
        if neighbor not in visited:
            dfs_recursive(graph, neighbor, visited, order)
    return order

print(dfs_recursive(graph, 'A'))   # ['A', 'B', 'D', 'C', 'E']
```
Both BFS (Topic 6's `deque`-based pattern applied to a general graph) and the recursive DFS were verified to have a genuine, correct iterative counterpart too — same relationship as Topic 6's iterative-vs-recursive tree traversal.

---

## 3. Cycle Detection in a Directed Graph — Real 3-Color Approach

```python
def has_cycle_directed(graph):
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}

    def dfs(node):
        color[node] = GRAY   # currently in the recursion stack
        for neighbor in graph.get(node, []):
            if color.get(neighbor, WHITE) == GRAY:
                return True   # back edge to a node in the CURRENT path = real cycle
            if color.get(neighbor, WHITE) == WHITE and dfs(neighbor):
                return True
        color[node] = BLACK   # done processing, no longer in recursion stack
        return False

    return any(dfs(node) for node in graph if color[node] == WHITE)
```
Real results:
```
Acyclic (A->B->C): False
Cyclic (A->B->C->A): True
```
**The real reason 3 colors (not just visited/unvisited) are needed:** a plain "visited" set can't distinguish between "already fully processed, safe" (BLACK) and "currently being processed, on the active recursion path" (GRAY) — only revisiting a GRAY node genuinely indicates a cycle. Revisiting a BLACK node just means the graph has multiple paths to it, which is completely normal in a DAG and not a cycle at all.

---

## 4. Topological Sort — Kahn's Algorithm, Real In-Degree Tracking

```python
def topological_sort(graph):
    in_degree = {node: 0 for node in graph}
    for node in graph:
        for neighbor in graph[node]:
            in_degree[neighbor] += 1

    q = deque([node for node in graph if in_degree[node] == 0])
    order = []
    while q:
        node = q.popleft()
        order.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                q.append(neighbor)

    if len(order) != len(graph):
        return None   # real cycle - no valid order exists
    return order

dag = {'A': ['C'], 'B': ['C'], 'C': ['D'], 'D': []}
print(topological_sort(dag))          # ['A', 'B', 'C', 'D']
print(topological_sort(cyclic_graph)) # None
```
**Genuine, verified proof that Kahn's algorithm doubles as cycle detection:** on the cyclic graph, some nodes NEVER reach in-degree 0 (since they're stuck depending on each other in the cycle), so `order` ends up shorter than the full node count, and the function correctly returns `None`. This connects directly to Section 3 — two independent algorithms (3-color DFS, Kahn's BFS) both correctly detect the same real cycle, from different angles.

---

## 5. Dijkstra's Algorithm — Real Weighted Shortest Path, Genuinely Verified

```python
import heapq

def dijkstra(graph, start):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    pq = [(0, start)]
    visited = set()

    while pq:
        curr_dist, node = heapq.heappop(pq)
        if node in visited:
            continue
        visited.add(node)
        for neighbor, weight in graph[node]:
            new_dist = curr_dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor))
    return distances

weighted_graph = {
    'A': [('B', 4), ('C', 1)],
    'B': [('D', 1)],
    'C': [('B', 2), ('D', 5)],
    'D': []
}
print(dijkstra(weighted_graph, 'A'))
```
Real output: `{'A': 0, 'B': 3, 'C': 1, 'D': 4}`

**A genuinely verified, non-obvious result:** the shortest path to D is 4, via A→C→B→D (1+2+1=4) — NOT the seemingly-direct A→B→D (4+1=5). Dijkstra's algorithm correctly found the multi-hop path is actually shorter, exactly the kind of result that would be easy to get wrong by eyeballing the graph. The `heapq`-based priority queue is what makes this efficient — always exploring the currently-closest unvisited node next, using Topic 1's heap knowledge directly applied to a genuinely different domain.

---

## 6. Union-Find (Disjoint Set) — Real Path Compression

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])   # path compression
        return self.parent[x]

    def union(self, x, y):
        root_x, root_y = self.find(x), self.find(y)
        if root_x == root_y:
            return False
        if self.rank[root_x] < self.rank[root_y]:
            root_x, root_y = root_y, root_x
        self.parent[root_y] = root_x
        if self.rank[root_x] == self.rank[root_y]:
            self.rank[root_x] += 1
        return True
```
Real result after unioning `(0,1), (1,2), (3,4)` on 6 elements:
```
Connected components: {0: [0, 1, 2], 3: [3, 4], 5: [5]}
Are 0 and 2 connected? True   <- via the union chain 0-1-2, correctly resolved
Are 0 and 5 connected? False
```
**Why path compression matters:** the line `self.parent[x] = self.find(self.parent[x])` flattens the tree structure every time `find` is called, so future lookups for the same element become O(1) instead of re-walking a potentially long chain — this genuinely makes Union-Find operations amortized nearly O(1) (technically O(α(n)), the inverse Ackermann function, effectively constant for any realistic input size).

---

## 7. Number of Islands — Real 2D Grid BFS

```python
def num_islands(grid):
    rows, cols = len(grid), len(grid[0])
    visited = set()
    count = 0

    def bfs_island(r, c):
        q = deque([(r,c)])
        visited.add((r,c))
        while q:
            row, col = q.popleft()
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = row+dr, col+dc
                if (0 <= nr < rows and 0 <= nc < cols and
                    grid[nr][nc] == '1' and (nr,nc) not in visited):
                    visited.add((nr,nc))
                    q.append((nr,nc))

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1' and (r,c) not in visited:
                count += 1
                bfs_island(r, c)
    return count
```
Real grid and result:
```
1 1 0 0 0
1 1 0 0 0
0 0 1 0 0
0 0 0 1 1
Number of islands: 3
```
**The real, direct connection to earlier topics:** a 2D grid is itself a graph — each cell is a node, and adjacent cells (up/down/left/right) are edges. This is a genuinely common real-world framing worth recognizing: "grid traversal" problems and "graph traversal" problems are the SAME algorithm applied to a specific graph shape (a grid graph), not a separate category to learn from scratch.

---

## 8. Traps & Misconceptions (MCQ-Relevant)

1. **"A simple visited/unvisited set is enough to detect a cycle in a directed graph"** — FALSE, directly explained — you need to distinguish "on the current recursion path" (GRAY) from "fully processed, safe" (BLACK); revisiting a BLACK node is normal in a DAG, not a cycle.
2. **"Topological sort only works on graphs without cycles"** — More precisely: topological sort only EXISTS for acyclic graphs, and Kahn's algorithm genuinely detects this itself by producing a shorter-than-expected order, verified above — it doesn't need a separate cycle check beforehand.
3. **"Dijkstra's algorithm always picks the path with the fewest edges"** — FALSE, directly disproven — it found the shortest-WEIGHT path (A→C→B→D, 3 edges, weight 4), not the fewest-edge path (A→B→D, 2 edges, weight 5).
4. **"Union-Find without path compression has the same performance as with it"** — Not true at scale — path compression flattens chains during lookups, making subsequent `find` calls dramatically faster; without it, `find` can degrade toward O(n) for a long unbalanced chain.
5. **"Grid/matrix traversal problems require different algorithms than graph traversal"** — FALSE, as demonstrated — Number of Islands is literally BFS on a graph where each grid cell is a node and adjacency is defined by up/down/left/right neighbors.

---

## 9. Rapid-Fire Self-Check (MCQ Simulation)

1. Why does directed-graph cycle detection need 3 colors (white/gray/black) instead of a simple visited set? *(Must distinguish nodes currently on the active recursion path (gray) from fully-processed nodes (black) — only a back-edge to a GRAY node indicates a genuine cycle)*
2. How does Kahn's algorithm (topological sort) detect a cycle without a separate check? *(If the graph has a cycle, some nodes never reach in-degree 0, so the final order is shorter than the total node count)*
3. In the verified Dijkstra example, why was the 3-edge path A→C→B→D chosen over the 2-edge path A→B→D? *(Dijkstra minimizes total edge WEIGHT, not edge count — 1+2+1=4 is genuinely less than 4+1=5)*
4. What does path compression in Union-Find's `find` method actually do? *(Flattens the tree by making every visited node point directly to the root during the lookup, so future finds for those nodes are much faster)*
5. What single insight connects "Number of Islands" to standard graph BFS? *(A 2D grid IS a graph — each cell is a node, and up/down/left/right adjacency defines the edges; it's the same BFS algorithm, not a different one)*

---

## Status
Every graph algorithm above — BFS, DFS, directed cycle detection, topological sort, Dijkstra's shortest path, Union-Find with path compression, and grid-based BFS — is demonstrated with real, executed Python code, including a genuinely non-obvious Dijkstra result (a 3-edge path beating a 2-edge path) and a real cycle correctly detected by two independent algorithms.

Ready for the companion **Cheatsheet — Topic 7** or straight into **Topic 8: Sorting & Searching** whenever you want to continue.
