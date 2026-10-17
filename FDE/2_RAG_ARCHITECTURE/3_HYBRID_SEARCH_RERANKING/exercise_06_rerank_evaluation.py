"""Exercise 6: evaluate reranking with hit rate, nDCG, and MRR by query slice.

Run: python exercise_06_rerank_evaluation.py

Behavior: evaluates hand-crafted hybrid and reranked orders against graded
relevance labels. It deliberately includes an exact-query slice where reranking
does not help, so routing decisions can be discussed.

Lesson: overall metrics can hide regressions. Compare slices and include latency
and cost before enabling a reranker for every request.
"""

import math


CASES = [
    ("exact", [3, 2, 1, 0], [3, 2, 1, 0]),
    ("exact", [2, 3, 1, 0], [2, 3, 1, 0]),
    ("paraphrase", [1, 0, 0, 0], [3, 2, 1, 0]),
    ("paraphrase", [0, 1, 0, 0], [3, 2, 1, 0]),
]


def hit_at_k(relevances, k=3):
    return float(any(relevances[:k]))


def ndcg_at_k(relevances, k=3):
    dcg = sum(rel / math.log2(rank + 2) for rank, rel in enumerate(relevances[:k]))
    ideal = sorted(relevances, reverse=True)[:k]
    idcg = sum(rel / math.log2(rank + 2) for rank, rel in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def reciprocal_rank(relevances):
    return next(
        (1 / (rank + 1) for rank, rel in enumerate(relevances) if rel > 0),
        0.0,
    )


def averages(rows):
    count = len(rows)
    return tuple(sum(metric(row) for row in rows) / count for metric in (hit_at_k, ndcg_at_k, reciprocal_rank))


def main():
    for slice_name in ("all", "exact", "paraphrase"):
        rows = CASES if slice_name == "all" else [row for row in CASES if row[0] == slice_name]
        before = averages([row[1] for row in rows])
        after = averages([row[2] for row in rows])
        print(
            f"{slice_name:10} "
            f"hit@3 {before[0]:.2f}->{after[0]:.2f}  "
            f"nDCG@3 {before[1]:.3f}->{after[1]:.3f}  "
            f"MRR {before[2]:.3f}->{after[2]:.3f}"
        )
    print("\nRouting: keep the exact slice on the hybrid order when reranking adds no nDCG;")
    print("apply reranking to the paraphrase slice only when measured gains justify its cost.")
    print("These are deterministic teaching labels, not live-provider evaluation results.")


if __name__ == "__main__":
    main()
"""
all        hit@3 1.00->1.00  nDCG@3 0.888->0.981  MRR 0.875->1.000
exact      hit@3 1.00->1.00  nDCG@3 0.961->0.961  MRR 1.000->1.000
paraphrase hit@3 1.00->1.00  nDCG@3 0.815->1.000  MRR 0.750->1.000

Routing: keep the exact slice on the hybrid order when reranking adds no nDCG;
apply reranking to the paraphrase slice only when measured gains justify its cost.
These are deterministic teaching labels, not live-provider evaluation results.

"""