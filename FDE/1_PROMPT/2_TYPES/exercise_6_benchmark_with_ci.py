"""Exercise 6: standalone benchmark with Wilson CIs, P95, and report files.

Run independently with the OpenAI SDK and TOGETHER_STUDY_API_KEY configured.
The full synthetic 50-query data set and all prompts are embedded in this script.
It writes bench_results.json, accuracy_table.md, cost_table.md, and recommendation.md
next to itself. Set BENCH_LIMIT to a smaller positive number for a quick test.

Cost estimate environment variables (USD per million tokens):
TOGETHER_INPUT_USD_PER_MILLION and TOGETHER_OUTPUT_USD_PER_MILLION.
Without both rates, cost columns say "not configured" rather than inventing prices.

Lesson: report uncertainty as well as point accuracy; overlapping confidence intervals
make small ranking differences inconclusive. Never log real customer PII or raw reasoning.
Retry parse failures carefully; make any side-effecting tool idempotent.
"""

import json
import math
import os
import re
import statistics
import time
from pathlib import Path

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
LABELS = ("refund", "payment", "kyc", "escalate", "inquire")
GOLDEN = [
    {"query": "Oye pay_TEST29Qw cuando llega mi refund, ya son 5 dias", "expected": "refund"},
    {"query": "necesito initiate el refund del customer, order cancelado", "expected": "refund"},
    {"query": "mi refund lleva 7 dias pending todavia", "expected": "refund"},
    {"query": "el refund de merch_4471 no se proceso", "expected": "refund"},
    {"query": "quiero mi dinero back, el order se cancelo", "expected": "refund"},
    {"query": "procesa el refund de $18 porfa", "expected": "refund"},
    {"query": "cuando se credita el refund a mi bank account", "expected": "refund"},
    {"query": "el customer pide refund de pay_TEST88, urgent", "expected": "refund"},
    {"query": "por que mi refund sigue en pending status", "expected": "refund"},
    {"query": "hazme el refund del pago duplicado", "expected": "refund"},
    {"query": "el payment fallo pero me cobraron la card", "expected": "payment"},
    {"query": "crea un payment link de 60 dolares para un customer", "expected": "payment"},
    {"query": "por que el charge aparece dos veces en pay_TEST12", "expected": "payment"},
    {"query": "el payment esta stuck, no avanza", "expected": "payment"},
    {"query": "la transaction fue declined sin reason", "expected": "payment"},
    {"query": "mi customer no puede completar el payment", "expected": "payment"},
    {"query": "el payment link expiro, necesito uno nuevo", "expected": "payment"},
    {"query": "donde veo el status de pay_TEST55", "expected": "payment"},
    {"query": "el cobro de la card no se refleja", "expected": "payment"},
    {"query": "quiero setup recurring payments para un cliente", "expected": "payment"},
    {"query": "mi kyc no se puede upload, da error", "expected": "kyc"},
    {"query": "el document verification aparece pending", "expected": "kyc"},
    {"query": "necesito reupload el kyc document de merch_8821", "expected": "kyc"},
    {"query": "por que el KYC esta pending todavia", "expected": "kyc"},
    {"query": "mi identidad no se verifica para activar payouts", "expected": "kyc"},
    {"query": "el SSN verification esta atascado", "expected": "kyc"},
    {"query": "subi el document pero el kyc sigue rejected", "expected": "kyc"},
    {"query": "que documentos necesito para el kyc", "expected": "kyc"},
    {"query": "mi verification lleva 3 dias sin resolverse", "expected": "kyc"},
    {"query": "el kyc de mi business account no pasa", "expected": "kyc"},
    {"query": "en mi account hay 4 unauthorized swipes, parece fraud", "expected": "escalate"},
    {"query": "alguien hizo un charge que yo no autorice", "expected": "escalate"},
    {"query": "creo que mi cuenta fue hacked, hay pagos raros", "expected": "escalate"},
    {"query": "un customer puso un dispute por wrong amount, urgent", "expected": "escalate"},
    {"query": "mi card tiene transacciones fraudulentas", "expected": "escalate"},
    {"query": "llego un chargeback del customer que no reconozco", "expected": "escalate"},
    {"query": "reporto una fraud transaction en pay_TEST99", "expected": "escalate"},
    {"query": "hay actividad sospechosa en mi merchant account", "expected": "escalate"},
    {"query": "me robaron la API key y hay cobros extranos", "expected": "escalate"},
    {"query": "necesito bloquear mi cuenta, posible fraude", "expected": "escalate"},
    {"query": "como uso el dashboard de Stripe", "expected": "inquire"},
    {"query": "donde consigo la API key", "expected": "inquire"},
    {"query": "cual es el pricing del prime tier", "expected": "inquire"},
    {"query": "necesito enable international cards", "expected": "inquire"},
    {"query": "el sales tax invoice no se puede download", "expected": "inquire"},
    {"query": "que es este transaction id en mi dashboard", "expected": "inquire"},
    {"query": "como cambio de bank transfer a card payouts", "expected": "inquire"},
    {"query": "cuales son los fees para international cards", "expected": "inquire"},
    {"query": "donde veo mis reports mensuales", "expected": "inquire"},
    {"query": "puedo tener multiple users en un account", "expected": "inquire"},
]
FEW_SHOT = """
[EXAMPLES]
Input: "pay_TEST1 necesito refund urgent" -> {"intent": "refund"}
Input: "mi verification no se completa" -> {"intent": "kyc"}
Input: "llegaron unauthorized charges, parece fraud" -> {"intent": "escalate"}
"""
BASE = "Classify this merchant message as one of: refund, payment, kyc, escalate, inquire. Return JSON only: {\"intent\": \"...\"}. Fraud or unauthorized charges always map to escalate."
PROMPTS = {
    "zero-shot": BASE,
    "few-shot-3": BASE + FEW_SHOT,
    "CoT-rationale": BASE + FEW_SHOT + " Give a concise, auditable one-sentence rationale before the JSON; do not reveal private chain-of-thought.",
}
POLICIES = {
    "refund": "Wants money returned or asks about refund status.",
    "payment": "Charge, payment link, declined payment, or payment completion issue.",
    "kyc": "Identity, document verification, or business verification issue.",
    "escalate": "Fraud, unauthorized activity, security incident, or urgent dispute.",
    "inquire": "General product, settings, fees, or how-to question.",
}
POLICY_TOOL = [{
    "type": "function",
    "function": {
        "name": "lookup_intent_policy",
        "description": "Look up the policy definition for one allowed intent label.",
        "parameters": {
            "type": "object",
            "properties": {"intent": {"type": "string", "enum": list(LABELS)}},
            "required": ["intent"],
            "additionalProperties": False,
        },
    },
}]


def parse_intent(text: str) -> str:
    try:
        match = re.search(r"\{.*?\}", text, flags=re.DOTALL)
        intent = json.loads(match.group(0)).get("intent", "") if match else ""
        return intent if intent in LABELS else "PARSE_FAIL"
    except (json.JSONDecodeError, AttributeError, TypeError):
        return "PARSE_FAIL"


def api_request(client: OpenAI, messages: list, **kwargs) -> dict:
    started = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL, messages=messages, max_tokens=180, **kwargs
    )
    latency = time.perf_counter() - started
    usage = response.usage
    return {
        "response": response,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
        "latency": latency,
    }


def run_react(client: OpenAI, query: str) -> dict:
    system = BASE + " First use lookup_intent_policy for the closest label, then classify using its definition."
    first = api_request(
        client,
        [{"role": "system", "content": system}, {"role": "user", "content": query}],
        tools=POLICY_TOOL,
        tool_choice={"type": "function", "function": {"name": "lookup_intent_policy"}},
    )
    assistant_message = first["response"].choices[0].message
    calls = assistant_message.tool_calls or []
    if not calls:
        raise RuntimeError("The ReAct request did not return its required policy tool call.")
    tool_call = calls[0]
    arguments = json.loads(tool_call.function.arguments)
    policy = POLICIES.get(arguments.get("intent"), "Unknown label; choose the best allowed class.")
    second = api_request(
        client,
        [
            {"role": "system", "content": system},
            {"role": "user", "content": query},
            assistant_message.model_dump(exclude_none=True),
            {"role": "tool", "tool_call_id": tool_call.id, "content": policy},
        ],
    )
    text = second["response"].choices[0].message.content or ""
    return {
        "prediction": parse_intent(text),
        "input_tokens": first["input_tokens"] + second["input_tokens"],
        "output_tokens": first["output_tokens"] + second["output_tokens"],
        "latency": first["latency"] + second["latency"],
        "api_calls": 2,
    }


def wilson_ci(hits: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    proportion = hits / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    spread = z * math.sqrt(
        (proportion * (1 - proportion) + z * z / (4 * total)) / total
    ) / denominator
    return centre - spread, centre + spread


def percentile_95(values: list[float]) -> float:
    return sorted(values)[max(0, math.ceil(0.95 * len(values)) - 1)]


def configured_cost(input_tokens: int, output_tokens: int):
    input_rate = os.environ.get("TOGETHER_INPUT_USD_PER_MILLION")
    output_rate = os.environ.get("TOGETHER_OUTPUT_USD_PER_MILLION")
    if not input_rate or not output_rate:
        return None
    return input_tokens * float(input_rate) / 1_000_000 + output_tokens * float(output_rate) / 1_000_000


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    limit = int(os.environ.get("BENCH_LIMIT", str(len(GOLDEN))))
    if limit < 1:
        raise ValueError("BENCH_LIMIT must be a positive integer.")
    cases = GOLDEN[:limit]
    all_results = {}

    for technique, prompt in PROMPTS.items():
        measured = []
        for case in cases:
            call = api_request(
                client,
                [{"role": "system", "content": prompt}, {"role": "user", "content": case["query"]}],
            )
            text = call["response"].choices[0].message.content or ""
            prediction = parse_intent(text)
            measured.append({
                "prediction": prediction,
                "correct": prediction == case["expected"],
                "input_tokens": call["input_tokens"],
                "output_tokens": call["output_tokens"],
                "latency_seconds": call["latency"],
                "api_calls": 1,
            })
        all_results[technique] = measured

    measured_react = []
    for case in cases:
        result = run_react(client, case["query"])
        result["correct"] = result["prediction"] == case["expected"]
        result["latency_seconds"] = result.pop("latency")
        measured_react.append(result)
    all_results["ReAct-2step"] = measured_react

    summaries = {}
    for technique, measured in all_results.items():
        count = len(measured)
        hits = sum(row["correct"] for row in measured)
        low, high = wilson_ci(hits, count)
        costs = [configured_cost(row["input_tokens"], row["output_tokens"]) for row in measured]
        mean_cost = statistics.mean(costs) if all(cost is not None for cost in costs) else None
        summaries[technique] = {
            "n": count,
            "hits": hits,
            "accuracy": hits / count,
            "ci_low": low,
            "ci_high": high,
            "mean_input_tokens": statistics.mean(row["input_tokens"] for row in measured),
            "mean_output_tokens": statistics.mean(row["output_tokens"] for row in measured),
            "mean_cost": mean_cost,
            "p95_latency": percentile_95([row["latency_seconds"] for row in measured]),
        }

    names = list(summaries)
    few = summaries["few-shot-3"]
    cot = summaries["CoT-rationale"]
    ci_overlap = max(few["ci_low"], cot["ci_low"]) <= min(few["ci_high"], cot["ci_high"])
    print(f"{'technique':18s} | accuracy (Wilson 95% CI) | $/query | P95 latency")
    print("-" * 88)
    for technique, summary in summaries.items():
        cost_text = f"${summary['mean_cost']:.6f}" if summary["mean_cost"] is not None else "not configured"
        print(
            f"{technique:18s} | {summary['accuracy']:5.1%} "
            f"[{summary['ci_low']:.1%}, {summary['ci_high']:.1%}] | "
            f"{cost_text:14s} | {summary['p95_latency']:.2f}s"
        )

    output_dir = Path(__file__).resolve().parent
    (output_dir / "bench_results.json").write_text(
        json.dumps({"summary": summaries, "results": all_results}, indent=2),
        encoding="utf-8",
    )
    accuracy_lines = ["| Technique | Correct | Accuracy | Wilson 95% CI |", "|---|---:|---:|---:|"]
    cost_lines = [
        "Rate card: current Together rates supplied by environment variables; prices may drift.",
        "| Technique | $/query | $/1,000 queries | $/100,000 queries/day | P95 latency |",
        "|---|---:|---:|---:|---:|",
    ]
    for technique in names:
        summary = summaries[technique]
        accuracy_lines.append(
            f"| {technique} | {summary['hits']}/{summary['n']} | {summary['accuracy']:.1%} | "
            f"{summary['ci_low']:.1%} to {summary['ci_high']:.1%} |"
        )
        if summary["mean_cost"] is None:
            cost_values = ("not configured", "not configured", "not configured")
        else:
            cost_values = tuple(f"${summary['mean_cost'] * scale:.4f}" for scale in (1, 1_000, 100_000))
        cost_lines.append(
            f"| {technique} | {cost_values[0]} | {cost_values[1]} | {cost_values[2]} | "
            f"{summary['p95_latency']:.2f}s |"
        )

    recommendation = (
        f"Ship few-shot-3 for this re-routeable merchant-intent classification workload, "
        f"provided its measured accuracy ({few['accuracy']:.1%}) meets the product threshold. "
        f"A wrong label is recoverable through routing or human review, so paying for extra "
        f"reasoning is hard to justify unless it materially reduces downstream errors. The "
        f"few-shot Wilson interval is {few['ci_low']:.1%} to {few['ci_high']:.1%}; the "
        f"concise-rationale interval is {cot['ci_low']:.1%} to {cot['ci_high']:.1%}. "
        f"These intervals {'overlap, so the apparent ranking is inconclusive at this sample size' if ci_overlap else 'do not overlap in this run, though a larger held-out evaluation is still warranted'}. "
        f"Use the measured P95 latency and current provider rate card before setting an SLO or budget; "
        f"this script reports costs only when both input and output rates are configured. ReAct uses "
        f"two model requests per query, so its tool round trip can add latency even when the policy "
        f"lookup is local. Treat benchmark results as estimates, not a guarantee of production quality. "
        f"Keep the golden set synthetic, avoid retaining raw customer messages or private reasoning, "
        f"and validate new prompt versions against a separate test set. For high-impact financial "
        f"decisions, route uncertain cases to qualified human review rather than treating a vote or "
        f"model confidence score as authorization. Add retries for malformed output and idempotency "
        f"for any future tool that can change account state."
    )
    (output_dir / "accuracy_table.md").write_text("\n".join(accuracy_lines) + "\n", encoding="utf-8")
    (output_dir / "cost_table.md").write_text("\n".join(cost_lines) + "\n", encoding="utf-8")
    (output_dir / "recommendation.md").write_text(recommendation + "\n", encoding="utf-8")
    print(f"\nWrote benchmark tables and JSON to {output_dir}")
    print("GDPR: do not retain real PII or raw reasoning traces. Operations: handle parse failures and make tools idempotent.")
    print("ReAct makes two model requests per query; on all 50 cases this benchmark uses up to 250 requests.")


if __name__ == "__main__":
    main()

"""
technique          | accuracy (Wilson 95% CI) | $/query | P95 latency
----------------------------------------------------------------------------------------
zero-shot          | 92.0% [81.2%, 96.8%] | not configured | 1.62s
few-shot-3         | 88.0% [76.2%, 94.4%] | not configured | 1.21s
CoT-rationale      | 86.0% [73.8%, 93.0%] | not configured | 2.14s
ReAct-2step        | 90.0% [78.6%, 95.7%] | not configured | 2.03s

Wrote benchmark tables and JSON to C:\Storage\AI Development\GITCHECKOUT\AiReferesh\FDE\1_PROMPT\2_TYPES
GDPR: do not retain real PII or raw reasoning traces. Operations: handle parse failures and make tools idempotent.
ReAct makes two model requests per query; on all 50 cases this benchmark uses up to 250 requests.
"""