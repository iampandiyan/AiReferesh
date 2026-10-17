"""Exercise 4: sweep dense-vs-sparse weights in Weighted RRF.

Run: python exercise_04_weighted_rrf_sweep.py

Behavior: scores deterministic candidate rankings for exact-identifier and
paraphrase queries at alpha values 0, .25, .5, .75, and 1. Alpha weights dense;
1-alpha weights sparse/BM25.

Lesson: query classes can favor different retrieval lanes. Measure by slice and
route the request instead of assuming one global weight is optimal.
"""


ALPHAS = (0.0, 0.25, 0.5, 0.75, 1.0)
CASES = [
    {
        "type": "keyword",
        "query": "AML 4.5.2",
        "gold": "exact",
        "dense": [f"dense_{i}" for i in range(10)] + ["exact"],
        "sparse": ["exact"] + [f"sparse_{i}" for i in range(9)],
    },
    {
        "type": "keyword",
        "query": "SAR filing",
        "gold": "sar",
        "dense": [f"dense_sar_{i}" for i in range(10)] + ["sar"],
        "sparse": ["sar"] + [f"sparse_sar_{i}" for i in range(9)],
    },
    {
        "type": "paraphrase",
        "query": "what rights does a data subject have",
        "gold": "rights",
        "dense": ["rights"] + [f"dense_rights_{i}" for i in range(9)],
        "sparse": [f"sparse_rights_{i}" for i in range(10)] + ["rights"],
    },
    {
        "type": "paraphrase",
        "query": "how can I move my personal information",
        "gold": "portability",
        "dense": ["portability"] + [f"dense_portability_{i}" for i in range(9)],
        "sparse": [f"sparse_portability_{i}" for i in range(10)] + ["portability"],
    },
]


def weighted_rrf(dense_ranks, sparse_ranks, alpha, k=60):
    scores = {}
    for rank, doc_id in enumerate(dense_ranks):
        scores[doc_id] = scores.get(doc_id, 0.0) + alpha / (k + rank)
    for rank, doc_id in enumerate(sparse_ranks):
        scores[doc_id] = scores.get(doc_id, 0.0) + (1 - alpha) / (k + rank)
    return sorted(scores, key=lambda doc_id: (-scores[doc_id], doc_id))


def recall_at_k(results, gold, k=10):
    return int(gold in results[:k])


def main():
    by_type = ("keyword", "paraphrase")
    best = {}
    print("alpha | keyword recall@10 | paraphrase recall@10")
    for alpha in ALPHAS:
        scores = {}
        for query_type in by_type:
            cases = [case for case in CASES if case["type"] == query_type]
            hits = sum(
                recall_at_k(
                    weighted_rrf(case["dense"], case["sparse"], alpha),
                    case["gold"],
                )
                for case in cases
            )
            scores[query_type] = hits / len(cases)
        print(f"{alpha:>5.2f} | {scores['keyword']:>16.0%} | {scores['paraphrase']:>19.0%}")
        for query_type, score in scores.items():
            best[query_type, alpha] = score

    for query_type in by_type:
        tie_break = (lambda value: -value) if query_type == "keyword" else (lambda value: value)
        alpha = max(ALPHAS, key=lambda value: (best[query_type, value], tie_break(value)))
        print(f"Best {query_type} alpha: {alpha:.2f}")
    print("Routing hint: start exact identifiers with lower alpha, paraphrases with higher alpha.")


if __name__ == "__main__":
    main()
"""
alpha | keyword recall@10 | paraphrase recall@10
 0.00 |             100% |                  0%
 0.25 |             100% |                100%
 0.50 |             100% |                100%
 0.75 |             100% |                100%
 1.00 |               0% |                100%
Best keyword alpha: 0.00
Best paraphrase alpha: 1.00
Routing hint: start exact identifiers with lower alpha, paraphrases with higher alpha.
"""