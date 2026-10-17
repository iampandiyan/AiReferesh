"""Exercise 1: demonstrate why dense retrieval can miss an exact section number.

Run: python exercise_01_dense_exact_miss.py

Behavior: a small deterministic dense-search simulation ranks semantically related
AML paraphrases ahead of exact section references. No API or third-party package
is needed; this intentionally illustrates the failure mode rather than claiming
to reproduce a particular embedding model's scores.

Lesson: dense similarity is useful for meaning, but rare identifiers and exact
strings can be weak semantic signals. Keep a lexical retrieval lane for them.
"""

import math
import re


EXACT_DOCS = [
    "AML bulletin 4.5.2 requires banks to verify beneficial ownership.",
    "AML bulletin 4.5.2 sets enhanced due diligence thresholds.",
    "AML bulletin 4.5.2 requires suspicious activity reports.",
    "AML bulletin 4.5.2 applies to national banks.",
    "AML bulletin 4.5.2 supersedes earlier customer guidance.",
]
PARAPHRASE_DOCS = [
    "The 4.5 series governs anti-money laundering checks for customer accounts.",
    "Banks follow the AML section 4.5.x rules for beneficial owners.",
    "The 4.5 series anti-money laundering guidance describes enhanced checks for high-risk clients.",
    "The 4.5.x regulatory bulletin series covers suspicious transaction reporting.",
    "Customer due diligence rules are described in the AML 4.5 framework series.",
]
DISTRACTORS = [
    f"Internal operations note {i}: routine account servicing and customer support."
    for i in range(15)
]
CORPUS = EXACT_DOCS + PARAPHRASE_DOCS + DISTRACTORS
QUERY = "AML bulletin 4.5.2"


def tokens(text):
    return re.findall(r"[a-z]+(?:-[a-z]+)?", text.lower())


def dense_demo_score(query, document):
    """Approximate semantic matching while intentionally down-weighting identifiers."""
    query_terms = set(tokens(query)) - {"4"}
    doc_terms = set(tokens(document))
    synonym_groups = (
        {"aml", "anti-money", "laundering"},
        {"bulletin", "guidance", "rules", "framework"},
        {"customer", "account", "client"},
    )
    score = len(query_terms & doc_terms) * 0.1
    for group in synonym_groups:
        if query_terms & group and doc_terms & group:
            score += 1.0
    if "4.5.2" not in document and ("4.5" in document or "series" in document):
        score += 1.0
    return score


def dense_top_k(query, documents, k):
    ranked = sorted(
        enumerate(documents),
        key=lambda item: (dense_demo_score(query, item[1]), -item[0]),
        reverse=True,
    )
    return [doc_id for doc_id, _ in ranked[:k]]


def main():
    top = dense_top_k(QUERY, CORPUS, 5)
    print(f'Dense-demo top 5 for "{QUERY}":')
    for rank, doc_id in enumerate(top, 1):
        text = CORPUS[doc_id]
        label = "EXACT" if "4.5.2" in text else "paraphrase/distractor"
        print(f"  {rank}. [{label}] {text}")

    exact_hits = sum("4.5.2" in CORPUS[doc_id] for doc_id in top)
    paraphrase_hits = sum(
        doc_id in range(len(EXACT_DOCS), len(EXACT_DOCS) + len(PARAPHRASE_DOCS))
        for doc_id in top
    )
    print(f"\nExact references in top 5: {exact_hits}")
    print(f"Paraphrases in top 5: {paraphrase_hits}")
    print("This is a controlled illustration, not a benchmark of a live embedding model.")


if __name__ == "__main__":
    main()

"""

"""