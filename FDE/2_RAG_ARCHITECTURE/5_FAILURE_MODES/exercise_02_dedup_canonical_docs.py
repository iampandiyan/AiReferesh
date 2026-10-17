"""Exercise 2: Deduplicate retrieved versions by canonical document identity.

Run: python exercise_02_dedup_canonical_docs.py

Behavior: Keeps the newest effective date for each canonical document id and
preserves the first-seen order of canonical ids. Uses only the Python standard
library and includes assertions for the old and new GDPR versions.

Lesson: Chunk ids identify individual chunks; they do not identify duplicate
or revised source documents. Deduplicate by a stable canonical id and an
explicit version date, and make tie behavior/order intentional.
"""

from dataclasses import dataclass
from datetime import date


@dataclass
class Doc:
    chunk_id: str
    canonical_doc_id: str
    effective_date: date
    text: str


def dedup_by_canonical(docs: list[Doc]) -> list[Doc]:
    """Keep each canonical document's newest version, in first-seen id order."""
    newest = {}
    for doc in docs:
        current = newest.get(doc.canonical_doc_id)
        if current is None or doc.effective_date > current.effective_date:
            newest[doc.canonical_doc_id] = doc

    ordered_ids = dict.fromkeys(doc.canonical_doc_id for doc in docs)
    return [newest[canonical_id] for canonical_id in ordered_ids]


def main():
    retrieved = [
        Doc("c1", "gdpr-art-7-consent", date(2023, 8, 11),
            "GDPR Art. 7 - consent definitions (original language)."),
        Doc("c2", "occ-master-kyc", date(2024, 1, 4),
            "OCC bulletin on KYC v2 - PEP screening update."),
        Doc("c3", "gdpr-art-7-consent", date(2025, 11, 13),
            "GDPR Art. 7 - clarified consent and withdrawal flow."),
        Doc("c4", "nist-ai-rmf-confirm", date(2025, 8, 20),
            "NIST AI RMF - out-of-band confirmation for AI-initiated transactions."),
        Doc("c5", "gdpr-art-17-erasure", date(2023, 8, 11),
            "GDPR Art. 17 - data subject right to erasure."),
    ]

    deduped = dedup_by_canonical(retrieved)
    assert len(deduped) == 4, f"expected 4 documents, got {len(deduped)}"
    assert all(doc.chunk_id != "c1" for doc in deduped), "older GDPR consent chunk remains"
    assert next(doc for doc in deduped if doc.canonical_doc_id == "gdpr-art-7-consent").chunk_id == "c3"

    for doc in deduped:
        print(f"{doc.canonical_doc_id:<22} {doc.effective_date} {doc.chunk_id}")
    print("\nDedup verified: the older GDPR Art. 7 consent version was pruned.")


if __name__ == "__main__":
    main()
