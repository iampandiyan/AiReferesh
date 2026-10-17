"""Exercise 4 - combine vector-style and keyword retrieval with RRF.

Run: python exercise_04_pgvector_hybrid_rrf.py

This standalone, standard-library exercise uses hashed toy vectors and token
overlap instead of PostgreSQL tsvector/pgvector. The comments outline the
production analogue: vector top-k plus ts_rank_cd top-k in SQL CTEs, then RRF.

Lesson: dense and lexical retrieval have different strengths. Fuse by rank,
not raw scores, because cosine and text-rank scores use different scales.
"""

import hashlib
import math
import re


DIM = 64
CORPUS = [
    "GDPR Article 44 cross-border transfer requires adequate safeguards.",
    "Personal data may leave the EEA only with appropriate transfer protections.",
    "OCC Bulletin 2013-29 covers third-party relationships and vendor due diligence.",
    "OCC model risk management requires independent validation and effective challenge.",
    "GDPR Article 15 gives data subjects the right to access personal data.",
    "Insurance cyber-security guidance requires ISO 27001 certification.",
] + [
    f"AcmeCorp branch operations note {i}: unrelated routine office procedure."
    for i in range(44)
]
QUERY = "GDPR Article 44 cross-border transfer"


def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def embed(text):
    vector = [0.0] * DIM
    for word in tokens(text):
        digest = hashlib.sha256(word.encode()).digest()
        vector[int.from_bytes(digest[:4], "big") % DIM] += 1 if digest[4] & 1 else -1
    norm = math.sqrt(sum(v * v for v in vector)) or 1
    return [v / norm for v in vector]


def vector_ranking(query):
    query_vector = embed(query)
    return sorted(
        range(len(CORPUS)),
        key=lambda i: (
            -sum(a * b for a, b in zip(query_vector, embed(CORPUS[i]))),
            i,
        ),
    )


def keyword_ranking(query):
    query_terms = tokens(query)
    return sorted(
        range(len(CORPUS)),
        key=lambda i: (
            -sum(tokens(CORPUS[i]).count(term) for term in query_terms),
            i,
        ),
    )


def rrf(rankings, k=60):
    scores = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1 / (k + rank)
    return sorted(scores, key=lambda doc_id: (-scores[doc_id], doc_id))


def main():
    dense = vector_ranking(QUERY)[:20]
    lexical = keyword_ranking(QUERY)[:20]
    fused = rrf((dense, lexical))[:10]
    print(f'Hybrid top 10 for "{QUERY}":')
    for rank, doc_id in enumerate(fused, 1):
        print(f"  {rank:2}. {CORPUS[doc_id]}")
    print("\nProduction SQL shape: WITH vec AS (... LIMIT 20), bm AS (... LIMIT 20),")
    print("fused AS (SUM(1.0 / (60 + rank)) GROUP BY doc_id) SELECT ... LIMIT 10.")
    print("Use a GIN index for tsvector and an ANN index for embeddings.")


if __name__ == "__main__":
    main()
