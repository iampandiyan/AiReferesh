"""Exercise 5 - compare vector memory and recall after quantization.

Run: python exercise_05_vector_quantization.py

Uses only Python's standard library. It compares float32-like Python values,
IEEE half precision values, int8 scalar quantization, and one-bit sign codes
with full-precision candidate rescoring.

Lesson: quantization saves memory but may alter nearest-neighbor rankings.
Measure recall against an exact full-precision baseline and account for index
metadata, alignment, and rescoring overhead in a production memory budget.
"""

import math
import random
import struct


DIM = 64
COUNT = 120
K = 10
PROBES = 20


def normalize(vector):
    norm = math.sqrt(sum(value * value for value in vector)) or 1
    return [value / norm for value in vector]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def pack_fp16(vector):
    return [struct.unpack("e", struct.pack("e", value))[0] for value in vector]


def quantize_int8(vectors):
    mins = [min(row[d] for row in vectors) for d in range(DIM)]
    maxs = [max(row[d] for row in vectors) for d in range(DIM)]
    scales = [(maxs[d] - mins[d]) / 255 or 1.0 for d in range(DIM)]
    codes = [
        [max(0, min(255, round((row[d] - mins[d]) / scales[d]))) for d in range(DIM)]
        for row in vectors
    ]
    decoded = [
        [mins[d] + codes[i][d] * scales[d] for d in range(DIM)]
        for i in range(len(vectors))
    ]
    return codes, decoded


def exact_top(query, vectors):
    return sorted(range(len(vectors)), key=lambda i: dot(query, vectors[i]), reverse=True)[:K]


def recall(approx, truth):
    return sum(len(set(a) & set(t)) / K for a, t in zip(approx, truth)) / len(truth)


def main():
    rng = random.Random(42)
    vectors = [normalize([rng.uniform(-1, 1) for _ in range(DIM)]) for _ in range(COUNT)]
    query_ids = rng.sample(range(COUNT), PROBES)
    queries = [vectors[i] for i in query_ids]
    truth = [exact_top(q, vectors) for q in queries]

    fp16_vectors = [pack_fp16(row) for row in vectors]
    fp16_queries = [pack_fp16(row) for row in queries]
    int8_codes, int8_vectors = quantize_int8(vectors)
    packed = [[1 if value >= 0 else 0 for value in row] for row in vectors]
    query_packed = [[1 if value >= 0 else 0 for value in row] for row in queries]
    binary_results = []
    for query, bits, own_id in zip(queries, query_packed, query_ids):
        candidates = sorted(
            range(COUNT),
            key=lambda i: sum(a != b for a, b in zip(bits, packed[i])),
        )[:50]
        candidates = [i for i in candidates if i != own_id]
        binary_results.append(
            sorted(candidates, key=lambda i: dot(query, vectors[i]), reverse=True)[:K]
        )

    fp16_results = [exact_top(q, fp16_vectors) for q in fp16_queries]
    int8_results = [exact_top(q, int8_vectors) for q in queries]
    print(f"{COUNT} vectors x {DIM} dimensions; {PROBES} deterministic probes; recall@{K}")
    print(f"{'representation':20} {'bytes/vector':>12} {'vs fp32':>10} {'recall':>10}")
    print(f"{'float32 baseline':20} {4 * DIM:12} {'1x':>10} {1.0:10.3f}")
    print(f"{'float16':20} {2 * DIM:12} {'2x smaller':>10} {recall(fp16_results, truth):10.3f}")
    print(f"{'int8 scalar':20} {DIM:12} {'4x smaller':>10} {recall(int8_results, truth):10.3f}")
    print(f"{'binary + rescore':20} {DIM // 8:12} {'32x smaller':>10} {recall(binary_results, truth):10.3f}")
    print("Byte counts are raw vector payload estimates; real indexes add metadata and alignment.")


if __name__ == "__main__":
    main()
