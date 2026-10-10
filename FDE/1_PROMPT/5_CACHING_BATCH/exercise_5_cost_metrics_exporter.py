"""Exercise 5: track Together usage and expose Prometheus text metrics.

Run independently with `python -m pip install openai` and TOGETHER_STUDY_API_KEY set.
Optional rates: TOGETHER_INPUT_USD_PER_MILLION and TOGETHER_OUTPUT_USD_PER_MILLION.
The standard-library HTTP exporter serves /metrics on port 9100; dashboard.json is
written beside this script. No Anthropic client or API key is used.

Lesson: use tenant/customer labels for operational attribution, calculate cost from
token usage and a current rate card, and distinguish cache reads from all prompt tokens.
Never put personal identifiers in metric labels; labels must have bounded cardinality.
"""

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
METRICS: dict[tuple[str, str, str], dict[str, float]] = {}
DASHBOARD = {
    "title": "Together AI Cost and Prompt Cache",
    "panels": [
        {
            "type": "timeseries",
            "title": "Approximate cost by customer per day",
            "targets": [{"expr": "sum by (customer) (increase(gen_ai_cost_usd_total[1d]))", "legendFormat": "{{customer}}"}],
            "fieldConfig": {"defaults": {"unit": "currencyUSD"}},
        },
        {
            "type": "timeseries",
            "title": "Reported cached prompt token ratio",
            "targets": [{"expr": "avg by (customer) (gen_ai_cache_hit_ratio)", "legendFormat": "{{customer}}"}],
            "fieldConfig": {"defaults": {"unit": "percentunit", "min": 0, "max": 1}},
        },
    ],
    "alerts": [{"name": "cache_hit_ratio_low", "expr": "avg by (customer) (gen_ai_cache_hit_ratio) < 0.7", "for": "5m"}],
}


def get_cached_tokens(usage) -> int:
    details = getattr(usage, "prompt_tokens_details", None)
    if isinstance(details, dict):
        value = details.get("cached_tokens", 0)
    else:
        value = getattr(details, "cached_tokens", 0) if details else 0
    return int(value or 0)


def call_and_record(client: OpenAI, customer: str, tier: str, system_prompt: str, query: str):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
        max_tokens=150,
    )
    usage = response.usage
    prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
    cached_tokens = get_cached_tokens(usage) if usage else 0
    input_rate = os.environ.get("TOGETHER_INPUT_USD_PER_MILLION")
    output_rate = os.environ.get("TOGETHER_OUTPUT_USD_PER_MILLION")
    cost = None
    if input_rate and output_rate:
        cost = (prompt_tokens * float(input_rate) + completion_tokens * float(output_rate)) / 1_000_000
    key = (customer, tier, MODEL)
    metric = METRICS.setdefault(key, {"cost": 0.0, "calls": 0.0, "cache_ratio": 0.0})
    metric["cost"] += cost or 0.0
    metric["calls"] += 1
    metric["cache_ratio"] = cached_tokens / prompt_tokens if prompt_tokens else 0.0
    return response


def escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def render_metrics() -> bytes:
    lines = [
        "# HELP gen_ai_cost_usd_total Approximate cumulative Together API cost.",
        "# TYPE gen_ai_cost_usd_total counter",
        "# HELP gen_ai_cache_hit_ratio Provider-reported cached prompt tokens divided by prompt tokens.",
        "# TYPE gen_ai_cache_hit_ratio gauge",
    ]
    for (customer, tier, model), values in METRICS.items():
        labels = f'customer="{escape_label(customer)}",tier="{escape_label(tier)}",model="{escape_label(model)}"'
        lines.append(f"gen_ai_cost_usd_total{{{labels}}} {values['cost']}")
        lines.append(f"gen_ai_cache_hit_ratio{{{labels}}} {values['cache_ratio']}")
    return ("\n".join(lines) + "\n").encode("utf-8")


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_error(404)
            return
        body = render_metrics()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    output_dir = Path(__file__).resolve().parent
    (output_dir / "dashboard.json").write_text(json.dumps(DASHBOARD, indent=2), encoding="utf-8")
    server = ThreadingHTTPServer(("127.0.0.1", 9100), MetricsHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    stable_prefix = "Synthetic support policy: answer concisely, protect user data. " * 80
    for _ in range(2):
        call_and_record(client, "study_customer_a", "standard", stable_prefix, "How do I check a test payment?")
    metrics = urlopen("http://127.0.0.1:9100/metrics").read().decode("utf-8")
    print(metrics)
    print("Wrote dashboard.json and served the smoke-tested metrics endpoint on http://127.0.0.1:9100/metrics")
    print("Cost is shown as zero when rates are not configured; cache ratio uses provider metadata.")
    time.sleep(0.1)
    server.shutdown()
    server.server_close()


if __name__ == "__main__":
    main()