"""Exercise 7: Localize failures to retrieval, ranking, or generation.

Run: python exercise_07_bisect_pipeline_failure.py

Behavior: Routes 12 self-contained examples into exactly one of three failure
buckets and asserts top-5 is contained in top-50. Uses only the Python standard
library and does not need an API key or external files.

Lesson: Diagnose where evidence disappeared before assigning a broader failure
mode: absent from top-50 points to retrieval; present in top-50 but absent from
top-5 points to ranking; present in top-5 but unused points to generation.
"""

from collections import Counter


FAILING = [
    {"id": "f01", "gold": "gdpr-17-timeline", "top50": ["gdpr-16-correction", "gdpr-7-consent", "occ-kyc-pep", "gdpr-5-minimization"], "top5": ["gdpr-16-correction", "gdpr-7-consent"], "answer": "Correction is covered in [gdpr-16-correction]."},
    {"id": "f02", "gold": "occ-kyc-pep", "top50": ["occ-liquidity-lcr", "occ-capital-basel-3", "gdpr-accountability"], "top5": ["occ-liquidity-lcr", "occ-capital-basel-3"], "answer": "The LCR floor is in [occ-liquidity-lcr]."},
    {"id": "f03", "gold": "nist-ai-rmf-confirm", "top50": ["nist-ai-rmf-audit", "nist-ai-rmf-explain", "gdpr-consent"], "top5": ["nist-ai-rmf-audit", "nist-ai-rmf-explain"], "answer": "Audit logging is required per [nist-ai-rmf-audit]."},
    {"id": "f04", "gold": "gdpr-5-minimization", "top50": ["gdpr-7-consent", "gdpr-16-correction", "occ-kyc-pep"], "top5": ["gdpr-7-consent", "gdpr-16-correction"], "answer": "Consent basis is in [gdpr-7-consent]."},
    {"id": "f05", "gold": "gdpr-17-erasure", "top50": ["gdpr-16-correction", "gdpr-7-consent", "gdpr-17-erasure", "gdpr-5-minimization", "occ-kyc-pep"], "top5": ["gdpr-16-correction", "gdpr-7-consent"], "answer": "Correction rights appear in [gdpr-16-correction]."},
    {"id": "f06", "gold": "occ-capital-basel-3", "top50": ["occ-liquidity-lcr", "occ-kyc-pep", "occ-capital-basel-3", "gdpr-accountability"], "top5": ["occ-liquidity-lcr", "occ-kyc-pep"], "answer": "The LCR floor is in [occ-liquidity-lcr]."},
    {"id": "f07", "gold": "nist-ai-rmf-explain", "top50": ["nist-ai-rmf-audit", "nist-ai-rmf-confirm", "nist-ai-rmf-explain", "gdpr-accountability"], "top5": ["nist-ai-rmf-audit", "nist-ai-rmf-confirm"], "answer": "Audit logs are required per [nist-ai-rmf-audit]."},
    {"id": "f08", "gold": "gdpr-accountability", "top50": ["gdpr-7-consent", "gdpr-grievance", "gdpr-accountability", "occ-kyc-pep"], "top5": ["gdpr-7-consent", "gdpr-grievance"], "answer": "The grievance contact is in [gdpr-grievance]."},
    {"id": "f09", "gold": "gdpr-17-erasure", "top50": ["gdpr-17-erasure", "gdpr-7-consent", "gdpr-16-correction", "occ-kyc-pep"], "top5": ["gdpr-17-erasure", "gdpr-7-consent"], "answer": "Consent is defined in [gdpr-7-consent]."},
    {"id": "f10", "gold": "occ-liquidity-lcr", "top50": ["occ-liquidity-lcr", "occ-capital-basel-3", "occ-kyc-pep"], "top5": ["occ-liquidity-lcr", "occ-capital-basel-3"], "answer": "The capital ratio floor is in [occ-capital-basel-3]."},
    {"id": "f11", "gold": "nist-ai-rmf-audit", "top50": ["nist-ai-rmf-audit", "nist-ai-rmf-explain", "nist-ai-rmf-confirm"], "top5": ["nist-ai-rmf-audit", "nist-ai-rmf-explain"], "answer": "Explanations are required per [nist-ai-rmf-explain]."},
    {"id": "f12", "gold": "gdpr-7-consent", "top50": ["gdpr-7-consent", "gdpr-17-erasure", "gdpr-16-correction"], "top5": ["gdpr-7-consent", "gdpr-17-erasure"], "answer": "Erasure is covered in [gdpr-17-erasure]."},
]

BUCKETS = ("retriever-miss", "reranker-demotion", "generation-ignore")
OWNER_FIX = {
    "retriever-miss": "retrieval owner: inspect chunking, embeddings, and hybrid search",
    "reranker-demotion": "ranking owner: inspect reranker features and candidate top-k",
    "generation-ignore": "generation owner: inspect context selection and evidence-use prompt",
}


def bisect(row):
    gold = row["gold"]
    if gold not in row["top50"]:
        return "retriever-miss"
    if gold not in row["top5"]:
        return "reranker-demotion"
    if gold not in row["answer"]:
        return "generation-ignore"
    raise ValueError(f"{row['id']}: row does not represent one of the three failure buckets")


def main():
    counts = Counter()
    for row in FAILING:
        assert set(row["top5"]) <= set(row["top50"]), f"{row['id']}: top-5 is not within top-50"
        bucket = bisect(row)
        counts[bucket] += 1
        print(f"{row['id']}  gold={row['gold']:<22} -> {bucket}")

    print("\nThree-bucket split:")
    for bucket in BUCKETS:
        print(f"  {bucket:<18} {counts[bucket]}  | {OWNER_FIX[bucket]}")
    assert sum(counts.values()) == len(FAILING)


if __name__ == "__main__":
    main()
