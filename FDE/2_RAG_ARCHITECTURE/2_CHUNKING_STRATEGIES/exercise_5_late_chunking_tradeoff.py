"""Exercise 5: compare isolated-window vectors with document-aware windows.

Run with Python 3; no key or third-party dependency is required. The vectorizer is local
feature hashing, not a real embedding model. “Late” is only approximated by adding document
context to each window; no token-level mean pooling is performed.

Lesson: document context can help questions that span sections, but can blur unrelated
topics. For production late chunking, use an embedding model with long-context token vectors
and compare measured retrieval quality, latency, and current provider pricing.
"""

import hashlib
import math
import re
import time
from pprint import pprint


SECTION = """7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.
"""
BIG_DOCUMENT = (SECTION + "\n") * 6
QUESTIONS = [
    {"query": "Compare 7(7)(a) ease of use with 7(7)(c) minimum data.", "need": ["(a) shall be as easy", "(c) shall not require"]},
    {"query": "Relate withdrawal timing and ease of withdrawal.", "need": ["right to withdraw consent at any time", "as easy to withdraw as to give"]},
    {"query": "Does fraud invalidate consent that must be demonstrable?", "need": ["is void", "must be demonstrable"]},
    {"query": "How do language coverage and clear language relate?", "need": ["available in every language", "clear and accessible"]},
    {"query": "Connect record keeping with withdrawal rights.", "need": ["Maintain a record", "right to withdraw consent"]},
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


def make_windows(text: str, size: int = 1200, overlap: int = 150) -> list[str]:
    step = size - overlap
    return [text[start:start + size] for start in range(0, len(text), step) if text[start:start + size].strip()]


def score_windows(
    windows: list[str], indexed_texts: list[str], question: dict
) -> tuple[int, int, list[tuple[float, str]]]:
    query_vector = vectorize(question["query"])
    ranking = sorted(
        ((cosine(query_vector, vectorize(indexed)), raw) for indexed, raw in zip(indexed_texts, windows)),
        key=lambda row: row[0], reverse=True,
    )[:3]
    context = "\n".join(raw for _, raw in ranking)
    hit = int(any(needle in context for needle in question["need"]))
    faithful = int(all(needle in context for needle in question["need"]))
    return hit, faithful, ranking


def run_pattern(name: str, contextual: bool) -> dict:
    started = time.perf_counter()
    windows = make_windows(BIG_DOCUMENT)
    indexed = [("Synthetic Article 7 consent withdrawal policy. " + window) if contextual else window for window in windows]
    print(f"\nAll windows for {name}:")
    for index, (window, indexed_text) in enumerate(zip(windows, indexed), 1):
        print(f"\n[window {index}/{len(windows)}] indexed text:\n{indexed_text}")
        if contextual:
            print("Original window:\n" + window)
    hits = faithfulness = 0
    retrieved_by_question = []
    for question in QUESTIONS:
        hit, faithful, ranking = score_windows(windows, indexed, question)
        hits += hit
        faithfulness += faithful
        retrieved_by_question.append((question["query"], hit, faithful, ranking))
    elapsed_ms = (time.perf_counter() - started) * 1000
    print(f"\nTop-three retrieved windows: {name}")
    for query, hit, faithful, ranking in retrieved_by_question:
        print(f"\nQuestion: {query}")
        print(f"Recall hit: {bool(hit)} | Faithful: {bool(faithful)}")
        for rank, (similarity, window) in enumerate(ranking, 1):
            print(f"\n  [{rank}] cosine={similarity:.3f}\n{window}")
    return {"name": name, "recall": hits / len(QUESTIONS), "faithfulness": faithfulness / len(QUESTIONS),
            "latency_ms": elapsed_ms, "windows": len(windows)}


def main() -> None:
    traditional = run_pattern("traditional", contextual=False)
    late_approx = run_pattern("document-context approximation", contextual=True)
    print(f"{'strategy':32s} | recall@3 | faithfulness | latency | windows")
    for row in (traditional, late_approx):
        print(f"{row['name']:32s} | {row['recall']:8.1%} | {row['faithfulness']:12.1%} | "
              f"{row['latency_ms']:7.2f}ms | {row['windows']}")
    print("\nTraditional result:")
    pprint(traditional)
    print("\nLate-approximation result:")
    pprint(late_approx)
    print("Embedding API/key/cost: none; local feature hashing is used for this demo.")
    print("Limitation: contextual window prepending is not true late chunking/token pooling.")
    print("Where late chunking may lose: unrelated topics can blur together in a long document context.")


if __name__ == "__main__":
    main()

"""
All windows for traditional:

[window 1/4] indexed text:
7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent

[window 2/4] indexed text:
hall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giv

[window 3/4] indexed text:
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to wit

[window 4/4] indexed text:
ct has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.



Top-three retrieved windows: traditional

Question: Compare 7(7)(a) ease of use with 7(7)(c) minimum data.
Recall hit: True | Faithful: True

  [1] cosine=0.487
hall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giv

  [2] cosine=0.484
7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent

  [3] cosine=0.484
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to wit

Question: Relate withdrawal timing and ease of withdrawal.
Recall hit: True | Faithful: True

  [1] cosine=0.311
hall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giv

  [2] cosine=0.309
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to wit

  [3] cosine=0.283
7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent

Question: Does fraud invalidate consent that must be demonstrable?
Recall hit: True | Faithful: True

  [1] cosine=0.419
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to wit

  [2] cosine=0.412
hall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giv

  [3] cosine=0.410
7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent

Question: How do language coverage and clear language relate?
Recall hit: True | Faithful: True

  [1] cosine=0.135
hall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giv

  [2] cosine=0.134
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to wit

  [3] cosine=0.119
7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent

Question: Connect record keeping with withdrawal rights.
Recall hit: True | Faithful: True

  [1] cosine=0.212
hall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giv

  [2] cosine=0.210
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to wit

  [3] cosine=0.209
ct has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.



All windows for document-context approximation:

[window 1/4] indexed text:
Synthetic Article 7 consent withdrawal policy. 7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent
Original window:
7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent

[window 2/4] indexed text:
Synthetic Article 7 consent withdrawal policy. hall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giv
Original window:
hall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giv

[window 3/4] indexed text:
Synthetic Article 7 consent withdrawal policy. 7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to wit
Original window:
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to wit

[window 4/4] indexed text:
Synthetic Article 7 consent withdrawal policy. ct has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.


Original window:
ct has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.



Top-three retrieved windows: document-context approximation

Question: Compare 7(7)(a) ease of use with 7(7)(c) minimum data.
Recall hit: True | Faithful: True

  [1] cosine=0.490
hall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giv

  [2] cosine=0.488
7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent

  [3] cosine=0.487
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to wit

Question: Relate withdrawal timing and ease of withdrawal.
Recall hit: True | Faithful: True

  [1] cosine=0.317
hall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giv

  [2] cosine=0.315
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to wit

  [3] cosine=0.294
ct has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.



Question: Does fraud invalidate consent that must be demonstrable?
Recall hit: True | Faithful: True

  [1] cosine=0.422
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to wit

  [2] cosine=0.416
hall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giv

  [3] cosine=0.414
7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent

Question: How do language coverage and clear language relate?
Recall hit: True | Faithful: True

  [1] cosine=0.130
hall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giv

  [2] cosine=0.129
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to wit

  [3] cosine=0.115
7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent

Question: Connect record keeping with withdrawal rights.
Recall hit: True | Faithful: True

  [1] cosine=0.216
ct has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.



  [2] cosine=0.214
hall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giv

  [3] cosine=0.213
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud or coercion is void.
7(7) Withdrawal mechanisms must follow these requirements:
(a) shall be as easy to use as giving consent;
(b) shall be available in every language in which consent was requested;
(c) shall not require unnecessary personal data.
7(8) Maintain a record of consent and withdrawal.

7(1) Consent must be demonstrable.
7(2) Written consent must be clear and accessible.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contract performance must not require unnecessary consent.
7(5) Consent shall be as easy to wit
strategy                         | recall@3 | faithfulness | latency | windows
traditional                      |   100.0% |       100.0% |   11.09ms | 4
document-context approximation   |   100.0% |       100.0% |   11.27ms | 4

Traditional result:
{'faithfulness': 1.0,
 'latency_ms': 11.092999950051308,
 'name': 'traditional',
 'recall': 1.0,
 'windows': 4}

Late-approximation result:
{'faithfulness': 1.0,
 'latency_ms': 11.266299989074469,
 'name': 'document-context approximation',
 'recall': 1.0,
 'windows': 4}
Embedding API/key/cost: none; local feature hashing is used for this demo.
Limitation: contextual window prepending is not true late chunking/token pooling.
Where late chunking may lose: unrelated topics can blur together in a long document context.
"""