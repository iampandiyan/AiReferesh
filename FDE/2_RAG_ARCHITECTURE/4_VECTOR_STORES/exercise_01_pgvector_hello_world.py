"""Exercise 1 - pgvector hello-world: insert and cosine-search synthetic chunks.

Run: python exercise_01_pgvector_hello_world.py

This dependency-free demo mimics the pgvector retrieval contract in memory. It
does not start PostgreSQL or claim to measure database latency. Replace the
in-memory scan with `ORDER BY embedding <=> query_vector LIMIT 5` in production.

Lesson: a vector store persists document IDs, text, and embeddings, then ranks
documents by similarity to an embedded query.
"""

import hashlib
import math
import random


DIMENSIONS = 64


def embed(text):
    vector = [0.0] * DIMENSIONS
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % DIMENSIONS
        vector[index] += 1.0 if digest[4] % 2 == 0 else -1.0
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def cosine(left, right):
    return sum(a * b for a, b in zip(left, right))


def main():
    random.seed(42)
    documents = [
        "GDPR Article 44 cross-border transfer requires adequate safeguards.",
        "GDPR data transfers outside the EEA need appropriate protection.",
        "OCC Bulletin 2013-29 covers third-party vendor due diligence.",
        "OCC model risk management requires independent validation.",
    ]
    documents.extend(
        f"AcmeCorp internal operations note {index} covers branch maintenance."
        for index in range(96)
    )
    rows = [
        {"id": doc_id, "text": text, "vector": embed(text)}
        for doc_id, text in enumerate(documents)
    ]
    query = "GDPR cross-border data transfer AcmeCorp"
    query_vector = embed(query)
    results = sorted(
        rows,
        key=lambda row: (-cosine(query_vector, row["vector"]), row["id"]),
    )[:5]

    print(f"Inserted {len(rows)} synthetic chunks into the in-memory vector table.")
    print(f'Top 5 cosine results for "{query}":')
    for row in results:
        print(
            f"  id={row['id']:3} cosine={cosine(query_vector, row['vector']):.3f} "
            f"{row['text']}"
        )
    print("Measured latency is for this local Python scan, not PostgreSQL/pgvector.")


if __name__ == "__main__":
    main()
