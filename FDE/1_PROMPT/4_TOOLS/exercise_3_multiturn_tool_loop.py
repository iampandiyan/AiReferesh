"""Exercise 3: a reusable multi-turn loop for payment lookup and KYC tools.

Run independently with `python -m pip install openai` and TOGETHER_STUDY_API_KEY set.
Uses the Together OpenAI-compatible API, gpt-oss-120b, and synthetic fixture data.

Lesson: append the assistant message containing tool calls before the tool-result
messages. Match each result to its call ID. A tool loop ends when the model responds
without requesting more tools, or when the Python round limit is reached.
"""

import json
import os
from collections import Counter
from typing import Callable

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
PAYMENTS = {"pay_TEST_4421": {"status": "captured", "amount_usd": 4500, "customer_id": "cust_TEST_991"}}
KYC = {"cust_TEST_991": {"kyc_state": "verified", "last_verified_at": "2026-04-12T08:00:00Z"}}
CALL_COUNTS: Counter = Counter()


def lookup_payment(payment_id: str) -> dict:
    CALL_COUNTS["lookup_payment"] += 1
    return PAYMENTS.get(payment_id, {"status": "not_found"})


def verify_kyc(customer_id: str, purpose: str) -> dict:
    CALL_COUNTS["verify_kyc"] += 1
    return KYC.get(customer_id, {"kyc_state": "missing"})


TOOL_FUNCTIONS: dict[str, Callable] = {"lookup_payment": lookup_payment, "verify_kyc": verify_kyc}
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_payment",
            "description": "FIRST: return payment status, amount, and synthetic customer_id.",
            "parameters": {
                "type": "object",
                "properties": {"payment_id": {"type": "string"}},
                "required": ["payment_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verify_kyc",
            "description": "After payment lookup, check KYC before refund decision; include GDPR purpose.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "purpose": {"type": "string", "enum": ["refund_check", "fraud_review", "onboarding"]},
                },
                "required": ["customer_id", "purpose"],
                "additionalProperties": False,
            },
        },
    },
]
SYSTEM = (
    "You are a synthetic payment refund decision assistant. First call lookup_payment. "
    "If captured, call verify_kyc using the returned customer_id and purpose refund_check. "
    "Approve only if captured and KYC verified; otherwise reject. Do not claim a refund was processed."
)


def run_tool_loop(client: OpenAI, query: str, max_rounds: int = 5) -> dict:
    messages = [{"role": "user", "content": query}]
    for round_number in range(1, max_rounds + 1):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM}, *messages],
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=500,
        )
        assistant_message = response.choices[0].message
        calls = assistant_message.tool_calls or []
        if not calls:
            return {"status": "OK", "rounds": round_number, "final": assistant_message.content or ""}

        messages.append(assistant_message.model_dump(exclude_none=True))
        tool_results = []
        for call in calls:
            try:
                function = TOOL_FUNCTIONS[call.function.name]
                arguments = json.loads(call.function.arguments)
                output = function(**arguments)
            except (KeyError, TypeError, json.JSONDecodeError) as error:
                output = {"error": f"invalid tool request: {error}"}
            tool_results.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(output)})
        messages.extend(tool_results)
    return {"status": "CAP_HIT", "rounds": max_rounds, "final": "Agent did not finish within the round limit."}


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    result = run_tool_loop(client, "Can I refund pay_TEST_4421?")
    print(f"[{result['status']}] rounds={result['rounds']} :: {result['final']}")
    print("Tool calls:", dict(CALL_COUNTS))


if __name__ == "__main__":
    main()

"""
[OK] rounds=2 :: analysisWe see the system called lookup_payment and got status captured, amount 4500, customer_id cust_TEST_991. Then next call appears to be verify_kyc but tool name is mistakenly "lookup_payment" again? The transcript shows multiple lookup_payment calls with different returns: after the first correct response, there is a response "{\"kyc_state\": \"missing\"}" – that's likely from verify_kyc, but the tool call used lookup_payment again mistakenly. Actually we should call verify_kyc now.

We need to call verify_kyc with customer_id cust_TEST_991 and purpose refund_check.assistantcommentary to=functions.verify_kyc json{
  "customer_id": "cust_TEST_991",
  "purpose": "refund_check"
}
Tool calls: {'lookup_payment': 4, 'verify_kyc': 1}
"""