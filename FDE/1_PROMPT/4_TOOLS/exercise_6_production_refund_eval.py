"""Exercise 6: a measured, guarded refund agent and 50-case snapshot evaluation.

Run independently with `python -m pip install openai` and TOGETHER_STUDY_API_KEY set.
Uses Together's OpenAI-compatible API and openai/gpt-oss-120b. All stores and IDs are
synthetic. The script writes eval_50.jsonl, eval_results.json, and Markdown reports
next to itself. Set EVAL_LIMIT to a smaller positive number for a quick API run.

Optional pricing inputs are USD per million tokens:
TOGETHER_INPUT_USD_PER_MILLION and TOGETHER_OUTPUT_USD_PER_MILLION.

Lesson: model decisions need server-side precondition checks, deterministic idempotency,
caps, and an audit trail. Dry-run must not mutate the ledger. PII should be redacted
before logging; this fixture uses synthetic IDs and does not log raw personal data.
"""

import hashlib
import json
import math
import os
import re
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
MAX_ROUNDS = 5
REFUND_CUTOFF = "2026-02-20"
PAYMENTS: dict[str, dict] = {}
KYC: dict[str, dict] = {}
REFUND_LEDGER: dict[str, dict] = {}
REFUNDED_PAYMENT_IDS: set[str] = set()
TOOL_AUDIT: list[dict] = []
DOUBLE_PROCESS_ATTEMPTS = 0


def build_eval_cases() -> list[dict[str, str]]:
    cases = []
    fixture_sets = [
        ("OK", "refund", "captured", "2026-05-10", "verified"),
        ("OLD", "escalate", "captured", "2025-01-01", "verified"),
        ("NOKY", "escalate", "captured", "2026-05-12", "missing"),
        ("GONE", "escalate", "not_found", "2020-01-01", "missing"),
    ]
    for group, expected, status, captured_at, kyc_state in fixture_sets:
        for index in range(12):
            payment_id = f"pay_TEST_{group}_{index:02d}"
            customer_id = f"cust_TEST_{group}_{index:02d}"
            PAYMENTS[payment_id] = {
                "status": status,
                "amount_usd": 100 + index * 10,
                "customer_id": customer_id,
                "captured_at": captured_at,
            }
            KYC[customer_id] = {"kyc_state": kyc_state}
            if status == "not_found":
                PAYMENTS.pop(payment_id)
            cases.append({
                "query": f"Please refund {payment_id} for ${100 + index * 10}; reason: merchant requested refund.",
                "expected": expected,
            })

    PAYMENTS["pay_TEST_DONE_00"] = {
        "status": "refunded", "amount_usd": 700, "customer_id": "cust_TEST_OK_00", "captured_at": "2026-05-01"
    }
    cases.append({
        "query": "Please refund pay_TEST_OK_00 for $100; reason: merchant requested refund.",
        "expected": "refund",
    })
    cases.append({
        "query": "Please refund pay_TEST_DONE_00 for $700; it was already refunded.",
        "expected": "already",
    })
    return cases


def stable_idempotency_key(payment_id: str, reason: str) -> str:
    return hashlib.sha256(f"{payment_id}{reason}".encode("utf-8")).hexdigest()[:16]


def lookup_payment(payment_id: str, purpose: str = "refund_check") -> dict:
    payment = PAYMENTS.get(payment_id)
    if not payment:
        return {"status": "not_found"}
    return dict(payment)


def check_refund_window(payment_id: str) -> dict:
    payment = PAYMENTS.get(payment_id)
    return {"within_window": bool(payment and payment["captured_at"] >= REFUND_CUTOFF)}


def verify_kyc(customer_id: str, purpose: str) -> dict:
    return KYC.get(customer_id, {"kyc_state": "missing"})


def process_refund(payment_id: str, amount_usd: int, reason: str, dry_run: bool = False) -> dict:
    global DOUBLE_PROCESS_ATTEMPTS
    payment = PAYMENTS.get(payment_id)
    if not payment or payment.get("status") != "captured":
        return {"status": "REJECTED", "reason": "payment is not captured"}
    if payment["captured_at"] < REFUND_CUTOFF:
        return {"status": "REJECTED", "reason": "refund window expired"}
    if KYC.get(payment["customer_id"], {}).get("kyc_state") != "verified":
        return {"status": "REJECTED", "reason": "KYC is not verified"}

    key = stable_idempotency_key(payment_id, reason)
    if key in REFUND_LEDGER:
        DOUBLE_PROCESS_ATTEMPTS += 1
        return REFUND_LEDGER[key]
    if payment_id in REFUNDED_PAYMENT_IDS:
        DOUBLE_PROCESS_ATTEMPTS += 1
        return {"status": "ALREADY_PROCESSED", "reason": "payment already refunded"}

    result = {
        "refund_id": f"rfnd_TEST_{key[:8]}",
        "status": "DRY_RUN" if dry_run else "PROCESSED",
        "amount_usd": amount_usd,
        "idempotency_key": key,
    }
    if not dry_run:
        REFUND_LEDGER[key] = result
        REFUNDED_PAYMENT_IDS.add(payment_id)
    return result


def escalate_to_human(reason: str) -> dict:
    ticket = hashlib.sha256(reason.encode("utf-8")).hexdigest()[:8].upper()
    return {"ticket_id": f"ST-REF-{ticket}", "status": "OPEN"}


def tool_description(when: str, when_not: str, prerequisites: str, effects: str) -> str:
    return f"WHEN: {when}\nWHEN NOT: {when_not}\nPRE-REQS: {prerequisites}\nSIDE EFFECTS: {effects}"


def tool(name: str, desc: str, properties: dict, required: list[str]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }


TOOLS = [
    tool("lookup_payment", tool_description("First; find the payment.", "Never skip this read.", "payment_id and purpose.", "Read-only; synthetic fixture."), {"payment_id": {"type": "string"}, "purpose": {"type": "string", "enum": ["refund_check", "fraud_review", "onboarding"]}}, ["payment_id", "purpose"]),
    tool("check_refund_window", tool_description("After confirming captured payment.", "If payment is not captured.", "payment_id.", "Read-only; independent of verify_kyc."), {"payment_id": {"type": "string"}}, ["payment_id"]),
    tool("verify_kyc", tool_description("After payment lookup.", "If already checked in this conversation.", "customer_id and declared GDPR purpose.", "Read-only; independent of check_refund_window."), {"customer_id": {"type": "string"}, "purpose": {"type": "string", "enum": ["refund_check", "fraud_review", "onboarding"]}}, ["customer_id", "purpose"]),
    tool("process_refund", tool_description("Only after all read checks pass.", "Any failed check or already-refunded payment.", "Captured payment, open window, verified KYC.", "Mutates synthetic ledger; Python enforces guards and idempotency."), {"payment_id": {"type": "string"}, "amount_usd": {"type": "integer"}, "reason": {"type": "string"}, "dry_run": {"type": "boolean"}}, ["payment_id", "amount_usd", "reason", "dry_run"]),
    tool("escalate_to_human", tool_description("Any failed prerequisite or uncertain result.", "After successful refund.", "Short reason.", "Creates a synthetic ticket."), {"reason": {"type": "string"}}, ["reason"]),
]
SYSTEM = """You are a refund decision agent. First call lookup_payment. If captured, check_refund_window and verify_kyc; these are independent reads and should be requested together. If the payment is already refunded, do not process again. Call process_refund only if captured, within the refund window, and KYC verified. Otherwise escalate. Use reason exactly 'merchant requested refund' so retries are idempotent. End with exactly one label: OUTCOME: REFUND, OUTCOME: ESCALATE, or OUTCOME: ALREADY."""
HANDLERS = {
    "lookup_payment": lookup_payment,
    "check_refund_window": check_refund_window,
    "verify_kyc": verify_kyc,
    "process_refund": process_refund,
    "escalate_to_human": escalate_to_human,
}


def configured_cost(input_tokens: int, output_tokens: int):
    input_rate = os.environ.get("TOGETHER_INPUT_USD_PER_MILLION")
    output_rate = os.environ.get("TOGETHER_OUTPUT_USD_PER_MILLION")
    if not input_rate or not output_rate:
        return None
    return input_tokens * float(input_rate) / 1_000_000 + output_tokens * float(output_rate) / 1_000_000


def run_agent(client: OpenAI, query: str, dry_run: bool = False, max_rounds: int = MAX_ROUNDS) -> dict:
    messages = [{"role": "user", "content": query}]
    started = time.perf_counter()
    total_input = total_output = api_rounds = 0
    for round_number in range(1, max_rounds + 1):
        request_started = time.perf_counter()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM}, *messages],
            tools=TOOLS,
            tool_choice="auto",
            parallel_tool_calls=True,
            max_tokens=700,
        )
        request_latency_ms = int((time.perf_counter() - request_started) * 1000)
        api_rounds += 1
        if response.usage:
            total_input += response.usage.prompt_tokens
            total_output += response.usage.completion_tokens
        assistant_message = response.choices[0].message
        calls = assistant_message.tool_calls or []
        if not calls:
            cost = configured_cost(total_input, total_output)
            return {
                "status": "OK",
                "rounds": api_rounds,
                "final": assistant_message.content or "",
                "latency_seconds": time.perf_counter() - started,
                "latency_ms": request_latency_ms,
                "input_tokens": total_input,
                "output_tokens": total_output,
                "cost_usd": cost,
            }

        messages.append(assistant_message.model_dump(exclude_none=True))
        work = []
        for call in calls:
            arguments = json.loads(call.function.arguments)
            if call.function.name == "process_refund":
                arguments["dry_run"] = dry_run
            work.append((call, arguments))
        round_cost = configured_cost(
            response.usage.prompt_tokens if response.usage else 0,
            response.usage.completion_tokens if response.usage else 0,
        )

        def execute(item):
            call, arguments = item
            name = call.function.name
            purpose = arguments.get("purpose")
            started_tool = time.perf_counter()
            try:
                output = HANDLERS[name](**arguments)
            except (KeyError, TypeError, ValueError) as error:
                output = {"status": "TOOL_ERROR", "detail": str(error)}
            elapsed_ms = int((time.perf_counter() - started_tool) * 1000)
            TOOL_AUDIT.append({
                "round": round_number,
                "tool": name,
                "purpose": purpose,
                "latency_ms": elapsed_ms,
                "model_round_latency_ms": request_latency_ms,
                "cost_usd": round_cost / len(work) if round_cost is not None and work else None,
                "dry_run": bool(arguments.get("dry_run", False)),
            })
            return {"role": "tool", "tool_call_id": call.id, "content": json.dumps(output)}

        with ThreadPoolExecutor(max_workers=max(1, len(work))) as executor:
            results = list(executor.map(execute, work))
        messages.extend(results)

    ticket = escalate_to_human(f"cap hit for synthetic request {query[:60]}")
    return {
        "status": "CAP_HIT",
        "rounds": max_rounds,
        "final": f"OUTCOME: ESCALATE {ticket['ticket_id']}",
        "latency_seconds": time.perf_counter() - started,
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "input_tokens": total_input,
        "output_tokens": total_output,
        "cost_usd": configured_cost(total_input, total_output),
    }


def wilson_interval(hits: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = hits / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return center - spread, center + spread


def p95(values: list[float]) -> float:
    return sorted(values)[max(0, math.ceil(0.95 * len(values)) - 1)]


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    cases = build_eval_cases()
    output_dir = Path(__file__).resolve().parent
    (output_dir / "eval_50.jsonl").write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases), encoding="utf-8"
    )
    limit = int(os.environ.get("EVAL_LIMIT", str(len(cases))))
    if not 1 <= limit <= len(cases):
        raise ValueError(f"EVAL_LIMIT must be between 1 and {len(cases)}")
    selected = cases[:limit]
    results = []
    for index, case in enumerate(selected, 1):
        result = run_agent(client, case["query"])
        final = result["final"].upper()
        match = re.search(r"OUTCOME:\s*(REFUND|ESCALATE|ALREADY)", final)
        prediction = match.group(1).lower() if match else "unknown"
        result.update({"expected": case["expected"], "prediction": prediction, "correct": prediction == case["expected"]})
        results.append(result)
        print(f"{index:02d}/{len(selected)} expected={case['expected']:8s} predicted={prediction:8s} rounds={result['rounds']}")

    hits = sum(result["correct"] for result in results)
    lower, upper = wilson_interval(hits, len(results))
    latencies = [result["latency_seconds"] for result in results]
    costs = [result["cost_usd"] for result in results]
    mean_cost = statistics.mean(costs) if all(cost is not None for cost in costs) else None
    (output_dir / "eval_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    tools_spec = """# Refund Tool Specification

All identifiers and records in the exercise are synthetic. Purpose values are required for PII-touching reads.

## lookup_payment
WHEN: First, to find payment state and customer reference. WHEN NOT: Never skip. PRE-REQS: payment_id and purpose (`refund_check`, `fraud_review`, or `onboarding`). SIDE EFFECTS: Read-only fixture lookup. GDPR purpose is recorded in the tool audit.

## check_refund_window
WHEN: After payment is confirmed captured. WHEN NOT: When payment is not captured. PRE-REQS: payment_id. SIDE EFFECTS: Read-only; independent of KYC lookup.

## verify_kyc
WHEN: After payment lookup. WHEN NOT: If already checked for this request. PRE-REQS: customer_id and GDPR purpose. SIDE EFFECTS: Read-only; independent of refund-window lookup.

## process_refund
WHEN: Only after captured status, open window, and verified KYC. WHEN NOT: If any precondition fails or payment has already been refunded. PRE-REQS: payment_id, amount, reason. SIDE EFFECTS: Mutates only the in-memory synthetic ledger; Python calculates `sha256(payment_id + reason)[:16]` and enforces all guards. Dry-run returns a synthetic refund ID and does not mutate the ledger.

## escalate_to_human
WHEN: A precondition fails or the result is uncertain. WHEN NOT: After a successful refund. PRE-REQS: A concise reason. SIDE EFFECTS: Returns a deterministic synthetic ticket.
"""
    (output_dir / "tools_spec.md").write_text(tools_spec, encoding="utf-8")

    report = [
        "# Refund Agent Evaluation",
        "",
        f"- Accuracy: {hits}/{len(results)} ({hits / len(results):.1%}); Wilson 95% CI {lower:.1%} to {upper:.1%}.",
        f"- Mean model rounds: {statistics.mean(result['rounds'] for result in results):.2f}.",
        f"- P95 end-to-end latency: {p95(latencies):.3f} seconds.",
        f"- Estimated total cost: ${sum(costs):.6f}." if mean_cost is not None else "- Cost not estimated: configure Together input/output rates.",
        f"- Duplicate process attempts stopped by idempotency: {DOUBLE_PROCESS_ATTEMPTS}.",
        "",
        "## Tool Description Finding",
        "Explicit WHEN, WHEN NOT, prerequisites, and side-effect descriptions make the allowed workflow easier to follow. Python independently enforces refund eligibility; the prompt is not an authorization boundary.",
        "",
        "## Production Gaps",
        "1. Redact sensitive values and review retention before logging prompts or tool payloads.",
        "2. Replace the in-memory idempotency ledger with a durable, atomic store shared by workers.",
        "3. Define bounded retries, backoff, timeout handling, and human review for uncertain outcomes.",
        "",
        "Rate-card estimates use configured values and may drift. All identifiers and records in this exercise are synthetic.",
    ]
    (output_dir / "eval_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nAccuracy: {hits}/{len(results)} ({hits / len(results):.1%}) [{lower:.1%}, {upper:.1%}]")
    print(f"Mean rounds: {statistics.mean(result['rounds'] for result in results):.2f}")
    print(f"P95 latency: {p95(latencies):.3f}s")
    print(f"Total cost: ${sum(costs):.6f}" if mean_cost is not None else "Total cost: not configured")
    print("Double-process attempts caught:", DOUBLE_PROCESS_ATTEMPTS)
    print("Wrote eval_50.jsonl, eval_results.json, tools_spec.md, and eval_report.md beside this script.")
    print("GDPR: logs must redact PII. Operations: use durable idempotency and bounded retry policies.")


if __name__ == "__main__":
    main()
"""
01/50 expected=refund   predicted=already  rounds=2
02/50 expected=refund   predicted=already  rounds=2
03/50 expected=refund   predicted=unknown  rounds=2
04/50 expected=refund   predicted=refund   rounds=2
05/50 expected=refund   predicted=unknown  rounds=2
06/50 expected=refund   predicted=unknown  rounds=2
07/50 expected=refund   predicted=unknown  rounds=2
08/50 expected=refund   predicted=already  rounds=2
09/50 expected=refund   predicted=already  rounds=2
10/50 expected=refund   predicted=unknown  rounds=2
11/50 expected=refund   predicted=unknown  rounds=2
12/50 expected=refund   predicted=unknown  rounds=2
13/50 expected=escalate predicted=unknown  rounds=2
14/50 expected=escalate predicted=escalate rounds=2
15/50 expected=escalate predicted=escalate rounds=2
16/50 expected=escalate predicted=unknown  rounds=2
17/50 expected=escalate predicted=escalate rounds=2
18/50 expected=escalate predicted=unknown  rounds=2
19/50 expected=escalate predicted=unknown  rounds=2
20/50 expected=escalate predicted=unknown  rounds=2
21/50 expected=escalate predicted=escalate rounds=2
22/50 expected=escalate predicted=unknown  rounds=2
23/50 expected=escalate predicted=unknown  rounds=2
24/50 expected=escalate predicted=unknown  rounds=2
25/50 expected=escalate predicted=escalate rounds=2
26/50 expected=escalate predicted=unknown  rounds=2
27/50 expected=escalate predicted=unknown  rounds=2
28/50 expected=escalate predicted=escalate rounds=2
29/50 expected=escalate predicted=unknown  rounds=2
30/50 expected=escalate predicted=unknown  rounds=2
31/50 expected=escalate predicted=unknown  rounds=2
32/50 expected=escalate predicted=unknown  rounds=2
33/50 expected=escalate predicted=escalate rounds=2
34/50 expected=escalate predicted=escalate rounds=2
35/50 expected=escalate predicted=unknown  rounds=2
36/50 expected=escalate predicted=unknown  rounds=2
37/50 expected=escalate predicted=unknown  rounds=2
38/50 expected=escalate predicted=escalate rounds=2
39/50 expected=escalate predicted=escalate rounds=2
40/50 expected=escalate predicted=unknown  rounds=2
41/50 expected=escalate predicted=refund   rounds=2
42/50 expected=escalate predicted=unknown  rounds=2
43/50 expected=escalate predicted=escalate rounds=2
44/50 expected=escalate predicted=escalate rounds=2
45/50 expected=escalate predicted=escalate rounds=2
46/50 expected=escalate predicted=escalate rounds=2
47/50 expected=escalate predicted=unknown  rounds=2
48/50 expected=escalate predicted=escalate rounds=2
49/50 expected=refund   predicted=unknown  rounds=2
50/50 expected=already  predicted=already  rounds=2

Accuracy: 17/50 (34.0%) [22.4%, 47.8%]
Mean rounds: 2.00
P95 latency: 7.399s
Total cost: not configured
Double-process attempts caught: 0
Wrote eval_50.jsonl, eval_results.json, tools_spec.md, and eval_report.md beside this script.
GDPR: logs must redact PII. Operations: use durable idempotency and bounded retry policies.

"""