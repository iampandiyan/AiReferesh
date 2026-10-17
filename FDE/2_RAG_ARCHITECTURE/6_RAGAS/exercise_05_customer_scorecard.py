"""Exercise 5: render a one-page HTML RAG scorecard.

Run with `python exercise_05_customer_scorecard.py`; writes an HTML file to the
current working directory. Uses only the Python standard library.

Behavior: renders four metric cards with a traffic light, quarter-over-quarter
delta, inline SVG trend, and generated commentary.

Lesson: customer-facing scorecards should show both current quality and trend.
The threshold and the change from the prior period answer different questions.
"""

from html import escape
from pathlib import Path


GATE = {
    "faithfulness": 0.85,
    "answer_relevancy": 0.85,
    "context_precision": 0.80,
    "context_recall": 0.80,
}


def traffic_light(value, gate):
    if value >= gate:
        return "#0d9488"
    if value >= gate - 0.05:
        return "#f59e0b"
    return "#e11d48"


def sparkline(trend, gate, width=120, height=28):
    if not trend:
        raise ValueError("Each metric needs at least one trend point.")
    low, high = min(min(trend), gate), max(max(trend), gate)
    span = high - low or 1.0
    step = width / max(1, len(trend) - 1)
    points = " ".join(
        f"{index * step:.1f},{height - (value - low) / span * height:.1f}"
        for index, value in enumerate(trend)
    )
    gate_y = height - (gate - low) / span * height
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'role="img" aria-label="metric trend">'
        f'<line x1="0" y1="{gate_y:.1f}" x2="{width}" y2="{gate_y:.1f}" '
        'stroke="#94a3b8" stroke-dasharray="3 3" stroke-width="1"/>'
        f'<polyline points="{points}" fill="none" stroke="#0891b2" stroke-width="2"/>'
        "</svg>"
    )


def commentary(scores, deltas):
    breached = [metric for metric, value in scores.items() if value < GATE[metric]]
    improved = [metric for metric, delta in deltas.items() if delta > 0.005]
    dropped = [metric for metric, delta in deltas.items() if delta < -0.005]
    parts = [
        "All four metrics clear the gate."
        if not breached
        else "Below gate: " + ", ".join(breached) + " - merge blocked."
    ]
    if improved:
        parts.append("Up vs last quarter: " + ", ".join(improved) + ".")
    if dropped:
        parts.append("Down vs last quarter: " + ", ".join(dropped) + " - watch for drift.")
    return " ".join(parts)


def scorecard(scores, customer_name, period, deltas, trends):
    missing = sorted(set(GATE) - set(scores))
    if missing:
        raise ValueError("Missing metric scores: " + ", ".join(missing))
    cards = []
    for metric, gate in GATE.items():
        value = scores[metric]
        if not 0 <= value <= 1:
            raise ValueError(f"{metric} score must be between 0 and 1.")
        color = traffic_light(value, gate)
        delta = deltas.get(metric, 0.0)
        metric_trend = trends.get(metric)
        if metric_trend is None:
            raise ValueError(f"Missing trend for {metric}.")
        cards.append(
            f'<article class="card" style="border-top-color:{color}">'
            f'<div class="label">{escape(metric.replace("_", " "))}</div>'
            f'<div class="value" style="color:{color}">{value:.2f}</div>'
            f'<div class="delta">{delta:+.2f} vs prior quarter; gate {gate:.2f}</div>'
            f'<div>{sparkline(metric_trend, gate)}</div></article>'
        )
    return (
        "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>RAG scorecard</title>"
        "<style>body{font:15px Arial,sans-serif;background:#fafaf9;color:#0f172a;"
        "margin:2rem}.wrap{max-width:760px;margin:auto;padding:1.5rem;border:1px "
        "solid #e7e5e4;border-radius:12px}.cards{display:flex;flex-wrap:wrap;gap:12px}"
        ".card{background:white;border:1px solid #e7e5e4;border-top:4px solid;"
        "border-radius:10px;padding:12px;min-width:150px;flex:1}"
        ".label{text-transform:uppercase;color:#64748b;font-size:11px}"
        ".value{font-size:24px;font-weight:bold}.delta{font-size:12px;color:#475569}"
        "</style><main class=\"wrap\"><h1>RAG scorecard</h1>"
        f"<p>Customer: <strong>{escape(customer_name)}</strong>; period "
        f"<strong>{escape(period)}</strong>; region us-east1</p>"
        f'<section class="cards">{"".join(cards)}</section>'
        f"<p>{escape(commentary(scores, deltas))}</p></main></html>"
    )


def main():
    scores = {
        "faithfulness": 0.91,
        "answer_relevancy": 0.93,
        "context_precision": 0.86,
        "context_recall": 0.79,
    }
    deltas = {
        "faithfulness": 0.04,
        "answer_relevancy": 0.01,
        "context_precision": -0.02,
        "context_recall": -0.06,
    }
    trends = {
        "faithfulness": [0.86, 0.88, 0.91],
        "answer_relevancy": [0.90, 0.92, 0.93],
        "context_precision": [0.88, 0.87, 0.86],
        "context_recall": [0.85, 0.83, 0.79],
    }
    report = scorecard(scores, "AcmeCorp EU-bank", "Q3 2026", deltas, trends)
    output = Path.cwd() / "exercise_05_scorecard.html"
    output.write_text(report, encoding="utf-8")
    print(f"{output} written ({len(report)} characters)")
    print(commentary(scores, deltas))


if __name__ == "__main__":
    main()
