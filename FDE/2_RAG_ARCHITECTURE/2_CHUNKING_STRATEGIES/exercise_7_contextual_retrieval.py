"""Exercise 7: add document context to chunks before indexing.

Run with Python 3; no embedding key is needed. Local feature hashing is used for retrieval,
not OpenAI text-embedding-3-small or Voyage. Optionally install `openai`, set
TOGETHER_STUDY_API_KEY, and set USE_TOGETHER_CONTEXT=1 to generate chunk context with
openai/gpt-oss-120b. That option makes one chat request per chunk and does not use provider
prompt caching.

Lesson: context prefixes can help queries whose clue is weak or cross-references other
sections. Measure recall lift, add generation cost/latency at ingest, and remember that
prefixing alone is only an approximation of contextual retrieval.
"""

import hashlib
import math
import os
import re


ARTICLE = """Synthetic GDPR Article 7 consent notes.
7(1) Consent must be demonstrable.
7(2) Written consent must be distinguishable and use clear language.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contracts must not require consent to unnecessary processing.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
7(7) Withdrawal mechanisms shall meet the following requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was requested, including Spanish, and in accessible formats;
(c) shall not require disclosure of additional personal data beyond what is necessary to authenticate the data subject.
7(8) Maintain a record of consent and withdrawal.
"""
GOLDEN = [
    {"query": "In what languages must withdrawal mechanisms be available?", "clause": "(b) shall be available"},
    {"query": "Must withdrawing consent be as easy as giving it?", "clause": "(a) shall be as easy"},
    {"query": "What extra data may the withdrawal mechanism require?", "clause": "(c) shall not require"},
    {"query": "What record must the controller maintain?", "clause": "Maintain a record"},
    {"query": "Can consent be withdrawn at any time?", "clause": "right to withdraw consent at any time"},
    {"query": "Is pre-ticked box consent valid?", "clause": "pre-ticked box is void"},
]


def vectorize(text: str, dimensions: int = 256) -> list[float]:
    vector = [0.0] * dimensions
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        vector[int.from_bytes(digest[:4], "big") % dimensions] += 1.0 if digest[4] & 1 else -1.0
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def chunks(text: str, size: int = 512, overlap: int = 51) -> list[str]:
    step = size - overlap
    return [text[index:index + size] for index in range(0, len(text), step) if text[index:index + size].strip()]


def local_context(chunk: str) -> str:
    section_match = re.search(r"7\(\d+\)", chunk)
    section = section_match.group(0) if section_match else "Article 7"
    terms = [word for word in re.findall(r"[a-z]{5,}", chunk.lower()) if word not in {"shall", "which", "where", "their", "consent"}]
    keywords = ", ".join(dict.fromkeys(terms[:5])) or "consent policy"
    return f"This excerpt is from synthetic Article 7 section {section}; key topics: {keywords}. "


def maybe_generate_context(parts: list[str]) -> list[str]:
    if os.environ.get("USE_TOGETHER_CONTEXT") != "1":
        return [local_context(part) + part for part in parts]
    from openai import OpenAI

    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("USE_TOGETHER_CONTEXT=1 requires TOGETHER_STUDY_API_KEY.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    contextual = []
    for part in parts:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "Write one factual sentence locating a chunk within its source document. Do not add facts."},
                {"role": "user", "content": f"DOCUMENT:\n{ARTICLE}\n\nCHUNK:\n{part}"},
            ],
            max_tokens=100,
        )
        context = response.choices[0].message.content or ""
        contextual.append(context + " " + part)
    return contextual


def recall_at_k(raw_chunks: list[str], indexed_chunks: list[str], k: int = 5) -> tuple[float, dict[str, int]]:
    vectors = [vectorize(text) for text in indexed_chunks]
    per_query = {}
    for example in GOLDEN:
        query_vector = vectorize(example["query"])
        ranking = sorted(
            ((cosine(query_vector, vector), index) for index, vector in enumerate(vectors)),
            reverse=True,
        )[:k]
        hit = int(any(example["clause"].lower() in raw_chunks[index].lower() for _, index in ranking))
        per_query[example["query"]] = hit
    return sum(per_query.values()) / len(per_query), per_query


def main() -> None:
    raw_chunks = chunks(ARTICLE)
    contextual_chunks = maybe_generate_context(raw_chunks)
    print("\nBaseline chunks (raw text):")
    for index, chunk in enumerate(raw_chunks, 1):
        print(f"\n[baseline {index}/{len(raw_chunks)}]\n{chunk}")
    print("\nContextual retrieval chunks (generated context + raw text):")
    for index, chunk in enumerate(contextual_chunks, 1):
        print(f"\n[contextual {index}/{len(contextual_chunks)}]\n{chunk}")

    baseline, baseline_by_query = recall_at_k(raw_chunks, raw_chunks)
    contextual, contextual_by_query = recall_at_k(raw_chunks, contextual_chunks)
    improved = [query for query in baseline_by_query if not baseline_by_query[query] and contextual_by_query[query]]
    print(f"Chunks: {len(raw_chunks)}")
    print(f"Baseline local-hash recall@5: {baseline:.1%}")
    print(f"Contextual local-hash recall@5: {contextual:.1%}")
    print(f"Recall lift: {contextual - baseline:+.1%}")
    print("Query only contextual retrieval found:", improved[0] if improved else "none on this small synthetic corpus")
    print("Embedding model/key: none; local feature hashing is used. It is not a semantic embedding model.")
    print("Prompt-cache note: Together context generation does not use Anthropic cache_control; account for each request.")


if __name__ == "__main__":
    main()

"""
Baseline chunks (raw text):

[baseline 1/2]
Synthetic GDPR Article 7 consent notes.
7(1) Consent must be demonstrable.
7(2) Written consent must be distinguishable and use clear language.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contracts must not require consent to unnecessary processing.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
7(7) Withdrawal mechanisms shall meet the following requirements:
(a) shall be as easy to use as the m

[baseline 2/2]
 requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was requested, including Spanish, and in accessible formats;
(c) shall not require disclosure of additional personal data beyond what is necessary to authenticate the data subject.
7(8) Maintain a record of consent and withdrawal.


Contextual retrieval chunks (generated context + raw text):

[contextual 1/2]
This excerpt is from synthetic Article 7 section 7(1); key topics: synthetic, article, notes, demonstrable, written. Synthetic GDPR Article 7 consent notes.
7(1) Consent must be demonstrable.
7(2) Written consent must be distinguishable and use clear language.
7(3) The data subject has the right to withdraw consent at any time.
7(4) Contracts must not require consent to unnecessary processing.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
7(7) Withdrawal mechanisms shall meet the following requirements:
(a) shall be as easy to use as the m

[contextual 2/2]
This excerpt is from synthetic Article 7 section 7(8); key topics: requirements, mechanism, available, every, language.  requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was requested, including Spanish, and in accessible formats;
(c) shall not require disclosure of additional personal data beyond what is necessary to authenticate the data subject.
7(8) Maintain a record of consent and withdrawal.

Chunks: 2
Baseline local-hash recall@5: 100.0%
Contextual local-hash recall@5: 100.0%
Recall lift: +0.0%
Query only contextual retrieval found: none on this small synthetic corpus
Embedding model/key: none; local feature hashing is used. It is not a semantic embedding model.
Prompt-cache note: Together context generation does not use Anthropic cache_control; account for each request.
"""