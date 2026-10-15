"""Exercise 8: self-contained chunking pipeline and migration artifacts.

Run with Python 3; no API key, embedding service, or third-party package is required.
This exercise uses local feature hashing as a deterministic retrieval stand-in; it is
not a trained embedding model, and its faithfulness figures are only teaching metrics.
Generated memo and runbook files are written to exercise_8_output/ beside this script.

Lesson: choose chunking per document type, preserve table headers, compare strategies on
a golden set, version every chunk, guard against stale versions, and budget the full
migration separately from raw re-embedding. Verify current embedding rates before budgeting.
"""

import hashlib
import json
import math
import re
import os
from pathlib import Path


ARTICLE = """Synthetic policy, Article 7 consent.
7(1) Processing based on consent must be demonstrable.
7(2) Written consent must be distinguishable, intelligible, and use clear and plain language.
7(3) The data subject has the right to withdraw consent at any time; withdrawal does not affect prior lawful processing.
7(4) Consider whether contract performance is conditional on consent to unnecessary processing.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and accessible formats;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
7(8) The controller shall maintain a record of consent and withdrawal and provide it to the supervisory authority on request.
"""
CLAUSES = [
    ("(b) shall be available", "7(7)"),
    ("(a) shall be as easy", "7(7)"),
    ("(c) shall not require", "7(7)"),
    ("maintain a record of consent", "7(8)"),
    ("right to withdraw consent at any time", "7(3)"),
    ("pre-ticked box is void", "7(6)"),
    ("clear and plain language", "7(2)"),
    ("must be demonstrable", "7(1)"),
    ("as easy to withdraw as to give", "7(5)"),
    ("contract performance is conditional", "7(4)"),
]
GOLDEN = [
    {
        "query": query,
        "clause": clause,
        "header": header,
    }
    for clause, header in CLAUSES
    for query in (
        f"What does the synthetic article say about {clause.replace('(', '').replace(')', '')}?",
        f"Explain the policy rule for {clause.replace('(', '').replace(')', '')}.",
    )
]
OUTPUT_DIR = Path(__file__).resolve().parent / "exercise_8_output"
CURRENT_CHUNKER_VERSION = "v2-semantic-hier"
CHUNKER_MEMO = {
    "PDF body": ("semantic + hierarchical", "paragraph boundaries preserve clauses; parent expansion restores citations"),
    "numbered tables": ("row-as-chunk + replicated header", "each retrieved row retains its column meaning"),
    "footnotes": ("attach to parent clause", "an orphan footnote lacks its subject"),
    "annexures": ("header-based + hierarchical", "preserve schedule and annex identifiers"),
    "lending memos": ("semantic", "topic boundaries fit argumentative prose"),
    "chat transcripts": ("speaker-turn chunks + thread parent", "preserve speaker attribution and conversation context"),
}


def vectorize(text: str, dimensions: int = 256) -> list[float]:
    vector = [0.0] * dimensions
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        vector[int.from_bytes(digest[:4], "big") % dimensions] += 1 if digest[4] & 1 else -1
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def fixed_chunks(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    step = size - overlap
    return [text[index:index + size] for index in range(0, len(text), step) if text[index:index + size].strip()]


def semantic_hierarchical(text: str) -> list[tuple[str, str]]:
    sections = [section.strip() for section in re.split(r"(?=7\(\d+\))", text) if section.strip()]
    output = []
    for section in sections:
        header = section.splitlines()[0]
        # Short sections remain intact; longer ones split on sentence/semicolon boundaries.
        child_parts = [part.strip() for part in re.split(r"(?<=[.;])\s+(?=[A-Z(])", section) if part.strip()]
        for child in child_parts:
            output.append((child, section))
    return output


def late_windows(text: str, size: int = 1000, overlap: int = 150) -> list[str]:
    step = size - overlap
    return [text[index:index + size] for index in range(0, len(text), step) if text[index:index + size].strip()]


def retrieve_context(chunks: list[tuple[str, str]], query: str, k: int = 5) -> str:
    query_vector = vectorize(query)
    ranked = sorted(
        ((cosine(query_vector, vectorize(search_text)), parent_text) for search_text, parent_text in chunks),
        key=lambda pair: pair[0], reverse=True,
    )[:k]
    return "\n".join(parent for _, parent in ranked)


def evaluate_strategy(strategy: str) -> tuple[float, list[str]]:
    if strategy == "fixed-500":
        records = [(chunk, chunk) for chunk in fixed_chunks(ARTICLE)]
    elif strategy == "semantic+hierarchical":
        records = semantic_hierarchical(ARTICLE)
    elif strategy == "late-approximation":
        windows = late_windows((ARTICLE + "\n") * 3)
        records = [("Synthetic Article 7 context " + window, window) for window in windows]
    else:
        raise ValueError(strategy)

    print(f"\nChunks for strategy: {strategy}")
    for index, (indexed_text, source_text) in enumerate(records, 1):
        print(f"\n[chunk {index}/{len(records)}] indexed text:\n{indexed_text}")
        if source_text != indexed_text:
            label = "Parent section" if strategy == "semantic+hierarchical" else "Original window"
            print(f"{label}:\n{source_text}")

    failures = []
    hits = 0
    for example in GOLDEN:
        context = retrieve_context(records, example["query"])
        faithful = example["clause"].lower() in context.lower() and example["header"].lower() in context.lower()
        hits += faithful
        if not faithful:
            failures.append(example["query"])
    return hits / len(GOLDEN), failures


def row_as_chunks(csv_text: str) -> tuple[str, list[str]]:
    lines = [line for line in csv_text.splitlines() if line.strip()]
    if not lines:
        return "", []
    header = lines[0]
    return header, [f"{header}\n{row}" for row in lines[1:]]


def validate_no_orphans(chunks: list[str], header: str) -> bool:
    orphans = [index for index, chunk in enumerate(chunks) if not chunk.startswith(header + "\n")]
    if orphans:
        raise ValueError(f"orphan table rows without replicated header: {orphans}")
    return True


def stamp_chunk(text: str, doc_id: str, section_id: str, version: str = CURRENT_CHUNKER_VERSION) -> dict:
    return {"text": text, "doc_id": doc_id, "section_id": section_id, "chunker_version": version}


def read_guard(chunk: dict, current: str = CURRENT_CHUNKER_VERSION) -> dict:
    if chunk.get("chunker_version") != current:
        raise RuntimeError(f"stale chunk version {chunk.get('chunker_version')!r}; expected {current!r}")
    return chunk


def write_deliverables(results: list[dict], reembed_usd: float | None) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    memo_lines = ["# Chunker Selection Memo", "", "| Document type | Strategy | Rationale |", "|---|---|---|"]
    memo_lines.extend(f"| {kind} | {strategy} | {why} |" for kind, (strategy, why) in CHUNKER_MEMO.items())
    (OUTPUT_DIR / "chunker_memo.md").write_text("\n".join(memo_lines) + "\n", encoding="utf-8")
    eval_lines = ["# Faithfulness Evaluation", "", "| Strategy | Faithfulness | Example failure |", "|---|---:|---|"]
    eval_lines.extend(f"| {row['strategy']} | {row['faithfulness']:.1%} | {row['failure'] or 'none'} |" for row in results)
    (OUTPUT_DIR / "faithfulness_report.md").write_text("\n".join(eval_lines) + "\n", encoding="utf-8")
    raw_line = (f"Illustrative raw re-embed estimate: ~${reembed_usd:,.0f}, using 1.5B tokens at the lesson's example rate of $0.06/1M. Verify current provider/model pricing; excludes engineering, storage, compute, dual-write, validation, and rollback costs."
                if reembed_usd is not None else "Raw re-embed cost not calculated; set EMBEDDING_USD_PER_MILLION to a verified current rate.")
    runbook = f"""# Re-chunk Migration Runbook

1. **Dual-write:** stamp new chunks with `{CURRENT_CHUNKER_VERSION}` and write old/new indexes for a limited canary.
2. **Backfill:** process historical documents in bounded batches; track failures and verify table-row headers.
3. **Shadow-read:** compare faithfulness, retrieval latency, and error rates without changing user-visible answers.
4. **Cutover:** switch reads only after the promotion gate is met and owners approve.
5. **Rollback:** point reads to the prior index/version, stop new writes if needed, and preserve both indexes until reconciliation.

{raw_line}
"""
    (OUTPUT_DIR / "rechunk_runbook.md").write_text(runbook, encoding="utf-8")


def main() -> None:
    print("(1) Per-document chunker memo:")
    for kind, (strategy, reason) in CHUNKER_MEMO.items():
        print(f"  {kind:20s} -> {strategy:28s} | {reason}")

    strategies = ("fixed-500", "semantic+hierarchical", "late-approximation")
    results = []
    print("\n(2) Faithfulness on 20 synthetic queries:")
    for strategy in strategies:
        score, failures = evaluate_strategy(strategy)
        failure = failures[0] if failures else ""
        results.append({"strategy": strategy, "faithfulness": score, "failure": failure})
        print(f"  {strategy:24s} {score:.1%}; failing query: {failure or 'none'}")

    table = """Tier,RepoRate,Effective,Notification
Tier 1 (AAA),6.50%,2026-04-01,OCC-TEST-001
Tier 2 (AA),7.25%,2026-04-01,OCC-TEST-001
Tier 3 (A and below),8.10%,2026-04-01,OCC-TEST-001"""
    header, chunks = row_as_chunks(table)
    validate_no_orphans(chunks, header)
    deliberately_bad = [chunks[0]] + [chunk.split("\n", 1)[1] for chunk in chunks[1:]]
    try:
        validate_no_orphans(deliberately_bad, header)
    except ValueError as error:
        print("\n(4) Orphan-row guard caught:", error)
    else:
        raise AssertionError("Orphan table rows were not rejected")

    stamped = stamp_chunk("sample section", "article_TEST_7", "7(7)")
    assert read_guard(stamped)["chunker_version"] == CURRENT_CHUNKER_VERSION
    try:
        read_guard({**stamped, "chunker_version": "v1-fixed-500"})
    except RuntimeError as error:
        print("Version guard caught stale chunk:", error)
    else:
        raise AssertionError("Stale chunk version was not rejected")

    rate = os.environ.get("EMBEDDING_USD_PER_MILLION")
    reembed_usd = 1_500_000_000 / 1_000_000 * float(rate) if rate else None
    if reembed_usd is None:
        print("Raw re-embed estimate not computed; set EMBEDDING_USD_PER_MILLION to a verified current rate.")
    else:
        print(f"Illustrative raw re-embed cost at configured rate: ${reembed_usd:,.2f} (1.5B tokens)")

    write_deliverables(results, reembed_usd)
    print("\nEmbedding note: all retrieval here uses local feature hashing, not OpenAI/Voyage embeddings.")
    print("Generated chunker_memo.md, faithfulness_report.md, and rechunk_runbook.md in", OUTPUT_DIR)


if __name__ == "__main__":
    main()

"""
(1) Per-document chunker memo:
  PDF body             -> semantic + hierarchical      | paragraph boundaries preserve clauses; parent expansion restores citations
  numbered tables      -> row-as-chunk + replicated header | each retrieved row retains its column meaning
  footnotes            -> attach to parent clause      | an orphan footnote lacks its subject
  annexures            -> header-based + hierarchical  | preserve schedule and annex identifiers
  lending memos        -> semantic                     | topic boundaries fit argumentative prose
  chat transcripts     -> speaker-turn chunks + thread parent | preserve speaker attribution and conversation context

(2) Faithfulness on 20 synthetic queries:
  fixed-500                100.0%; failing query: none
  semantic+hierarchical    100.0%; failing query: none
  late-approximation       100.0%; failing query: none

(4) Orphan-row guard caught: orphan table rows without replicated header: [1, 2]
Version guard caught stale chunk: stale chunk version 'v1-fixed-500'; expected 'v2-semantic-hier'
Raw re-embed estimate not computed; set EMBEDDING_USD_PER_MILLION to a verified current rate.

Embedding note: all retrieval here uses local feature hashing, not OpenAI/Voyage embeddings.
Generated chunker_memo.md, faithfulness_report.md, and rechunk_runbook.md in C:\Storage\AI Development\GITCHECKOUT\AiReferesh\FDE\2_RAG_ARCHITECTURE\2_CHUNKING_STRATEGIES\exercise_8_output

(rag-labs) C:\Storage\AI Development\GITCHECKOUT\AiReferesh\FDE\2_RAG_ARCHITECTURE\2_CHUNKING_STRATEGIES>python exercise_8_production_chunking_pipeline.py
(1) Per-document chunker memo:
  PDF body             -> semantic + hierarchical      | paragraph boundaries preserve clauses; parent expansion restores citations
  numbered tables      -> row-as-chunk + replicated header | each retrieved row retains its column meaning
  footnotes            -> attach to parent clause      | an orphan footnote lacks its subject
  annexures            -> header-based + hierarchical  | preserve schedule and annex identifiers
  lending memos        -> semantic                     | topic boundaries fit argumentative prose
  chat transcripts     -> speaker-turn chunks + thread parent | preserve speaker attribution and conversation context

(2) Faithfulness on 20 synthetic queries:

Chunks for strategy: fixed-500

[chunk 1/3] indexed text:
Synthetic policy, Article 7 consent.
7(1) Processing based on consent must be demonstrable.
7(2) Written consent must be distinguishable, intelligible, and use clear and plain language.
7(3) The data subject has the right to withdraw consent at any time; withdrawal does not affect prior lawful processing.
7(4) Consider whether contract performance is conditional on consent to unnecessary processing.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud, coerci

[chunk 2/3] indexed text:
 give.
7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and accessible formats;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
7(8) The controller shall maintain a record of consent and withdr

[chunk 3/3] indexed text:
ller shall maintain a record of consent and withdrawal and provide it to the supervisory authority on request.

  fixed-500                100.0%; failing query: none

Chunks for strategy: semantic+hierarchical

[chunk 1/11] indexed text:
Synthetic policy, Article 7 consent.

[chunk 2/11] indexed text:
7(1) Processing based on consent must be demonstrable.

[chunk 3/11] indexed text:
7(2) Written consent must be distinguishable, intelligible, and use clear and plain language.

[chunk 4/11] indexed text:
7(3) The data subject has the right to withdraw consent at any time; withdrawal does not affect prior lawful processing.

[chunk 5/11] indexed text:
7(4) Consider whether contract performance is conditional on consent to unnecessary processing.

[chunk 6/11] indexed text:
7(5) Consent shall be as easy to withdraw as to give.

[chunk 7/11] indexed text:
7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.

[chunk 8/11] indexed text:
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
Parent section:
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and accessible formats;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.

[chunk 9/11] indexed text:
(b) shall be available in every language in which consent was originally requested, including Spanish and accessible formats;
Parent section:
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and accessible formats;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.

[chunk 10/11] indexed text:
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
Parent section:
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and accessible formats;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.

[chunk 11/11] indexed text:
7(8) The controller shall maintain a record of consent and withdrawal and provide it to the supervisory authority on request.
  semantic+hierarchical    100.0%; failing query: none

Chunks for strategy: late-approximation

[chunk 1/4] indexed text:
Synthetic Article 7 context Synthetic policy, Article 7 consent.
7(1) Processing based on consent must be demonstrable.
7(2) Written consent must be distinguishable, intelligible, and use clear and plain language.
7(3) The data subject has the right to withdraw consent at any time; withdrawal does not affect prior lawful processing.
7(4) Consider whether contract performance is conditional on consent to unnecessary processing.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and accessible formats;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
7(8) The controller shall maintain a record of consent and withdrawal and provide it to the supervisory authority o
Original window:
Synthetic policy, Article 7 consent.
7(1) Processing based on consent must be demonstrable.
7(2) Written consent must be distinguishable, intelligible, and use clear and plain language.
7(3) The data subject has the right to withdraw consent at any time; withdrawal does not affect prior lawful processing.
7(4) Consider whether contract performance is conditional on consent to unnecessary processing.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and accessible formats;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
7(8) The controller shall maintain a record of consent and withdrawal and provide it to the supervisory authority o

[chunk 2/4] indexed text:
Synthetic Article 7 context  to authenticate the data subject.
7(8) The controller shall maintain a record of consent and withdrawal and provide it to the supervisory authority on request.

Synthetic policy, Article 7 consent.
7(1) Processing based on consent must be demonstrable.
7(2) Written consent must be distinguishable, intelligible, and use clear and plain language.
7(3) The data subject has the right to withdraw consent at any time; withdrawal does not affect prior lawful processing.
7(4) Consider whether contract performance is conditional on consent to unnecessary processing.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and accessible formats;
(c) shall not require additional personal data beyond what
Original window:
 to authenticate the data subject.
7(8) The controller shall maintain a record of consent and withdrawal and provide it to the supervisory authority on request.

Synthetic policy, Article 7 consent.
7(1) Processing based on consent must be demonstrable.
7(2) Written consent must be distinguishable, intelligible, and use clear and plain language.
7(3) The data subject has the right to withdraw consent at any time; withdrawal does not affect prior lawful processing.
7(4) Consider whether contract performance is conditional on consent to unnecessary processing.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and accessible formats;
(c) shall not require additional personal data beyond what

[chunk 3/4] indexed text:
Synthetic Article 7 context guage in which consent was originally requested, including Spanish and accessible formats;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
7(8) The controller shall maintain a record of consent and withdrawal and provide it to the supervisory authority on request.

Synthetic policy, Article 7 consent.
7(1) Processing based on consent must be demonstrable.
7(2) Written consent must be distinguishable, intelligible, and use clear and plain language.
7(3) The data subject has the right to withdraw consent at any time; withdrawal does not affect prior lawful processing.
7(4) Consider whether contract performance is conditional on consent to unnecessary processing.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available
Original window:
guage in which consent was originally requested, including Spanish and accessible formats;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
7(8) The controller shall maintain a record of consent and withdrawal and provide it to the supervisory authority on request.

Synthetic policy, Article 7 consent.
7(1) Processing based on consent must be demonstrable.
7(2) Written consent must be distinguishable, intelligible, and use clear and plain language.
7(3) The data subject has the right to withdraw consent at any time; withdrawal does not affect prior lawful processing.
7(4) Consider whether contract performance is conditional on consent to unnecessary processing.
7(5) Consent shall be as easy to withdraw as to give.
7(6) Consent obtained through fraud, coercion, or a pre-ticked box is void.
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available

[chunk 4/4] indexed text:
Synthetic Article 7 context  void.
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and accessible formats;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
7(8) The controller shall maintain a record of consent and withdrawal and provide it to the supervisory authority on request.


Original window:
 void.
7(7) Withdrawal mechanisms shall meet these requirements:
(a) shall be as easy to use as the mechanism to give consent;
(b) shall be available in every language in which consent was originally requested, including Spanish and accessible formats;
(c) shall not require additional personal data beyond what is necessary to authenticate the data subject.
7(8) The controller shall maintain a record of consent and withdrawal and provide it to the supervisory authority on request.


  late-approximation       100.0%; failing query: none

(4) Orphan-row guard caught: orphan table rows without replicated header: [1, 2]
Version guard caught stale chunk: stale chunk version 'v1-fixed-500'; expected 'v2-semantic-hier'
Raw re-embed estimate not computed; set EMBEDDING_USD_PER_MILLION to a verified current rate.

Embedding note: all retrieval here uses local feature hashing, not OpenAI/Voyage embeddings.
Generated chunker_memo.md, faithfulness_report.md, and rechunk_runbook.md in C:\Storage\AI Development\GITCHECKOUT\AiReferesh\FDE\2_RAG_ARCHITECTURE\2_CHUNKING_STRATEGIES\exercise_8_output
"""