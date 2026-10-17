"""Exercise 2: compare sparse BM25-style retrieval on exact and paraphrased queries.

Run: python exercise_02_bm25_exact_vs_paraphrase.py

Behavior: computes a compact BM25 score using only the standard library. The
corpus includes exact AML section references and GDPR rights content.

Lesson: lexical retrieval is excellent when query terms match the source, but
does not understand a paraphrase that uses different vocabulary.
"""

import math
import re


CORPUS = [
    "AML bulletin 4.5.2 requires banks to verify beneficial ownership.",
    "AML bulletin 4.5.2 sets enhanced due diligence thresholds.",
    "AML bulletin 4.5.2 requires suspicious activity reports.",
    "The AML 4.5 series governs customer due diligence.",
    "National banks follow anti-money laundering guidance.",
    "GDPR gives data subjects rights to access personal information.",
    "Individuals may request erasure of their personal data under GDPR.",
    "The right to portability lets people transfer their personal data.",
    "Organizations must answer data subject access requests.",
    "Privacy policy notes explain personal information handling.",
]


def tokenize(text):
    return re.findall(r"[a-z0-9.]+", text.lower())


def bm25_scores(query, documents, k1=1.5, b=0.75):
    tokenized = [tokenize(document) for document in documents]
    query_terms = tokenize(query)
    average_length = sum(map(len, tokenized)) / max(len(tokenized), 1)
    document_frequency = {
        term: sum(term in set(doc) for doc in tokenized)
        for term in set(query_terms)
    }
    scores = []
    for doc in tokenized:
        score = 0.0
        frequencies = {term: doc.count(term) for term in set(query_terms)}
        for term, frequency in frequencies.items():
            if not frequency:
                continue
            df = document_frequency[term]
            idf = math.log(1 + (len(documents) - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (1 - b + b * len(doc) / average_length)
            score += idf * frequency * (k1 + 1) / denominator
        scores.append(score)
    return scores


def search(query, k=5):
    scores = bm25_scores(query, CORPUS)
    return sorted(range(len(CORPUS)), key=lambda i: (-scores[i], i))[:k]


def show(query, relevant_ids):
    print(f'\nBM25-style top results for "{query}":')
    for rank, doc_id in enumerate(search(query), 1):
        relevant = doc_id in relevant_ids
        print(f"  {rank}. {'[relevant]' if relevant else '[other]'} {CORPUS[doc_id]}")
    print(f"  Relevant docs in top 5: {sum(doc_id in relevant_ids for doc_id in search(query))}")


def main():
    show("AML bulletin 4.5.2", {0, 1, 2})
    show("how can old profiles disappear permanently", {6})
    print("\nThe second query uses words absent from many relevant documents; lexical overlap is limited.")


if __name__ == "__main__":
    main()
"""
BM25-style top results for "AML bulletin 4.5.2":
  1. [relevant] AML bulletin 4.5.2 requires suspicious activity reports.
  2. [relevant] AML bulletin 4.5.2 sets enhanced due diligence thresholds.
  3. [relevant] AML bulletin 4.5.2 requires banks to verify beneficial ownership.
  4. [other] The AML 4.5 series governs customer due diligence.
  5. [other] National banks follow anti-money laundering guidance.
  Relevant docs in top 5: 3

BM25-style top results for "how can old profiles disappear permanently":
  1. [other] AML bulletin 4.5.2 requires banks to verify beneficial ownership.
  2. [other] AML bulletin 4.5.2 sets enhanced due diligence thresholds.
  3. [other] AML bulletin 4.5.2 requires suspicious activity reports.
  4. [other] The AML 4.5 series governs customer due diligence.
  5. [other] National banks follow anti-money laundering guidance.
  Relevant docs in top 5: 0

The second query uses words absent from many relevant documents; lexical overlap is limited.
"""