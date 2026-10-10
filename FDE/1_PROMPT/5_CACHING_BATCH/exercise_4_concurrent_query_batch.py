"""Exercise 4: submit 100 code-mixed queries concurrently through Together.

Run independently with `python -m pip install openai` and TOGETHER_STUDY_API_KEY set.
The script writes its own JSONL input and results. This is a concurrent client-side
batch, not OpenAI's Batch API and not a promised discounted Together batch product.
Set BATCH_QUERY_LIMIT to a smaller positive value for a lower-cost test.

Lesson: batching can mean workload orchestration, while provider batch endpoints and
discounts are separate capabilities. Track custom IDs and parse every result; never
assume a discount that the provider did not report or document.
"""

import json
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
SEED_QUERIES = [
    "Necesito un loan de $2,400, mi salary es 45K. Eligible?",
    "Calcula el monthly payment: $3,600, 13%, 24 months.",
    "Mi credit score es 690, puedo get a home loan?",
    "Personal loan vs business loan - cual es better para un shop?",
    "Cuanto dan por un secured loan?",
]
SYSTEM = "Classify lending intent using one label only: payment, eligibility, comparison, other."


def build_queries() -> list[str]:
    queries = []
    for index in range(100):
        query = SEED_QUERIES[index % len(SEED_QUERIES)]
        queries.append(query if index < len(SEED_QUERIES) else f"{query} (synthetic variant {index})")
    return queries


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    limit = int(os.environ.get("BATCH_QUERY_LIMIT", "100"))
    if not 1 <= limit <= 100:
        raise ValueError("BATCH_QUERY_LIMIT must be from 1 to 100")

    queries = build_queries()[:limit]
    output_dir = Path(__file__).resolve().parent
    input_path = output_dir / "together_batch_input.jsonl"
    results_path = output_dir / "together_batch_results.jsonl"
    lines = [
        json.dumps({"custom_id": f"q-{index:03d}", "query": query}, ensure_ascii=False)
        for index, query in enumerate(queries)
    ]
    input_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert len(lines) == limit
    assert len({json.loads(line)["custom_id"] for line in lines}) == limit

    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    max_workers = int(os.environ.get("BATCH_WORKERS", "8"))
    results = []
    started = time.perf_counter()

    def classify(custom_id: str, query: str) -> dict:
        call_started = time.perf_counter()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": query}],
            max_tokens=30,
        )
        usage = response.usage
        return {
            "custom_id": custom_id,
            "query": query,
            "content": response.choices[0].message.content or "",
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
            "latency_seconds": time.perf_counter() - call_started,
        }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(classify, f"q-{index:03d}", query): index
            for index, query in enumerate(queries)
        }
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda item: item["custom_id"])
    results_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in results), encoding="utf-8"
    )
    print(f"Input JSONL: {input_path} ({limit} unique queries)")
    print(f"Results JSONL: {results_path} ({len(results)} parsed results)")
    print(f"Concurrent workers: {max_workers}; wall time: {time.perf_counter() - started:.2f}s")
    print(f"Mean per-request latency: {statistics.mean(row['latency_seconds'] for row in results):.2f}s")
    print(f"Total tokens: input={sum(row['prompt_tokens'] for row in results)}, "
          f"output={sum(row['completion_tokens'] for row in results)}")
    print("This client-side concurrent workload does not imply a 50% provider batch discount.")


if __name__ == "__main__":
    main()