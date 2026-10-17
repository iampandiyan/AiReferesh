"""Exercise 7 - pgvector-to-Qdrant migration runbook and dual-write check.

Run: python exercise_07_pgvector_to_qdrant_runbook.py
Optional draft generation: set TOGETHER_STUDY_API_KEY and install `together`.

This script prints a five-phase operational runbook and runs a local dual-write
consistency example. The local dictionaries are not real databases. If a
Together key is set, the script can ask openai/gpt-oss-120b for a supplementary
draft; the checked-in runbook remains the deterministic source of truth.

Lesson: dual-write, count/recall verification, shadow reads, controlled canary,
and explicit rollback gates make migrations reversible. Keep the old store until
the rollback window has expired and reconciliation passes.
"""

import os


PROMPT_V1 = (
    "You are an infrastructure migration reviewer. Suggest concise checks for "
    "a vector-store migration. Do not replace or weaken rollback, GDPR, or "
    "read-consistency safeguards."
)

PHASES = [
    (
        "1. Dual-write build",
        "Write every new ID to pgvector and Qdrant; compare counts hourly and reconcile failures.",
        "Rollback: disable Qdrant writes with the feature flag within 60 seconds; continue pgvector writes.",
    ),
    (
        "2. Backfill",
        "Bulk-copy the 10M existing vectors in resumable batches; verify checksums/counts and recall@10 on 200 golden queries within 1pp.",
        "Rollback: stop the backfill job, keep pgvector authoritative, and delete only the incomplete Qdrant collection.",
    ),
    (
        "3. Shadow reads",
        "Mirror reads to Qdrant for 48 hours; compare top-10 IDs, latency, errors, and tenant filters.",
        "Rollback: stop shadow traffic; since results are not user-facing, restore no read flag.",
    ),
    (
        "4. Canary cutover",
        "Route 5%, then 25%, then 100% of reads over five days using a feature flag and golden-set gates.",
        "Rollback: flip vector_store=pgvector within 60 seconds; retain dual-write and inspect diffs.",
    ),
    (
        "5. Cleanup",
        "After the 14-day rollback window, stop dual-write, take a final snapshot, then release old index disk.",
        "Rollback: restore from the retained snapshot and re-enable pgvector reads/writes; do not drop before sign-off.",
    ),
]


def dual_write(doc_id, text, pg_store, qdrant_store):
    pg_store[doc_id] = text
    qdrant_store[doc_id] = text
    return pg_store.get(doc_id) == qdrant_store.get(doc_id)


def optional_together_review():
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        return None
    try:
        from together import Together
    except ImportError as error:
        raise RuntimeError(
            "Install the optional Together SDK with `pip install together`."
        ) from error
    client = Together(api_key=api_key)
    customer_message = (
        "Review these migration phases for missing rollback safeguards:\n"
        + "\n".join(f"{name}: {goal} {rollback}" for name, goal, rollback in PHASES)
    )
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": PROMPT_V1},
            {"role": "user", "content": customer_message},
        ],
    )
    return response.choices[0].message.content or ""


def main():
    print("PGVECTOR -> QDRANT MIGRATION RUNBOOK")
    for name, goal, rollback in PHASES:
        print(f"\n{name}\n  Goal: {goal}\n  {rollback}")

    pg_store, qdrant_store = {}, {}
    text = "GDPR Article 35 high-risk AI impact assessment"
    consistent = dual_write(9999, text, pg_store, qdrant_store)
    print(f"\nDual-write read-consistency check (ID 9999 in both stores): {consistent}")
    assert consistent

    review = optional_together_review()
    if review is not None:
        print("\nOptional Together review (openai/gpt-oss-120b):")
        print(review)
    else:
        print("\nOptional Together review skipped; set TOGETHER_STUDY_API_KEY to request one.")


if __name__ == "__main__":
    main()
