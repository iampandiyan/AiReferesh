"""Exercise 2 - compare HNSW-style and IVF-style ANN search methodology.

Run: python exercise_02_hnsw_vs_ivf_benchmark.py

This uses only Python's standard library. It implements small graph-greedy and
centroid-partition search surrogates; neither is a production HNSW or IVF index.
The reported timings are for this machine and tiny synthetic vectors only.

Lesson: benchmark build time, p50/p95 query latency, and recall against exact
search on the same corpus. The 200-row toy corpus cannot establish scale behavior.
"""

import math
import random
import statistics
import time


DIM = 24
N = 200
K = 5


def normalize(vector):
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def dot(left, right):
    return sum(a * b for a, b in zip(left, right))


def make_data():
    rng = random.Random(42)
    vectors = [normalize([rng.uniform(-1, 1) for _ in range(DIM)]) for _ in range(N)]
    queries = [normalize([rng.uniform(-1, 1) for _ in range(DIM)]) for _ in range(30)]
    return vectors, queries


def exact_search(vectors, query):
    return sorted(range(len(vectors)), key=lambda i: dot(vectors[i], query), reverse=True)[:K]


def build_graph(vectors, degree=8):
    started = time.perf_counter()
    graph = []
    for i, vector in enumerate(vectors):
        neighbors = sorted(
            (j for j in range(len(vectors)) if j != i),
            key=lambda j: dot(vector, vectors[j]),
            reverse=True,
        )[:degree]
        graph.append(neighbors)
    return graph, (time.perf_counter() - started) * 1000


def graph_search(vectors, graph, query, ef=45):
    current = 0
    visited = {current}
    for _ in range(ef):
        candidates = [i for i in graph[current] if i not in visited]
        if not candidates:
            break
        visited.update(candidates)
        next_node = max(candidates, key=lambda i: dot(vectors[i], query))
        if dot(vectors[next_node], query) <= dot(vectors[current], query):
            break
        current = next_node
    pool = visited | set(graph[current])
    return sorted(pool, key=lambda i: dot(vectors[i], query), reverse=True)[:K]


def build_ivf(vectors, n_lists=10):
    started = time.perf_counter()
    centers = [vectors[i * len(vectors) // n_lists] for i in range(n_lists)]
    lists = [[] for _ in centers]
    for index, vector in enumerate(vectors):
        owner = max(range(n_lists), key=lambda j: dot(vector, centers[j]))
        lists[owner].append(index)
    return centers, lists, (time.perf_counter() - started) * 1000


def ivf_search(vectors, centers, lists, query, n_probe=3):
    selected = sorted(
        range(len(centers)), key=lambda i: dot(query, centers[i]), reverse=True
    )[:n_probe]
    candidates = [item for list_id in selected for item in lists[list_id]]
    return sorted(candidates, key=lambda i: dot(vectors[i], query), reverse=True)[:K]


def benchmark(label, search_fn, queries, truth):
    durations = []
    recalls = []
    for query, expected in zip(queries, truth):
        started = time.perf_counter()
        results = search_fn(query)
        durations.append((time.perf_counter() - started) * 1000)
        recalls.append(len(set(results) & set(expected)) / K)
    ordered = sorted(durations)
    p50 = statistics.median(ordered)
    p95 = ordered[min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1)]
    print(f"{label:12} p50={p50:.4f} ms p95={p95:.4f} ms recall@5={statistics.mean(recalls):.3f}")


def main():
    vectors, queries = make_data()
    truth = [exact_search(vectors, query) for query in queries]

    graph, graph_build_ms = build_graph(vectors)
    centers, lists, ivf_build_ms = build_ivf(vectors)
    print(f"Toy index: {N} vectors x {DIM} dimensions; {len(queries)} queries; K={K}")
    print(f"HNSW-style graph build: {graph_build_ms:.3f} ms (degree=8)")
    print(f"IVF-style partition build: {ivf_build_ms:.3f} ms (lists={len(lists)})")
    benchmark("exact baseline", lambda q: exact_search(vectors, q), queries, truth)
    benchmark("graph search", lambda q: graph_search(vectors, graph, q), queries, truth)
    benchmark(
        "IVF search",
        lambda q: ivf_search(vectors, centers, lists, q),
        queries,
        truth,
    )
    print("Pick by measured recall/latency and update pattern; this toy surrogate is not a real HNSW-vs-IVF benchmark.")


if __name__ == "__main__":
    main()
