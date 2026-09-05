# Python Cheatsheet — DSA Topic 7 (Graphs)

**Companion to:** DSA_Topic7_Graphs.md
**Format:** Signature → Top usage → One verified runnable example per entry

---

## Adjacency List Representation

```python
graph = {'A': ['B', 'C'], 'B': ['A', 'D'], ...}   # unweighted
weighted_graph = {'A': [('B', 4), ('C', 1)], ...}  # weighted: (neighbor, weight) tuples
```
O(V+E) space — the standard representation for sparse graphs in coding assessments.

---

## BFS Template

```python
def bfs(graph, start):
    visited = {start}
    q = deque([start])
    while q:
        node = q.popleft()
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                q.append(neighbor)
```
Verified: `['A', 'B', 'C', 'D', 'E']` — explores level by level via a real queue.

---

## Directed-Graph Cycle Detection Template (3-Color)

```python
def has_cycle(graph):
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}
    def dfs(node):
        color[node] = GRAY
        for nb in graph.get(node, []):
            if color.get(nb, WHITE) == GRAY: return True
            if color.get(nb, WHITE) == WHITE and dfs(nb): return True
        color[node] = BLACK
        return False
    return any(dfs(n) for n in graph if color[n] == WHITE)
```
Verified: correctly distinguishes a real cycle from a DAG.

---

## Topological Sort Template (Kahn's Algorithm)

```python
def topo_sort(graph):
    in_degree = {n: 0 for n in graph}
    for n in graph:
        for nb in graph[n]: in_degree[nb] += 1
    q = deque([n for n in graph if in_degree[n] == 0])
    order = []
    while q:
        n = q.popleft()
        order.append(n)
        for nb in graph[n]:
            in_degree[nb] -= 1
            if in_degree[nb] == 0: q.append(nb)
    return order if len(order) == len(graph) else None   # None = cycle detected
```
Verified: real DAG → full order; real cyclic graph → `None`.

---

## Dijkstra's Algorithm Template

```python
def dijkstra(graph, start):
    distances = {n: float('inf') for n in graph}
    distances[start] = 0
    pq = [(0, start)]
    visited = set()
    while pq:
        d, node = heapq.heappop(pq)
        if node in visited: continue
        visited.add(node)
        for nb, w in graph[node]:
            if d + w < distances[nb]:
                distances[nb] = d + w
                heapq.heappush(pq, (d + w, nb))
    return distances
```
Verified: correctly found a 3-edge path (weight 4) shorter than a 2-edge path (weight 5).

---

## Union-Find Template (With Path Compression)

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
        rx, ry = self.find(x), self.find(y)
        if rx == ry: return False
        if self.rank[rx] < self.rank[ry]: rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]: self.rank[rx] += 1
        return True
```
Verified: correctly identified connected components and answered connectivity queries.

---

## Grid BFS Template (Number of Islands Pattern)

```python
DIRECTIONS = [(-1,0),(1,0),(0,-1),(0,1)]
def bfs_from(grid, r, c, visited):
    q = deque([(r,c)]); visited.add((r,c))
    while q:
        row, col = q.popleft()
        for dr, dc in DIRECTIONS:
            nr, nc = row+dr, col+dc
            if (0<=nr<len(grid) and 0<=nc<len(grid[0])
                and grid[nr][nc]=='1' and (nr,nc) not in visited):
                visited.add((nr,nc)); q.append((nr,nc))
```
Verified: real 4-row grid correctly counted as 3 separate islands. A grid IS a graph — cells are nodes, adjacency is up/down/left/right.

---

## Status
6 core algorithm templates verified with real executed output in the main Topic 7 doc.
