"""Exercise 2: compare measured cost for repeated prompts with cache metadata.

Run independently with `python -m pip install openai` and TOGETHER_STUDY_API_KEY set.
Rates are read from TOGETHER_INPUT_USD_PER_MILLION and
TOGETHER_OUTPUT_USD_PER_MILLION. Optional discounted cached-input rate:
TOGETHER_CACHED_INPUT_USD_PER_MILLION. Without rates, report tokens only.

Lesson: count cached tokens separately only when the provider reports them. Do not apply
Anthropic rates or assume a Together cache discount; verify current model pricing first.
"""

import os
import statistics

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
SYSTEM_PROMPT = ("You are a small-business lending advisor. Follow these synthetic policy notes: "
                "explain assumptions, avoid inventing applicant information, distinguish APR "
                "from monthly rates, and give concise estimates. " * 120)
QUERY = "Estimate the monthly payment for a $2,400 loan at 18% APR over 24 months."
CALLS_PER_MODE = int(os.environ.get("CACHE_COST_CALLS", "10"))


def usage_cost(usage) -> tuple[float | None, int, int, int]:
    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
    completion_tokens = getattr(usage, "completion_tokens", 0) or 0
    details = getattr(usage, "prompt_tokens_details", None)
    cached = (details.get("cached_tokens", 0) if isinstance(details, dict)
              else getattr(details, "cached_tokens", 0) if details else 0) or 0
    input_rate = os.environ.get("TOGETHER_INPUT_USD_PER_MILLION")
    output_rate = os.environ.get("TOGETHER_OUTPUT_USD_PER_MILLION")
    if not input_rate or not output_rate:
        return None, prompt_tokens, cached, completion_tokens
    cached_rate = float(os.environ.get("TOGETHER_CACHED_INPUT_USD_PER_MILLION", input_rate))
    uncached_tokens = max(0, prompt_tokens - cached)
    cost = (uncached_tokens * float(input_rate) + cached * cached_rate
            + completion_tokens * float(output_rate)) / 1_000_000
    return cost, prompt_tokens, cached, completion_tokens


def measure(client: OpenAI, use_same_prompt_label: str) -> list[dict]:
    measured = []
    for _ in range(CALLS_PER_MODE):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": QUERY}],
            max_tokens=100,
        )
        cost, prompt, cached, completion = usage_cost(response.usage)
        measured.append({"cost": cost, "prompt": prompt, "cached": cached, "completion": completion})
    print(f"{use_same_prompt_label}: sent {len(measured)} identical system-prefix requests")
    return measured


def main() -> None:
    if CALLS_PER_MODE < 1:
        raise ValueError("CACHE_COST_CALLS must be positive")
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    no_cache = measure(client, "comparison A")
    repeated_prefix = measure(client, "comparison B")

    def summarize(rows: list[dict]) -> str:
        costs = [row["cost"] for row in rows]
        if all(cost is not None for cost in costs):
            return f"${sum(costs):.6f}"
        total_tokens = sum(row["prompt"] + row["completion"] for row in rows)
        return f"rates not configured ({total_tokens} total tokens)"

    cached_tokens = sum(row["cached"] for row in repeated_prefix)
    print(f"{'mode':24s} | total cost / usage")
    print("-" * 68)
    print(f"{'first comparison':24s} | {summarize(no_cache)}")
    print(f"{'repeated prefix':24s} | {summarize(repeated_prefix)}")
    print(f"Provider-reported cached tokens in repeated-prefix run: {cached_tokens}")
    if all(row["cost"] is not None for row in no_cache + repeated_prefix):
        baseline = sum(row["cost"] for row in no_cache)
        repeated = sum(row["cost"] for row in repeated_prefix)
        savings = 100 * (baseline - repeated) / baseline if baseline else 0
        print(f"Cost difference: {savings:.1f}% (can be negative due to response variation)")
    print("These are separate request groups, not a controlled provider cache-on/cache-off switch.")
    print("Rates are user-configured and should be checked against the current Together rate card.")


if __name__ == "__main__":
    main()