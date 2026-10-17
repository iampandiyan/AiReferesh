"""Exercise 6: run a compact RAG-evaluation CI composite.

Run with `python exercise_06_composite_ci.py`; creates `eval/golden.jsonl` and
`exercise_06_scorecard.html` under the current working directory. Standard library only.

Behavior: creates 50 explicitly illustrative golden rows, compares three fixed
evaluation iterations against standard and enterprise renewal gates, and emits a
customer report. Scores are fixtures, not results from a live Ragas evaluation.

Lesson: track multiple versions, record deltas, and apply stricter enterprise
thresholds explicitly. Synthetic questions are scaffolding, not SME-validated data.
"""

import html
import json
from pathlib import Path


TYPES = ("citation", "paraphrase", "multi_hop", "non_english")
LANGS = {
    "citation": "en",
    "paraphrase": "en",
    "multi_hop": "en",
    "non_english": "fr",
}
REFERENCES = {
    "citation": (
        "Which policy clause governs this question?",
        "Consult the cited governing policy clause; verify its current wording with the SME.",
        ["AcmeCorp policy fixture: citation question placeholder; replace with a reviewed clause."],
    ),
    "paraphrase": (
        "In plain language, what policy requirement applies to this scenario?",
        "The applicable requirement must be confirmed against the approved AcmeCorp policy.",
        ["AcmeCorp policy fixture: paraphrase example; replace with an SME-approved source."],
    ),
    "multi_hop": (
        "How do the two relevant policy requirements apply together?",
        "Apply both governing requirements; an SME must verify their interaction.",
        [
            "AcmeCorp policy fixture: first requirement; replace with a reviewed source.",
            "AcmeCorp policy fixture: second requirement; replace with a reviewed source.",
        ],
    ),
    "non_english": (
        "Quelle exigence de la politique s'applique a ce scenario?",
        "L'exigence applicable doit etre confirmee dans la politique approuvee par AcmeCorp.",
        ["Exemple de politique AcmeCorp: remplacer par une source validee par un expert."],
    ),
}
ITERATIONS = {
    "v1 baseline prompt": {
        "faithfulness": 0.81,
        "answer_relevancy": 0.88,
        "context_precision": 0.83,
        "context_recall": 0.80,
    },
    "v2 add citations": {
        "faithfulness": 0.87,
        "answer_relevancy": 0.90,
        "context_precision": 0.85,
        "context_recall": 0.82,
    },
    "v3 rerank + rewrite": {
        "faithfulness": 0.92,
        "answer_relevancy": 0.93,
        "context_precision": 0.88,
        "context_recall": 0.84,
    },
}
STANDARD_GATE = {
    "faithfulness": 0.85,
    "answer_relevancy": 0.85,
    "context_precision": 0.80,
    "context_recall": 0.80,
}
RENEWAL_GATE = {**STANDARD_GATE, "faithfulness": 0.90}


def build_golden_set():
    golden = []
    for index in range(50):
        kind = TYPES[index % len(TYPES)]
        question, reference, contexts = REFERENCES[kind]
        if LANGS[kind] == "fr":
            question = f"{question} (exemple {index + 1})"
        else:
            question = f"{question} (illustrative example {index + 1})"
        golden.append(
            {
                "user_input": question,
                "reference": reference,
                "reference_contexts": contexts,
                "metadata": {
                    "type": kind,
                    "lang": LANGS[kind],
                    "illustrative_placeholder": True,
                },
            }
        )
    return golden


def gate_report(scores, thresholds):
    breaches = [
        f"{metric} {scores[metric]:.2f}<{threshold:.2f}"
        for metric, threshold in thresholds.items()
        if scores[metric] < threshold
    ]
    return "PASS" if not breaches else "FAIL: " + ", ".join(breaches)


def scorecard_html(scores, previous_faithfulness):
    cards = []
    for metric, threshold in STANDARD_GATE.items():
        value = scores[metric]
        color = "#0d9488" if value >= threshold else "#e11d48"
        cards.append(
            f'<article style="border:1px solid #ddd;border-top:4px solid {color};'
            f'padding:12px"><strong>{html.escape(metric)}</strong>: {value:.2f} '
            f"(gate {threshold:.2f})</article>"
        )
    delta = scores["faithfulness"] - previous_faithfulness
    return (
        "<!doctype html><html lang='en'><meta charset='utf-8'><title>RAG scorecard</title>"
        "<style>body{font:15px Arial;margin:2rem}.cards{display:grid;"
        "grid-template-columns:repeat(2,minmax(180px,1fr));gap:12px}</style>"
        "<h1>AcmeCorp EU-bank RAG scorecard - v3</h1><p>Illustrative fixture; "
        "replace scores and golden rows with evaluated, SME-reviewed data.</p>"
        f"<p>Faithfulness delta vs v2: {delta:+.2f}</p>"
        f"<section class='cards'>{''.join(cards)}</section></html>"
    )


def main():
    golden = build_golden_set()
    golden_path = Path.cwd() / "eval" / "golden.jsonl"
    golden_path.parent.mkdir(parents=True, exist_ok=True)
    with golden_path.open("w", encoding="utf-8") as file:
        for row in golden:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{golden_path}: {len(golden)} illustrative rows")

    print("\nTrend across 3 iterations (standard gate / renewal gate):")
    previous = None
    for name, scores in ITERATIONS.items():
        delta = "" if previous is None else f"  d_faith={scores['faithfulness'] - previous:+.2f}"
        print(
            f"  {name:22s} standard={gate_report(scores, STANDARD_GATE):5s} "
            f"renewal={gate_report(scores, RENEWAL_GATE)}{delta}"
        )
        previous = scores["faithfulness"]

    report = scorecard_html(ITERATIONS["v3 rerank + rewrite"], ITERATIONS["v2 add citations"]["faithfulness"])
    report_path = Path.cwd() / "exercise_06_scorecard.html"
    report_path.write_text(report, encoding="utf-8")
    print(f"\n{report_path} written")


if __name__ == "__main__":
    main()
