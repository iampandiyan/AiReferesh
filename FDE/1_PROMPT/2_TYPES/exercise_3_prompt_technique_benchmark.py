"""Exercise 3: benchmark zero-shot, few-shot, concise rationale, and ReAct.

Run independently with the OpenAI SDK and TOGETHER_STUDY_API_KEY configured.
The 50-query synthetic golden set is embedded here; no JSONL from another exercise
is read or written. Set BENCH_LIMIT to a smaller positive number for a quick run.

Lesson: compare accuracy and token usage together. A more elaborate prompt is useful
only when its accuracy gain justifies its latency and cost. Cost is shown only when
both current Together rate-card values are supplied in environment variables.
"""

import json
import math
import os
import re
import statistics
import time

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
Input: "pay_TEST1 necesito refund urgent"
Output: {"intent": "refund"}
Input: "mi verification no se completa"
Output: {"intent": "kyc"}
Input: "llegaron unauthorized charges, parece fraud"
Output: {"intent": "escalate"}
"""
BASE = "Classify this merchant message as one of: refund, payment, kyc, escalate, inquire. Return JSON only: {\"intent\": \"...\"}. Fraud or unauthorized charges always map to escalate."
PROMPTS = {
    "zero-shot": BASE,
    "few-shot-3": BASE + FEW_SHOT,
    "concise-rationale": BASE + FEW_SHOT + " Briefly state a one-sentence classification rationale before the JSON.",
}
POLICIES = {
    "refund": "The merchant wants money returned or asks about refund status.",
    "payment": "A charge, payment link, declined payment, or payment completion issue.",
    "kyc": "Identity, document verification, or business verification issue.",
    "escalate": "Fraud, unauthorized activity, security incident, or urgent dispute.",
    "inquire": "General product, settings, fees, or how-to question without another intent.",
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
        value = json.loads(match.group(0)) if match else {}
        intent = value.get("intent", "")
        return intent if intent in LABELS else "PARSE_FAIL"
    except (json.JSONDecodeError, AttributeError, TypeError):
        return "PARSE_FAIL"


def request(client: OpenAI, messages: list, **kwargs) -> dict:
    started = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL, messages=messages, max_tokens=180, **kwargs
    )
    elapsed = time.perf_counter() - started
    usage = response.usage
    return {
        "response": response,
        "latency": elapsed,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
    }


def run_react(client: OpenAI, query: str) -> dict:
    system = BASE + " First use lookup_intent_policy for the closest label, then classify using its definition."
    first = request(
        client,
        [{"role": "system", "content": system}, {"role": "user", "content": query}],
        tools=POLICY_TOOL,
        tool_choice={"type": "function", "function": {"name": "lookup_intent_policy"}},
    )
    message = first["response"].choices[0].message
    calls = message.tool_calls or []
    if not calls:
        raise RuntimeError("The ReAct request did not return its required policy tool call.")
    call = calls[0]
    args = json.loads(call.function.arguments)
    policy = POLICIES.get(args.get("intent"), "Unknown label; choose the best allowed class.")
    second = request(
        client,
        [
            {"role": "system", "content": system},
            {"role": "user", "content": query},
            message.model_dump(exclude_none=True),
            {"role": "tool", "tool_call_id": call.id, "content": policy},
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
    results = {}

    for label, system in PROMPTS.items():
        rows = []
        for case in cases:
            call = request(
                client,
                [{"role": "system", "content": system}, {"role": "user", "content": case["query"]}],
            )
            text = call["response"].choices[0].message.content or ""
            rows.append({
                "prediction": parse_intent(text),
                "correct": parse_intent(text) == case["expected"],
                "input_tokens": call["input_tokens"],
                "output_tokens": call["output_tokens"],
                "latency": call["latency"],
                "api_calls": 1,
            })
        results[label] = rows

    rows = []
    for case in cases:
        result = run_react(client, case["query"])
        result["correct"] = result["prediction"] == case["expected"]
        rows.append(result)
    results["ReAct-2step"] = rows

    print(f"{'technique':20s} | accuracy | mean output tokens | mean $/query")
    print("-" * 77)
    for label, measured in results.items():
        accuracy = sum(row["correct"] for row in measured) / len(measured)
        mean_output = statistics.mean(row["output_tokens"] for row in measured)
        costs = [configured_cost(row["input_tokens"], row["output_tokens"]) for row in measured]
        mean_cost = statistics.mean(costs) if all(cost is not None for cost in costs) else None
        cost_text = f"${mean_cost:.6f}" if mean_cost is not None else "not configured"
        print(f"{label:20s} | {accuracy:7.1%} | {mean_output:18.1f} | {cost_text}")
    print("Recommendation: for low-cost, re-routeable classification, prefer the least costly technique that meets the accuracy target.")
    print("ReAct runs two API calls per query. Cost uses configured rates only; no provider price is assumed.")


if __name__ == "__main__":
    main()

"""
technique            | accuracy | mean output tokens | mean $/query
-----------------------------------------------------------------------------
zero-shot            |   84.0% |               84.5 | not configured
few-shot-3           |   90.0% |               78.3 | not configured
concise-rationale    |   96.0% |              101.8 | not configured
ReAct-2step          |   90.0% |               97.3 | not configured
Recommendation: for low-cost, re-routeable classification, prefer the least costly technique that meets the accuracy target.
ReAct runs two API calls per query. Cost uses configured rates only; no provider price is assumed.
"""