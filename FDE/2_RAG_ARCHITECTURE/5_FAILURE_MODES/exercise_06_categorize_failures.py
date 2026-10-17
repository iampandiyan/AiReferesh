"""Exercise 6: Categorize RAG failures and prioritize named fixes.

Run: python exercise_06_categorize_failures.py

Behavior: Runs the notebook's self-contained 20-row worked sample, writes
categorized_failures.csv and fix_memo.md next to this script, and prints an FM
frequency pivot with the top-three named fixes. It uses only the standard
library; the original graded task's separate 50-row CSV is not present here.

Lesson: Use a consistent failure taxonomy, quantify recurring failure modes,
and connect each priority to a concrete, testable fix. Keep uplift estimates
hedged; counts in an authored sample are not production incident statistics.
"""

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DiagRow:
    query_id: str
    query_text: str
    fm_primary: str
    fm_secondary: str
    fix_lesson: str
    fix_status: str
    notes: str


DIAG_ROWS = [
    DiagRow("q-001", "AcmeCorp retention rules que son para customer data?", "FM8", "FM4", "L4.5+L4.1", "TODO", "Code-mixed phrasing; English-only docs scored low."),
    DiagRow("q-002", "Data-Protection Standard clause 4.2 exact text", "FM3", "", "L4.5", "DONE", "Two versions retrieved; canonical dedupe applied."),
    DiagRow("q-003", "Compare retention rule with refund record-keeping", "FM6", "FM3", "L4.5", "TODO", "Multi-hop; one side missing in retrieved set."),
    DiagRow("q-004", "List grievance-redressal clauses", "FM7", "", "L4.5", "TODO", "Citations referenced docs not in retrieved set."),
    DiagRow("q-005", "Refund window in the 2018 policy", "FM5", "", "L4.5", "DONE", "Stale 2018 doc surfaced; TTL filter added."),
    DiagRow("q-006", "Default AcmeCorp retention window?", "FM1", "", "L4.5+L3.1", "TODO", "Needle at 50% of 30K context; recall dropped."),
    DiagRow("q-007", "los datos del cliente, cuantos dias se pueden conservar?", "FM8", "", "L4.1", "TODO", "Code-mixed; needs multilingual embedder."),
    DiagRow("q-008", "Refund Policy Section 3.2 exact wording", "FM2", "", "L4.3", "TODO", "Dense missed exact section; needs hybrid + BM25."),
    DiagRow("q-009", "Refund timeline for regulated-finance customers", "FM6", "FM2", "L4.5+L4.3", "TODO", "Multi-hop AND irrelevant top-K context."),
    DiagRow("q-010", "GDPR penalty schedule", "FM7", "FM4", "L4.5", "TODO", "Hallucinated clause numbers; tightened citation rule."),
    DiagRow("q-011", "Old 2019 retention policy still surfacing?", "FM5", "", "L4.5", "DONE", "Pre-2020 policy docs surfaced; TTL filter."),
    DiagRow("q-012", "GDPR vs HIPAA retention difference", "FM6", "", "L4.5", "TODO", "Cross-jurisdiction multi-hop."),
    DiagRow("q-013", "Default periodo de retencion de datos?", "FM8", "FM1", "L4.1+L4.5", "TODO", "Code-mixed and long context."),
    DiagRow("q-014", "Clause 4.2 amendment May 2025", "FM3", "", "L4.5", "DONE", "Conflicting versions resolved by canonical dedupe."),
    DiagRow("q-015", "Government-ID verification docs needed", "FM4", "", "L4.5", "TODO", "Irrelevant top-K; cosine threshold added."),
    DiagRow("q-016", "SOX Section 802 audit-trail exact wording", "FM2", "", "L4.3", "TODO", "Exact regulatory phrase; BM25 hybrid needed."),
    DiagRow("q-017", "Customer-grievance escalation steps", "FM7", "", "L4.5", "TODO", "Citation hallucination on escalation steps."),
    DiagRow("q-018", "Retention clause buried in a ~25K-token bundle", "FM1", "", "L4.5+L3.1", "TODO", "Needle lost in a long retrieved bundle."),
    DiagRow("q-019", "Recent May 2025 retention amendment summary", "FM3", "FM5", "L4.5", "DONE", "Newest version preferred; older purged by TTL."),
    DiagRow("q-020", "Data Controller vs Data Processor", "FM4", "", "L4.5", "TODO", "Irrelevant billing docs surfaced; cosine threshold."),
]
NAMED_FIXES = {
    "FM8": "Multilingual embeddings (e.g. voyage-3.5) with query-side language detection; evaluate code-mixed queries.",
    "FM3": "Deduplicate on canonical_doc_id and effective_date; retain the newest version with stable ordering.",
    "FM6": "Decompose into atomic sub-questions, retrieve per sub-question, and verify every comparison side is represented.",
    "FM7": "Validate each cited chunk id against retrieved ids, retry with feedback, and fail closed after a bounded retry count.",
    "FM1": "Reduce oversized context, rerank relevant chunks near the prompt end, and evaluate answer recall by evidence position.",
    "FM4": "Tune a cosine floor against labeled queries; report both off-topic rejection and relevant-document recall.",
    "FM5": "Filter by effective_date with an explicit historical-query exception; audit the chosen retention window.",
    "FM2": "Combine dense retrieval with BM25 for exact identifiers and phrases; measure recall@k by query type.",
}


def write_csv(path):
    fields = ["query_id", "query_text", "fm_primary", "fm_secondary", "fix_lesson", "fix_status", "notes"]
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for row in DIAG_ROWS:
            writer.writerow(row.__dict__)


def build_memo(counts, top3):
    total = len(DIAG_ROWS)
    frequency = "\n".join(
        f"- {mode}: {count} ({100 * count / total:.1f}%)"
        for mode, count in counts.most_common()
    )
    fixes = "\n".join(f"- {mode}: {NAMED_FIXES[mode]}" for mode in top3)
    uplift = (
        "No numerical uplift is asserted from this authored sample. Estimate a range "
        "for each proposed fix only after measuring a labeled baseline; rerun the same "
        "evaluation set after each change and report estimate versus observed change."
    )
    runbook = (
        "Sample failed and successful production queries by query type, preserve the "
        "retrieved ids and scores, and first check whether the gold source was retrieved. "
        "If it was absent, investigate chunking, embeddings, hybrid retrieval, or language "
        "coverage. If present but demoted, inspect reranking and top-k. If present near the "
        "top but unused or mis-cited, inspect context placement, prompt constraints, and "
        "citation validation. Assign a named owner, change one factor at a time, and rerun "
        "the fixed evaluation set with query-level metrics. Escalate unresolved cases for "
        "manual evidence review; never infer production impact from this 20-row example."
    )
    return (
        "# RAG failure triage memo (authored 20-row sample)\n\n"
        "## Frequency\n" + frequency + "\n\n"
        "## Top-three named fixes\n" + fixes + "\n\n"
        "## Uplift estimates\n" + uplift + "\n\n"
        "## Diagnostic flow runbook\n" + runbook + "\n"
    )


def main():
    output_dir = Path(__file__).resolve().parent
    csv_path = output_dir / "categorized_failures.csv"
    memo_path = output_dir / "fix_memo.md"
    counts = Counter(row.fm_primary for row in DIAG_ROWS)
    top3 = [mode for mode, _ in counts.most_common(3)]
    write_csv(csv_path)
    memo_path.write_text(build_memo(counts, top3), encoding="utf-8")

    print("Primary failure-mode counts:")
    for mode, count in counts.most_common():
        print(f"  {mode}: {count:>2} ({100 * count / len(DIAG_ROWS):4.1f}%)")
    print("\nTop-three fixes:")
    for mode in top3:
        print(f"  {mode}: {NAMED_FIXES[mode]}")
    print(f"\nWrote {csv_path.name} ({len(DIAG_ROWS)} authored sample rows)")
    print(f"Wrote {memo_path.name}")


if __name__ == "__main__":
    main()
