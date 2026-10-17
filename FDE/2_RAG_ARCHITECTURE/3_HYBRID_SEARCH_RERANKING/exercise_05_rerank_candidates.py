"""Exercise 5: rerank a hybrid candidate list and inspect rank changes.

Run: python exercise_05_rerank_candidates.py

Behavior: creates a 50-document candidate pool, compares its hybrid order with
a deterministic query-document relevance reranker. A reranker is simulated so
this file runs without a Cohere key or package.

Lesson: retrieve broadly, then rerank a small candidate pool. This lexical demo
is not a cross-encoder benchmark; a production reranker needs relevance testing,
latency monitoring, and an explicit choice of service/model.
"""

import re


QUERY = "AML bulletin 4.5.2 beneficial ownership"
DOCUMENTS = [
    "AML bulletin 4.5.2 requires banks to verify beneficial ownership.",
    "AML bulletin 4.5.2 sets enhanced due diligence thresholds.",
    "The AML 4.5 series concerns customer identity checks.",
    "Customer account servicing guide for retail branches.",
    "Beneficial ownership documentation must be checked for legal entities.",
]
DOCUMENTS.extend(
    f"General compliance operations note {index}: review controls and customer records."
    for index in range(5, 50)
)


def tokens(text):
    return set(re.findall(r"[a-z0-9.]+", text.lower()))


def hybrid_candidates(query, documents, limit=50):
    # Simulated hybrid order places exact hits in the candidate pool but below
    # generic semantic matches, giving the reranking stage something to correct.
    order = [2, 3, 4, 5, 6, 7, 8, 0, 1, 9] + list(range(10, len(documents)))
    return order[:limit]


def rerank(query, candidate_ids, documents, top_n=10):
    query_terms = tokens(query)
    scored = []
    for original_rank, doc_id in enumerate(candidate_ids):
        doc_terms = tokens(documents[doc_id])
        overlap = len(query_terms & doc_terms)
        exact_bonus = 4 if "4.5.2" in documents[doc_id] else 0
        score = overlap + exact_bonus
        scored.append((score, -original_rank, doc_id))
    return [doc_id for _, _, doc_id in sorted(scored, reverse=True)[:top_n]]


def main():
    candidates = hybrid_candidates(QUERY, DOCUMENTS)
    before, after = candidates[:10], rerank(QUERY, candidates, DOCUMENTS)
    before_rank = {doc_id: rank for rank, doc_id in enumerate(before, 1)}
    print("rank | before -> after | document")
    for new_rank, doc_id in enumerate(after, 1):
        prior = before_rank.get(doc_id)
        move = "NEW" if prior is None else f"{prior:>2} -> {new_rank:<2}"
        print(f"{new_rank:>4} | {move:>15} | {DOCUMENTS[doc_id]}")

    moved = [
        (doc_id, prior, rank)
        for rank, doc_id in enumerate(after, 1)
        if (prior := before_rank.get(doc_id)) is not None and abs(prior - rank) > 5
    ]
    print(f"\nDocuments moving more than 5 positions: {len(moved)}")
    if not moved:
        print("This compact corpus did not produce two >5-position movers; increase pool diversity to study larger shifts.")
    else:
        for doc_id, prior, rank in moved:
            print(f"  {prior} -> {rank}: {DOCUMENTS[doc_id]}")
    print("Reranker used here: transparent token-overlap heuristic, not Cohere Rerank 4.")


if __name__ == "__main__":
    main()
"""
rank | before -> after | document
   1 |         8 -> 1  | AML bulletin 4.5.2 requires banks to verify beneficial ownership.
   2 |         9 -> 2  | AML bulletin 4.5.2 sets enhanced due diligence thresholds.
   3 |         3 -> 3  | Beneficial ownership documentation must be checked for legal entities.
   4 |         1 -> 4  | The AML 4.5 series concerns customer identity checks.
   5 |         2 -> 5  | Customer account servicing guide for retail branches.
   6 |         4 -> 6  | General compliance operations note 5: review controls and customer records.
   7 |         5 -> 7  | General compliance operations note 6: review controls and customer records.
   8 |         6 -> 8  | General compliance operations note 7: review controls and customer records.
   9 |         7 -> 9  | General compliance operations note 8: review controls and customer records.
  10 |        10 -> 10 | General compliance operations note 9: review controls and customer records.

Documents moving more than 5 positions: 2
  8 -> 1: AML bulletin 4.5.2 requires banks to verify beneficial ownership.
  9 -> 2: AML bulletin 4.5.2 sets enhanced due diligence thresholds.
Reranker used here: transparent token-overlap heuristic, not Cohere Rerank 4.

"""