"""Exercise 8 - choose a vector store for a GDPR-sensitive AcmeCorp RAG.

Run: python exercise_08_pick_vector_store.py
Optional recommendation draft: set TOGETHER_STUDY_API_KEY and install `together`.

Prints a concise five-store decision matrix and runs a transparent rule-of-thumb
selector. Costs and latency depend on region, workload, and contract, so this
exercise marks them as estimates to measure, not vendor guarantees. Optional
Together output is an editable draft, not legal or procurement advice.

Lesson: choose around data residency, current infrastructure, scale, SLO, ops
capacity, and procurement. A few milliseconds of benchmark advantage rarely
outweigh unreviewed cross-border processing for regulated data.
"""

import os


PROMPT_V1 = (
    "You are a cloud architecture assistant. Draft a brief vector-store recommendation "
    "from the supplied constraints. Clearly distinguish assumptions from measured "
    "facts, do not invent benchmark numbers, and call out GDPR review requirements."
)

STORES = [
    ("pgvector", "Existing Postgres; EU placement", "Manual HNSW tuning", "Low incremental"),
    ("Qdrant self-hosted", "EU CoreWeave; payload filters", "On-call and upgrades", "Medium ops"),
    ("Pinecone", "Managed; fast POC", "Vendor/region review; egress", "Low ops"),
    ("Weaviate", "OSS; hybrid features", "More operating surface", "Medium ops"),
    ("Milvus", "OSS; GPU ANN options", "More operating surface", "High ops"),
]


def pick_store(constraints):
    residency = constraints.get("residency", "unknown").lower()
    scale = constraints.get("scale_vectors", 0)
    if residency == "eu" and constraints.get("postgres_in_prod"):
        return {
            "store": "pgvector",
            "why": "Reuse the existing in-region Postgres and avoid adding a vendor during the first scale phase.",
        }
    if residency == "eu" and scale > 50_000_000:
        return {
            "store": "Qdrant self-hosted on CoreWeave EU",
            "why": "Purpose-built ANN at this scale while keeping control of the deployment region.",
        }
    if constraints.get("time_to_demo_days", 999) <= 14 and not constraints.get("pii"):
        return {
            "store": "Pinecone",
            "why": "Managed service can accelerate a non-PII prototype; verify region and contract before production.",
        }
    return {
        "store": "Qdrant Cloud",
        "why": "Managed option to evaluate, contingent on region, DPA, and Chapter V review.",
    }


def optional_together_memo(constraints, choice):
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
        f"Customer constraints: {constraints}\nRule-of-thumb choice: {choice}\n"
        "Draft one paragraph for the CTO and CISO. Address EU residency, existing "
        "Postgres, 5M-vector target, 500ms end-to-end SLO, operational burden, and "
        "why a measured 6ms Pinecone lead alone does not settle the decision."
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
    constraints = {
        "residency": "eu",
        "postgres_in_prod": True,
        "scale_vectors": 5_000_000,
        "pii": True,
        "time_to_demo_days": 60,
        "end_to_end_slo_ms": 500,
    }
    print("AcmeCorp vector-store decision matrix (qualitative; benchmark locally)")
    print(f"{'Store':22} | {'Strength':34} | {'Trade-off':28} | {'Ops/cost signal'}")
    print("-" * 112)
    for store, strength, tradeoff, ops in STORES:
        print(f"{store:22} | {strength:34} | {tradeoff:28} | {ops}")

    choice = pick_store(constraints)
    print(f"\nConstraints: {constraints}")
    print(f"Rule-of-thumb recommendation: {choice['store']}")
    print(f"Reason: {choice['why']}")
    print("\nBefore production, benchmark p50/p95 at 5M vectors, estimate monthly spend from actual quotes,")
    print("and review residency, DPA/Chapter V transfer, audit logging, and IAM with privacy/security.")
    print("A claimed 6ms speed lead is not decisive without a reproducible same-workload benchmark.")

    memo = optional_together_memo(constraints, choice)
    if memo is not None:
        print("\nOptional recommendation draft (Together openai/gpt-oss-120b):")
        print(memo)
    else:
        print("\nOptional Together memo skipped; set TOGETHER_STUDY_API_KEY to generate a draft.")


if __name__ == "__main__":
    main()
