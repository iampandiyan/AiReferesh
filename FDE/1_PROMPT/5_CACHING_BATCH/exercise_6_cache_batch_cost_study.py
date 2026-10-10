"""Exercise 6: measure prompt layouts and workload modes with Together usage data.

Run independently with `python -m pip install openai` and TOGETHER_STUDY_API_KEY set.
The script embeds 100 synthetic Stripe queries, samples 20 by default, and writes
JSONL/results/dashboard/memo/runbook outputs next to itself. Set MEASURE_LIMIT for
a smaller API run. Set Together per-million rates to calculate dollar estimates.

This exercise uses concurrent Together chat requests for the overnight workload; it
does not call or assume an OpenAI Batch API or a 50% batch discount. Together cache
hits are measured only if usage metadata reports them. Optional
TOGETHER_CACHED_INPUT_USD_PER_MILLION can specify a documented cached-token price.

Lesson: compare measured usage, cache signals, and latency; scale estimates cautiously.
Cache invalidation, provider pricing, and batch SLA are operational assumptions, not
guarantees derived from synthetic queries.
"""

import concurrent.futures
import datetime
import hashlib
import json
import math
import os
import statistics
import time
from pathlib import Path

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
DAILY_VOLUME = 50_000
SYSTEM_PLAIN = "You are a Stripe merchant-support assistant. Answer briefly using the user message."
SYSTEM_STABLE = ("You are a Stripe merchant-support RAG assistant. Use only the synthetic policy below, "
                 "protect customer information, and answer in the language used by the merchant. "
                 "Refund status depends on payment state. Unauthorized activity must be escalated. "
                 "Settlement timing is determined by account configuration. KYC requires approved "
                 "business verification. Examples: code-mixed Spanish and English requests should "
                 "receive concise answers in the same language. Never invent transaction details. " * 45)
SEED_QUERIES = [
    "Procesa el refund de pay_TEST29Qw, 18 dolares porfa",
    "El settlement no llego ni despues de T+2",
    "Por que el KYC esta pending todavia?",
    "El payment fallo pero me cobraron la card",
    "Mi card tiene unauthorized transactions, parece fraud",
]


def build_queries() -> list[dict[str, str]]:
    rows = []
    for index in range(100):
        query = SEED_QUERIES[index % len(SEED_QUERIES)]
        if index >= len(SEED_QUERIES):
            query += f" (synthetic case {index:03d})"
        rows.append({"custom_id": f"stripe-q-{index:03d}", "query": query})
    return rows


def extract_cached_tokens(usage) -> int:
    details = getattr(usage, "prompt_tokens_details", None)
    if isinstance(details, dict):
        value = details.get("cached_tokens", 0)
    else:
        value = getattr(details, "cached_tokens", 0) if details else 0
    return int(value or 0)


def call_one(client: OpenAI, query: str, system_prompt: str, mode: str) -> dict:
    started = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
        max_tokens=180,
    )
    elapsed = time.perf_counter() - started
    usage = response.usage
    prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
    cached_tokens = extract_cached_tokens(usage) if usage else 0
    return {
        "mode": mode,
        "prompt_tokens": prompt_tokens,
        "cached_prompt_tokens": cached_tokens,
        "completion_tokens": completion_tokens,
        "latency_seconds": elapsed,
        "response": response.choices[0].message.content or "",
    }


def configured_cost(prompt_tokens: int, cached_tokens: int, completion_tokens: int) -> float | None:
    input_rate = os.environ.get("TOGETHER_INPUT_USD_PER_MILLION")
    output_rate = os.environ.get("TOGETHER_OUTPUT_USD_PER_MILLION")
    if not input_rate or not output_rate:
        return None
    cached_rate = float(os.environ.get("TOGETHER_CACHED_INPUT_USD_PER_MILLION", input_rate))
    normal_tokens = max(0, prompt_tokens - cached_tokens)
    return (
        normal_tokens * float(input_rate)
        + cached_tokens * cached_rate
        + completion_tokens * float(output_rate)
    ) / 1_000_000


def wilson_interval(hits: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return 0.0, 0.0
    proportion = hits / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    spread = z * math.sqrt(
        (proportion * (1 - proportion) + z * z / (4 * total)) / total
    ) / denominator
    return center - spread, center + spread


def p95(values: list[float]) -> float:
    return sorted(values)[max(0, math.ceil(0.95 * len(values)) - 1)]


def aggregate(rows: list[dict]) -> dict:
    costs = [row["cost_usd"] for row in rows]
    return {
        "calls": len(rows),
        "mean_prompt_tokens": statistics.mean(row["prompt_tokens"] for row in rows),
        "mean_cached_prompt_tokens": statistics.mean(row["cached_prompt_tokens"] for row in rows),
        "mean_completion_tokens": statistics.mean(row["completion_tokens"] for row in rows),
        "mean_latency_seconds": statistics.mean(row["latency_seconds"] for row in rows),
        "p95_latency_seconds": p95([row["latency_seconds"] for row in rows]),
        "cost_per_call": statistics.mean(costs) if all(cost is not None for cost in costs) else None,
    }


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    limit = int(os.environ.get("MEASURE_LIMIT", "20"))
    if not 1 <= limit <= 100:
        raise ValueError("MEASURE_LIMIT must be between 1 and 100")

    output_dir = Path(__file__).resolve().parent
    queries = build_queries()
    (output_dir / "eval_100.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in queries), encoding="utf-8"
    )
    selected = queries[:limit]
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    measured: dict[str, list[dict]] = {"baseline_realtime": [], "stable_prefix_realtime": [], "overnight_concurrent": []}

    for row in selected:
        item = call_one(client, row["query"], SYSTEM_PLAIN, "baseline_realtime")
        item["cost_usd"] = configured_cost(item["prompt_tokens"], item["cached_prompt_tokens"], item["completion_tokens"])
        item["custom_id"] = row["custom_id"]
        measured["baseline_realtime"].append(item)

    for row in selected:
        item = call_one(client, row["query"], SYSTEM_STABLE, "stable_prefix_realtime")
        item["cost_usd"] = configured_cost(item["prompt_tokens"], item["cached_prompt_tokens"], item["completion_tokens"])
        item["custom_id"] = row["custom_id"]
        measured["stable_prefix_realtime"].append(item)

    workers = int(os.environ.get("BATCH_WORKERS", "8"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(call_one, client, row["query"], SYSTEM_STABLE, "overnight_concurrent"): row
            for row in selected
        }
        for future in concurrent.futures.as_completed(futures):
            row = futures[future]
            item = future.result()
            item["cost_usd"] = configured_cost(item["prompt_tokens"], item["cached_prompt_tokens"], item["completion_tokens"])
            item["custom_id"] = row["custom_id"]
            measured["overnight_concurrent"].append(item)
    measured["overnight_concurrent"].sort(key=lambda item: item["custom_id"])

    summaries = {mode: aggregate(rows) for mode, rows in measured.items()}
    cached_avg = summaries["stable_prefix_realtime"]["cost_per_call"]
    batch_avg = summaries["overnight_concurrent"]["cost_per_call"]
    if cached_avg is not None and batch_avg is not None:
        blended_avg = 0.7 * cached_avg + 0.3 * batch_avg
    else:
        blended_avg = None
    summaries["blended_70_30"] = {"cost_per_call": blended_avg, "calls": limit}

    rows = [
        ("baseline (short prompt)", summaries["baseline_realtime"]["cost_per_call"]),
        ("stable-prefix realtime", cached_avg),
        ("overnight concurrent", batch_avg),
        ("blended 70/30", blended_avg),
    ]
    print(f"Measured {limit} synthetic queries per mode; total requests: {limit * 3}.")
    print(f"{'mode':26s} | $/call | $/day at 50K | $/month")
    print("-" * 78)
    for name, per_call in rows:
        if per_call is None:
            print(f"{name:26s} | rates not configured")
        else:
            daily = per_call * DAILY_VOLUME
            print(f"{name:26s} | ${per_call:.6f} | ${daily:.2f} | ${daily * 30:.2f}")
    print("Cached token means:", summaries["stable_prefix_realtime"]["mean_cached_prompt_tokens"])
    print("Concurrent path is not a discounted provider batch endpoint; no batch discount was assumed.")

    result_path = output_dir / "measure_results.json"
    result_path.write_text(json.dumps({"summaries": summaries, "calls": measured}, indent=2), encoding="utf-8")
    dashboard = {
        "title": "FDE prompt cost and cache study",
        "panels": [
            {"type": "timeseries", "title": "Approximate cost per customer/day", "targets": [{"expr": "sum by (customer) (increase(gen_ai_cost_usd_total[1d]))"}], "fieldConfig": {"defaults": {"unit": "currencyUSD"}}},
            {"type": "timeseries", "title": "Provider-reported cache ratio", "targets": [{"expr": "avg by (customer) (gen_ai_cache_hit_ratio)"}], "fieldConfig": {"defaults": {"unit": "percentunit", "min": 0, "max": 1}}},
        ],
        "alerts": [{"name": "cache_hit_ratio_low", "expr": "avg by (customer) (gen_ai_cache_hit_ratio) < 0.7", "for": "5m"}],
    }
    (output_dir / "dashboard.json").write_text(json.dumps(dashboard, indent=2), encoding="utf-8")

    if cached_avg is not None and blended_avg is not None:
        monthly_saving = (cached_avg - blended_avg) * DAILY_VOLUME * 30
        headline = f"At the measured sample rates, the 70/30 blend estimates approximately ${monthly_saving:.2f}/month difference from all stable-prefix realtime at 50,000 calls/day."
    else:
        headline = "Monthly savings are not estimated because current Together token rates were not configured."
    memo = f"""# CFO Memo: Prompt Cost and Workload Mix

{headline}

This is an approximate extrapolation from {limit} synthetic queries per mode using the configured model, openai/gpt-oss-120b. The estimate assumes 50,000 requests each day, a 30-day month, the measured prompt/output token mix, and a 70% stable-prefix realtime plus 30% concurrent overnight workload. Token rates must be supplied from the current Together rate card; reported cache tokens are priced at the normal input rate unless a separately verified cached-input rate is configured. Prices and provider behavior may change.

The comparison uses a short-prompt baseline and a longer stable RAG prefix; those prompts have different input sizes, so this is a workflow comparison, not an isolated test of a cache discount. Together usage metadata may or may not report cached tokens for this model. Concurrent submission is not a native batch API and receives no assumed batch discount.

Risks include policy revisions invalidating reusable context, cache availability changing by model or provider, and asynchronous processing missing deadlines for urgent support requests. Production measurement should use representative, approved data, tenant-isolated metrics, and a larger evaluation sample. Do not place customer identifiers or raw prompts in metric labels or long-lived logs. Before launch, verify current pricing, cache behavior, latency objectives, and data-retention rules. Consult the cache-invalidation runbook when the stable policy prefix changes.
"""
    (output_dir / "cfo_memo.md").write_text(memo, encoding="utf-8")
    runbook = """# Cache Invalidation Runbook

1. Compute and record the SHA-256 hash of the revised stable prompt; identify the policy revision.
2. Warm the new prefix with an approved synthetic canary request.
3. Verify provider-reported cache usage and confirm the cache-hit dashboard alert recovers above 0.7.
4. If cache behavior or output quality does not recover, disable the cache-dependent optimization, page the on-call owner, and investigate before routing production traffic back.
"""
    (output_dir / "runbook.md").write_text(runbook, encoding="utf-8")

    print(f"P95 stable-prefix latency: {summaries['stable_prefix_realtime']['p95_latency_seconds']:.2f}s")
    print(f"Wrote eval_100.jsonl, measure_results.json, dashboard.json, cfo_memo.md, and runbook.md in {output_dir}")
    print("Rates are approximate and may drift; see cfo_memo.md for assumptions and risks.")


if __name__ == "__main__":
    main()