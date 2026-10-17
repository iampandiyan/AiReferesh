"""Exercise 3: implement Reciprocal Rank Fusion (RRF) and compare retrieval lanes.

Run: python exercise_03_reciprocal_rank_fusion.py

Behavior: fuses sparse and dense ranked lists over a tiny labeled corpus. Ties
(a document found by both lanes) accumulate both rank contributions.

Lesson: rank fusion combines complementary candidate lists without comparing
incommensurate raw BM25 and cosine scores. RRF improves coverage only when the
retrieval lanes actually contribute complementary relevant documents.
"""


CORPUS = {
    "aml_exact": "AML bulletin 4.5.2 beneficial ownership requirements.",
    "aml_sar": "AML bulletin 4.5.2 suspicious activity reporting deadlines.",
    "gdpr_access": "GDPR data subjects can request access to personal data.",
    "gdpr_erase": "Individuals may request erasure of personal information.",
    "gdpr_portability": "GDPR grants data portability rights.",
    "irrelevant": "Office opening hours and visitor parking instructions.",
}
GOLDEN_SET = [
    ("AML bulletin 4.5.2", "aml_exact"),
    ("AML suspicious activity report", "aml_sar"),
    ("data subject rights under GDPR", "gdpr_access"),
    ("remove personal information", "gdpr_erase"),
    ("transfer my information to another service", "gdpr_portability"),
]


def rrf(rankings, k=60):
    """Return document IDs sorted by summed reciprocal rank scores."""
    scores = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda doc_id: (-scores[doc_id], str(doc_id)))


def sparse(query):
    lowered = query.lower()
    if "4.5.2" in lowered:
        return ["aml_exact", "aml_sar", "irrelevant"]
    if "suspicious activity report" in lowered:
        return ["aml_exact", "irrelevant", "gdpr_access", "aml_sar"]
    if "aml" in lowered or "suspicious" in lowered:
        return ["aml_sar", "aml_exact", "irrelevant"]
    if "gdpr" in lowered or "rights" in lowered:
        return ["gdpr_access", "gdpr_portability", "irrelevant"]
    return ["irrelevant", "gdpr_erase", "gdpr_portability"]


def dense(query):
    lowered = query.lower()
    if "4.5.2" in lowered:
        return ["aml_sar", "irrelevant", "aml_exact"]
    if "suspicious activity report" in lowered:
        return ["gdpr_erase", "irrelevant", "gdpr_access", "aml_sar"]
    if "aml" in lowered or "suspicious" in lowered:
        return ["aml_exact", "irrelevant", "aml_sar"]
    if "gdpr" in lowered or "rights" in lowered:
        return ["gdpr_portability", "gdpr_access", "gdpr_erase"]
    return ["gdpr_erase", "gdpr_portability", "irrelevant"]


def hit_at_k(results, gold, k=3):
    return int(gold in results[:k])


def main():
    totals = {"sparse": 0, "dense": 0, "hybrid": 0}
    for query, gold in GOLDEN_SET:
        sparse_results, dense_results = sparse(query), dense(query)
        fused = rrf((sparse_results, dense_results))
        rows = {
            "sparse": sparse_results,
            "dense": dense_results,
            "hybrid": fused,
        }
        for name, results in rows.items():
            totals[name] += hit_at_k(results, gold)
        print(f"\n{query!r} (gold={gold})")
        for name, results in rows.items():
            print(f"  {name:6}: top-3={results[:3]} hit@3={hit_at_k(results, gold)}")

    print("\nRecall/hit rate @3:")
    for name, hits in totals.items():
        print(f"  {name:6}: {hits}/{len(GOLDEN_SET)}")
    assert rrf((["d1", "d2"], ["d2", "d3"]))[0] == "d2"
    print("\nRRF overlap/tie check: PASS")


if __name__ == "__main__":
    main()
"""
'AML bulletin 4.5.2' (gold=aml_exact)
  sparse: top-3=['aml_exact', 'aml_sar', 'irrelevant'] hit@3=1
  dense : top-3=['aml_sar', 'irrelevant', 'aml_exact'] hit@3=1
  hybrid: top-3=['aml_sar', 'aml_exact', 'irrelevant'] hit@3=1

'AML suspicious activity report' (gold=aml_sar)
  sparse: top-3=['aml_exact', 'irrelevant', 'gdpr_access'] hit@3=0
  dense : top-3=['gdpr_erase', 'irrelevant', 'gdpr_access'] hit@3=0
  hybrid: top-3=['irrelevant', 'gdpr_access', 'aml_sar'] hit@3=1

'data subject rights under GDPR' (gold=gdpr_access)
  sparse: top-3=['gdpr_access', 'gdpr_portability', 'irrelevant'] hit@3=1
  dense : top-3=['gdpr_portability', 'gdpr_access', 'gdpr_erase'] hit@3=1
  hybrid: top-3=['gdpr_access', 'gdpr_portability', 'gdpr_erase'] hit@3=1

'remove personal information' (gold=gdpr_erase)
  sparse: top-3=['irrelevant', 'gdpr_erase', 'gdpr_portability'] hit@3=1
  dense : top-3=['gdpr_erase', 'gdpr_portability', 'irrelevant'] hit@3=1
  hybrid: top-3=['gdpr_erase', 'irrelevant', 'gdpr_portability'] hit@3=1

'transfer my information to another service' (gold=gdpr_portability)
  sparse: top-3=['irrelevant', 'gdpr_erase', 'gdpr_portability'] hit@3=1
  dense : top-3=['gdpr_erase', 'gdpr_portability', 'irrelevant'] hit@3=1
  hybrid: top-3=['gdpr_erase', 'irrelevant', 'gdpr_portability'] hit@3=1

Recall/hit rate @3:
  sparse: 4/5
  dense : 4/5
  hybrid: 5/5

RRF overlap/tie check: PASS
"""