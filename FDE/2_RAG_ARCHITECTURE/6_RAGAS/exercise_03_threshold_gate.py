"""Exercise 3: a deterministic four-metric RAG quality gate.

Run with `python exercise_03_threshold_gate.py`. No external packages or API key
are needed; the judge scores are intentionally stubbed to make the gate repeatable.

Behavior: demonstrates a passing run and a simulated regression that fails with
the metric name, observed value, and required threshold.

Lesson: use explicit thresholds for all required metrics. A deterministic gate is
easy to debug, but a production gate must consume measured evaluation results.
"""

THRESHOLDS = {
    "faithfulness": 0.85,
    "answer_relevancy": 0.85,
    "context_precision": 0.80,
    "context_recall": 0.80,
}


def stub_judge_scores(regression=False):
    """Return fixed example scores standing in for an evaluator result."""
    if regression:
        return {
            "faithfulness": 0.78,
            "answer_relevancy": 0.88,
            "context_precision": 0.82,
            "context_recall": 0.83,
        }
    return {
        "faithfulness": 0.91,
        "answer_relevancy": 0.90,
        "context_precision": 0.86,
        "context_recall": 0.84,
    }


def assert_gate(scores, thresholds=THRESHOLDS):
    missing = sorted(set(thresholds) - set(scores))
    if missing:
        raise ValueError("Missing metric scores: " + ", ".join(missing))
    breaches = [
        f"{metric}={scores[metric]:.2f} < {threshold:.2f}"
        for metric, threshold in thresholds.items()
        if scores[metric] < threshold
    ]
    if breaches:
        raise AssertionError("RAG CI gate FAILED: " + "; ".join(breaches))


def test_ragas_gate(regression=False):
    """Gate one deterministic score payload; raises AssertionError on breach."""
    assert_gate(stub_judge_scores(regression=regression))


def main():
    test_ragas_gate()
    print("clean run: PASS (gate green)")
    try:
        test_ragas_gate(regression=True)
    except AssertionError as error:
        print("regression run: FAIL as expected ->", error)
    else:
        raise AssertionError("The deliberate regression unexpectedly passed.")


if __name__ == "__main__":
    main()
