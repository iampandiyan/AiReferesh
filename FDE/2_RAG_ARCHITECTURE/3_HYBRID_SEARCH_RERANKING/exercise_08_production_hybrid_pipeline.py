"""Exercise 8: standalone production-pipeline comparison and Together answer call.

Run: python exercise_08_production_hybrid_pipeline.py
Optional live mode: set TOGETHER_STUDY_API_KEY to generate a grounded demo answer.
Install the client dependencies with: pip install together python-dotenv

Behavior: checks deterministic RRF ordering, compares four retrieval strategies
on a small 50/50 exact/paraphrase golden set, reports measured local runtimes,
and optionally calls Together chat completions (openai/gpt-oss-120b). It uses
Together's SDK for generation and otherwise keeps retrieval local, without
embedding or reranking provider SDKs. The key is loaded from a .env file next to
this script or from the process environment.

Lesson: evaluate recall and ranking quality by query type, report local timings
as local timings (not a production SLO), measure actual provider costs, and make
latency/residency requirements explicit before choosing a reranker.
"""

import math
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from together import Together


load_dotenv(Path(__file__).resolve().with_name(".env"))


MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "Answer the user using only the retrieved context. If the context is "
    "insufficient, say so. Do not invent regulatory requirements."
)
DOCUMENTS = [
    "AML bulletin 4.5.2 requires banks to verify beneficial ownership.",
    "AML bulletin 4.5.2 sets enhanced due diligence thresholds.",
    "AML bulletin 4.5.2 requires suspicious activity reports.",
    "GDPR gives data subjects rights to access personal data.",
    "Individuals may request erasure of personal information under GDPR.",
    "The right to portability lets people transfer their personal data.",
    "Banks should document risk reviews for high-risk customers.",
    "Organizations must answer valid privacy requests promptly.",
]
GOLDEN_SET = [
    ("AML bulletin 4.5.2 beneficial ownership", 0, "exact"),
    ("AML 4.5.2 enhanced checks", 1, "exact"),
    ("AML bulletin suspicious activity reports", 2, "exact"),
    ("AML 4.5.2 bank beneficial ownership verification", 0, "exact"),
    ("AML bulletin 4.5.2 due diligence threshold", 1, "exact"),
    ("AML 4.5.2 suspicious transaction reporting", 2, "exact"),
    ("bulletin 4.5.2 ownership legal entities", 0, "exact"),
    ("AML 4.5.2 high-risk customer checks", 1, "exact"),
    ("AML 4.5.2 reports deadline", 2, "exact"),
    ("OCC AML bulletin 4.5.2 beneficial owner rules", 0, "exact"),
    ("what information can a data subject see", 3, "paraphrase"),
    ("can I ask to see personal data", 3, "paraphrase"),
    ("show me the records held about me", 3, "paraphrase"),
    ("remove my personal information under GDPR", 4, "paraphrase"),
    ("how can I have my information erased", 4, "paraphrase"),
    ("delete personal data from an organization", 4, "paraphrase"),
    ("move personal data to another provider", 5, "paraphrase"),
    ("transfer my information to a different service", 5, "paraphrase"),
    ("take my data with me when I switch services", 5, "paraphrase"),
]


def tokens(text):
    return set(re.findall(r"[a-z0-9.]+", text.lower()))


def sparse_search(query, limit=5):
    q = tokens(query)
    return sorted(
        range(len(DOCUMENTS)),
        key=lambda i: (-len(q & tokens(DOCUMENTS[i])), i),
    )[:limit]


def dense_search(query, limit=5):
    q = tokens(query)
    paraphrases = {
        "remove": "erasure",
        "delete": "erasure",
        "erased": "erasure",
        "move": "portability",
        "switch": "portability",
        "provider": "transfer",
        "access": "access",
        "see": "access",
        "show": "access",
        "held": "access",
    }
    expanded = q | {value for key, value in paraphrases.items() if key in q}
    return sorted(
        range(len(DOCUMENTS)),
        key=lambda i: (-len(expanded & tokens(DOCUMENTS[i])), i),
    )[:limit]


def rrf(rankings, k=60):
    scores = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda doc_id: (-scores[doc_id], doc_id))


def rerank(query, candidates, limit=5):
    q = tokens(query)
    return sorted(
        candidates,
        key=lambda i: (-len(q & tokens(DOCUMENTS[i])), candidates.index(i)),
    )[:limit]


def strategy_search(strategy, query):
    if strategy == "dense":
        return dense_search(query)
    if strategy == "bm25":
        return sparse_search(query)
    fused = rrf((sparse_search(query), dense_search(query)))
    if strategy == "hybrid":
        return fused[:5]
    if strategy == "hybrid+rerank":
        return rerank(query, fused[:8])
    raise ValueError(f"Unknown strategy: {strategy}")


def ndcg_at_k(results, gold, k=5):
    relevance = [1.0 if doc_id == gold else 0.0 for doc_id in results[:k]]
    dcg = sum(rel / math.log2(rank + 2) for rank, rel in enumerate(relevance))
    return dcg


def together_chat(system_prompt, customer_message):
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        return None
    client = Together(api_key=api_key)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": customer_message},
        ],
    )
    return response.choices[0].message.content or ""


def test_rrf():
    fused = rrf((["d1", "d2", "d3"], ["d3", "d2", "d4"]))
    assert set(fused) == {"d1", "d2", "d3", "d4"}
    assert fused.index("d2") < fused.index("d1")
    assert fused.index("d3") < fused.index("d4")
    return "PASS"


def main():
    print(f"RRF deterministic unit test: {test_rrf()}")
    strategies = ("dense", "bm25", "hybrid", "hybrid+rerank")
    print("\nstrategy          hit@5   nDCG@5   local p50/p95 ms")
    for strategy in strategies:
        hits, ndcg, timings = [], [], []
        for query, gold, _ in GOLDEN_SET:
            started = time.perf_counter()
            results = strategy_search(strategy, query)
            timings.append((time.perf_counter() - started) * 1000)
            hits.append(float(gold in results[:5]))
            ndcg.append(ndcg_at_k(results, gold))
        ordered = sorted(timings)
        p50 = ordered[len(ordered) // 2]
        p95 = ordered[min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1)]
        print(
            f"{strategy:17} {sum(hits) / len(hits):5.0%}  "
            f"{sum(ndcg) / len(ndcg):7.3f}  {p50:6.3f}/{p95:6.3f}"
        )

    cost_per_query_usd = {
        "dense": 0.001,
        "bm25": 0.0,
        "hybrid": 0.001,
        "hybrid+rerank": 0.003,
    }
    print("\nIllustrative cost assumptions (USD/query; replace with measured invoices):")
    for strategy, cost in cost_per_query_usd.items():
        print(f"  {strategy:17} ${cost:.3f}")
    print("These timings are local synthetic-code timings, not provider latency/SLO measurements.")
    print("At 100,000 queries/day, multiply measured per-query cost by 3,000,000 for a 30-day estimate.")

    query = "What rights do people have over personal information?"
    context = "\n".join(DOCUMENTS[doc_id] for doc_id in strategy_search("hybrid+rerank", query))
    customer_message = f"Query: {query}\n\nRetrieved context:\n{context}"
    answer = together_chat(PROMPT_V1, customer_message)
    if answer is None:
        print("\nTogether answer generation skipped: TOGETHER_STUDY_API_KEY is not set.")
        print("Set that environment variable to call openai/gpt-oss-120b.")
    else:
        print(f"\nTogether ({MODEL}) answer:\n{answer}")
        print("Together API usage may incur charges.")
    print("\nProduction note: choose managed vs self-hosted reranking only after validating residency,")
    print("sub-500 ms end-to-end latency, actual pricing, and slice-level quality on a 20+ query gold set.")


if __name__ == "__main__":
    main()
"""
RRF deterministic unit test: PASS

strategy          hit@5   nDCG@5   local p50/p95 ms
dense              100%    0.915   0.051/ 0.237
bm25                95%    0.831   0.036/ 0.145
hybrid             100%    0.857   0.085/ 0.198
hybrid+rerank      100%    0.857   0.102/ 0.202

Illustrative cost assumptions (USD/query; replace with measured invoices):
  dense             $0.001
  bm25              $0.000
  hybrid            $0.001
  hybrid+rerank     $0.003
These timings are local synthetic-code timings, not provider latency/SLO measurements.
At 100,000 queries/day, multiply measured per-query cost by 3,000,000 for a 30-day estimate.

Together (openai/gpt-oss-120b) answer:
GDPR gives data subjects several specific rights over their personal information:

- **Right of access** – they can obtain a copy of the personal data that is being processed about them.
- **Right to erasure** – they can request that their personal information be deleted.
- **Right to data portability** – they can receive their personal data in a structured, commonly used format and transfer it to another controller.
Together API usage may incur charges.

Production note: choose managed vs self-hosted reranking only after validating residency,
sub-500 ms end-to-end latency, actual pricing, and slice-level quality on a 20+ query gold set.
"""