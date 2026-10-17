"""Exercise 3 - insert and benchmark a Qdrant-like in-memory vector store.

Run: python exercise_03_qdrant_vs_pgvector_sim.py

Uses only the standard library and a simple in-memory API-shaped store. This
does not contact Qdrant or PostgreSQL. To benchmark real infrastructure, start
Qdrant/Postgres separately and use identical vectors, queries, filters, and K.

Lesson: report p50/p95 and recall against a shared exact baseline; never present
small local simulator timings as a hosted database comparison.
"""

import hashlib
import math
import random
import statistics
import time


DIM = 48
COUNT = 300
K = 10


def embed(text):
    vector = [0.0] * DIM
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode()).digest()
        vector[int.from_bytes(digest[:4], "big") % DIM] += 1 if digest[4] & 1 else -1
    norm = math.sqrt(sum(value * value for value in vector)) or 1
    return [value / norm for value in vector]


def similarity(a, b):
    return sum(x * y for x, y in zip(a, b))


class InMemoryVectorStore:
    def __init__(self):
        self.points = {}

    def upsert(self, point_id, vector, payload):
        self.points[point_id] = (vector, payload)

    def search(self, query, limit):
        return sorted(
            (
                (similarity(query, vector), point_id, payload)
                for point_id, (vector, payload) in self.points.items()
            ),
            reverse=True,
        )[:limit]


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)]


def main():
    rng = random.Random(7)
    records = [
        (i, f"synthetic policy record {i} topic {rng.choice(['GDPR', 'OCC', 'insurance'])}")
        for i in range(COUNT)
    ]
    store = InMemoryVectorStore()
    build_start = time.perf_counter()
    for point_id, text in records:
        store.upsert(point_id, embed(text), {"text": text})
    build_ms = (time.perf_counter() - build_start) * 1000

    queries = [embed(f"GDPR policy topic {i}") for i in range(40)]
    latencies = []
    recall = []
    for query in queries:
        start = time.perf_counter()
        results = store.search(query, K)
        latencies.append((time.perf_counter() - start) * 1000)
        exact = sorted(
            records,
            key=lambda row: similarity(query, embed(row[1])),
            reverse=True,
        )[:K]
        recall.append(len({r[1] for r in results} & {row[0] for row in exact}) / K)

    print(f"Inserted {len(store.points)} points into in-memory Qdrant-style store.")
    print(f"Local insert time: {build_ms:.3f} ms")
    print(
        f"Query p50={statistics.median(latencies):.4f} ms "
        f"p95={percentile(latencies, 0.95):.4f} ms "
        f"recall@{K}={statistics.mean(recall):.3f}"
    )
    print("Comparison note: these are Python in-memory timings, not Qdrant vs pgvector results.")


if __name__ == "__main__":
    main()
