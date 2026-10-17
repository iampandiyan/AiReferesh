"""Exercise 3: Filter off-topic retrievals with a cosine-similarity floor.

Run: python exercise_03_cosine_threshold_filter.py

Behavior: Applies 0.55 and 0.70 thresholds to a fixed set of measured cosine
scores. This is a standalone, deterministic standard-library demonstration;
it does not call an embedding API or require a vector database.

Lesson: A higher threshold can remove weak/off-topic matches, but may also
discard relevant evidence. Tune the threshold against labeled queries and
report both relevance and recall rather than assuming one universal cutoff.
"""

QUERY = "What is the data subject's right to erasure under GDPR?"
CANDIDATE_COS = [
    ("gdpr-17-erasure", 0.812),
    ("gdpr-16-correction", 0.703),
    ("gdpr-17-timeline", 0.778),
    ("occ-capital-basel-3", 0.241),
    ("occ-liquidity-lcr", 0.198),
    ("gdpr-7-consent", 0.622),
    ("occ-kyc-pep", 0.273),
    ("gdpr-5-minimization", 0.598),
]
OFF_TOPIC_OCC = {"occ-capital-basel-3", "occ-liquidity-lcr", "occ-kyc-pep"}


def filter_by_floor(threshold):
    print(f"\n--- cosine threshold = {threshold:.2f} ---")
    kept, dropped = [], []
    for candidate_id, score in CANDIDATE_COS:
        verdict = "KEEP" if score >= threshold else "DROP"
        print(f"  {verdict}  {score:.3f}  {candidate_id}")
        (kept if score >= threshold else dropped).append(candidate_id)
    print(f"  kept {len(kept)}, dropped {len(dropped)}")
    return kept, dropped


def main():
    print(f"Query: {QUERY}")
    kept_055, _ = filter_by_floor(0.55)
    filter_by_floor(0.70)
    below_055 = {candidate_id for candidate_id, score in CANDIDATE_COS if score < 0.55}
    assert OFF_TOPIC_OCC <= below_055, "all OCC examples should fall below 0.55"
    assert "gdpr-17-erasure" in kept_055
    print("\nVerified: every example OCC chunk is below the 0.55 floor.")


if __name__ == "__main__":
    main()
