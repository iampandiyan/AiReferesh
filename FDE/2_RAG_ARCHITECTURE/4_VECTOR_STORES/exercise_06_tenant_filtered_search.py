"""Exercise 6 - compare pre-filter and post-filter tenant vector search.

Run: python exercise_06_tenant_filtered_search.py

Uses synthetic deterministic hashed vectors and only the Python standard
library. Every returned hit is checked against the selected tenant. This is a
retrieval-contract demonstration, not an ANN implementation.

Lesson: post-filtering can underfill a page when a tenant is selective. Tenant
isolation is a hard correctness/security condition: validate every result and
prefer storage/query mechanisms that enforce filters during candidate search.
"""

import hashlib
import math


DIM = 48
TENANTS = 50
TARGET_TENANT = 7
K = 10


def embed(text):
    vector = [0.0] * DIM
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode()).digest()
        vector[int.from_bytes(digest[:4], "big") % DIM] += 1.0 if digest[4] & 1 else -1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1
    return [value / norm for value in vector]


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


def main():
    records = []
    for doc_id in range(500):
        tenant_id = doc_id % TENANTS
        text = (
            f"GDPR cross-border data transfer policy tenant {tenant_id} "
            f"document {doc_id}"
        )
        records.append(
            {"id": doc_id, "tenant_id": tenant_id, "text": text, "vector": embed(text)}
        )

    query = embed("GDPR cross-border transfer")
    ranked = sorted(records, key=lambda row: cosine(query, row["vector"]), reverse=True)
    post_filter = [row for row in ranked[:K] if row["tenant_id"] == TARGET_TENANT]
    allowed = [row for row in records if row["tenant_id"] == TARGET_TENANT]
    pre_filter = sorted(
        allowed, key=lambda row: cosine(query, row["vector"]), reverse=True
    )[:K]

    for mode, results in (("post-filter", post_filter), ("pre-filter", pre_filter)):
        assert all(row["tenant_id"] == TARGET_TENANT for row in results), (
            f"Cross-tenant leakage in {mode}"
        )
        print(f"{mode:11}: returned {len(results)}/{K}; tenant IDs={sorted({r['tenant_id'] for r in results})}")

    print(
        f"\nTenant {TARGET_TENANT} owns {len(allowed)}/{len(records)} records. "
        "Post-filter may underfill K; pre-filter searches only authorized candidates."
    )
    print("Zero cross-tenant leakage: PASS")


if __name__ == "__main__":
    main()
