"""Exercise 6: sweep chunk size and overlap, then identify a recall/cost knee.

Run with Python 3; no API key or dependency is needed. The local feature-hash vectorizer
is not a pretrained embedding model, and chunk sizes here are character counts.

Lesson: smaller chunks increase index size; overlap can preserve boundary context but adds
vectors and storage. Select a knee against measured retrieval quality and operational cost,
not by assuming one chunk size is universally best.
"""

import hashlib
import math
import re


ARTICLE = """7(1) Processing based on consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance shall not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested, including accessible formats;
(c) shall not require unnecessary personal data.
7(8) The controller shall maintain a record of consent and withdrawal.
"""
SWEEP_TEXT = (ARTICLE + "\n") * 4
GOLDEN = [
    ("In what languages must a withdrawal mechanism be available?", "(b) shall be available"),
    ("Must withdrawal be as easy as giving consent?", "(a) shall be as easy"),
    ("What record must the controller keep?", "maintain a record of consent"),
    ("Can consent be withdrawn at any time?", "right to withdraw consent at any time"),
    ("Is coerced consent valid?", "obtained through fraud or coercion is void"),
    ("What data can the withdrawal mechanism require?", "(c) shall not require"),
]


def vectorize(text: str, dimensions: int = 256) -> list[float]:
    vector = [0.0] * dimensions
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        digest = hashlib.sha256(token.encode()).digest()
        vector[int.from_bytes(digest[:4], "big") % dimensions] += 1.0 if digest[4] & 1 else -1.0
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def chunk(text: str, size: int, overlap: int) -> list[str]:
    step = max(1, size - overlap)
    return [text[index:index + size] for index in range(0, len(text), step) if text[index:index + size].strip()]


def recall_at_5(chunks: list[str]) -> float:
    vectors = [vectorize(part) for part in chunks]
    hits = 0
    for query, clause in GOLDEN:
        query_vector = vectorize(query)
        top = sorted(zip((cosine(query_vector, vector) for vector in vectors), chunks), reverse=True)[:5]
        hits += any(clause in part for _, part in top)
    return hits / len(GOLDEN)


def main() -> None:
    rows = []
    for size in (256, 512, 1024):
        for overlap_fraction in (0.0, 0.10, 0.15):
            overlap = int(size * overlap_fraction)
            chunks = chunk(SWEEP_TEXT, size, overlap)
            rows.append({"size": size, "overlap": overlap_fraction, "recall": recall_at_5(chunks), "count": len(chunks)})
    print(f"{'chars':>6s} {'overlap':>8s} {'recall@5':>9s} {'chunks':>8s}")
    for row in rows:
        print(f"{row['size']:6d} {row['overlap']:7.0%} {row['recall']:8.1%} {row['count']:8d}")
    best = max(row["recall"] for row in rows)
    best_by_size = {size: max(row["recall"] for row in rows if row["size"] == size) for size in (256, 512, 1024)}
    knee = next(size for size in (256, 512, 1024) if best_by_size[size] >= best - 0.02)
    print(f"\nBest recall@5={best:.1%}; smallest size within 2 percentage points: {knee} characters.")
    print("Cost note: overlap increases indexed vectors; hosted embedding cost depends on the chosen model/rates.")
    print("This sweep uses local feature hashing, so its recall scores are only a reproducible teaching proxy.")


if __name__ == "__main__":
    main()

"""
chars  overlap  recall@5   chunks
   256      0%   100.0%       11
   256     10%   100.0%       12
   256     15%    83.3%       13
   512      0%   100.0%        6
   512     10%   100.0%        6
   512     15%   100.0%        7
  1024      0%   100.0%        3
  1024     10%   100.0%        3
  1024     15%   100.0%        4

Best recall@5=100.0%; smallest size within 2 percentage points: 256 characters.
Cost note: overlap increases indexed vectors; hosted embedding cost depends on the chosen model/rates.
This sweep uses local feature hashing, so its recall scores are only a reproducible teaching proxy.
"""