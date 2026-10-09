"""Exercise 5: a five-tool refund agent with Python-enforced safety checks.

Run independently with `python -m pip install openai` and TOGETHER_STUDY_API_KEY set.
All IDs and financial data are synthetic. Refunds modify only an in-memory demo ledger.

Lesson: prompts describe intended tool behavior, but Python must enforce authorization
preconditions, iteration limits, deterministic idempotency, and fallback escalation.
Read-only prerequisites can run in parallel after payment lookup. Never ship an agent
that can move real money without durable controls, review, and monitoring.
"""

import asyncio
import hashlib
import json
import os

from openai import AsyncOpenAI


MODEL = "openai/gpt-oss-120b"
MAX_ROUNDS = 5
PAYMENTS = {
    "pay_TEST_OK": {"status": "captured", "amount_usd": 4500, "customer_id": "cust_TEST_OK", "captured_at": "2026-05-10"},
    "pay_TEST_OLD": {"status": "captured", "amount_usd": 1200, "customer_id": "cust_TEST_OK", "captured_at": "2025-01-01"},
    "pay_TEST_NOKY": {"status": "captured", "amount_usd": 900, "customer_id": "cust_TEST_NOKY", "captured_at": "2026-05-12"},
}
KYC = {"cust_TEST_OK": {"kyc_state": "verified"}, "cust_TEST_NOKY": {"kyc_state": "missing"}}
REFUND_LEDGER: dict[str, dict] = {}
PAYMENT_REFUNDS: set[str] = set()


def idempotency_key(payment_id: str, reason: str) -> str:
    return hashlib.sha256(f"{payment_id}{reason}".encode("utf-8")).hexdigest()[:16]


def lookup_payment(payment_id: str) -> dict:
    return PAYMENTS.get(payment_id, {"status": "not_found"})


def check_refund_window(payment_id: str) -> dict:
    payment = PAYMENTS.get(payment_id)
    if not payment:
        return {"within_window": False}
    return {"within_window": payment["captured_at"] >= "2026-02-20"}


def verify_kyc(customer_id: str, purpose: str) -> dict:
    return KYC.get(customer_id, {"kyc_state": "missing"})


def process_refund(payment_id: str, amount_usd: int, reason: str, dry_run: bool) -> dict:
    payment = PAYMENTS.get(payment_id)
    if not payment or payment.get("status") != "captured":
        return {"status": "rejected", "reason": "payment is not captured"}
    if payment["captured_at"] < "2026-02-20":
        return {"status": "rejected", "reason": "refund window expired"}
    if KYC.get(payment["customer_id"], {}).get("kyc_state") != "verified":
        return {"status": "rejected", "reason": "KYC is not verified"}
    key = idempotency_key(payment_id, reason)
    if key in REFUND_LEDGER:
        return REFUND_LEDGER[key]
    if payment_id in PAYMENT_REFUNDS:
        return {"status": "rejected", "reason": "payment already refunded"}
    result = {"refund_id": f"rfnd_TEST_{key[:8]}", "status": "DRY_RUN" if dry_run else "processed", "amount_usd": amount_usd}
    if not dry_run:
        REFUND_LEDGER[key] = result
        PAYMENT_REFUNDS.add(payment_id)
    return result


def escalate_to_human(reason: str) -> dict:
    digest = hashlib.sha256(reason.encode("utf-8")).hexdigest()[:8].upper()
    return {"ticket_id": f"ST-REF-{digest}", "status": "open"}


TOOL_HANDLERS = {
    "lookup_payment": lookup_payment,
    "check_refund_window": check_refund_window,
    "verify_kyc": verify_kyc,
    "process_refund": process_refund,
    "escalate_to_human": escalate_to_human,
}


def description(when: str, when_not: str, prerequisites: str, side_effects: str) -> str:
    return f"WHEN: {when}\nWHEN NOT: {when_not}\nPRE-REQS: {prerequisites}\nSIDE EFFECTS: {side_effects}"


def function_tool(name: str, desc: str, properties: dict, required: list[str]) -> dict:
    return {"type": "function", "function": {"name": name, "description": desc, "parameters": {
        "type": "object", "properties": properties, "required": required, "additionalProperties": False,
    }}}


TOOLS = [
    function_tool("lookup_payment", description("FIRST; identify payment and customer.", "Never skip.", "payment_id.", "Read-only."), {"payment_id": {"type": "string"}}, ["payment_id"]),
    function_tool("check_refund_window", description("After captured payment lookup.", "If payment is not captured.", "payment_id.", "Read-only; independent of KYC check."), {"payment_id": {"type": "string"}}, ["payment_id"]),
    function_tool("verify_kyc", description("After payment lookup; before refund decision.", "If already checked this session.", "customer_id and GDPR purpose.", "Read-only; independent of refund-window check."), {"customer_id": {"type": "string"}, "purpose": {"type": "string", "enum": ["refund_check", "fraud_review", "onboarding"]}}, ["customer_id", "purpose"]),
    function_tool("process_refund", description("Only when payment is captured, window is open, and KYC is verified.", "Any prerequisite failed or payment already refunded.", "All prerequisite reads pass.", "Mutates synthetic ledger; Python enforces eligibility and idempotency."), {"payment_id": {"type": "string"}, "amount_usd": {"type": "integer"}, "reason": {"type": "string"}, "dry_run": {"type": "boolean"}}, ["payment_id", "amount_usd", "reason", "dry_run"]),
    function_tool("escalate_to_human", description("When payment, window, KYC, or tool checks fail.", "After a successful refund.", "Short reason.", "Creates a synthetic review ticket."), {"reason": {"type": "string"}}, ["reason"]),
]
SYSTEM = """Handle a refund request using tools. First look up payment. If captured, check the window and KYC (these reads are independent and may be called together). Process a refund only if both pass. Otherwise escalate. Never claim processing before process_refund succeeds. Keep the reason stable across retries."""


async def run_agent(client: AsyncOpenAI, query: str, dry_run: bool = False, max_rounds: int = MAX_ROUNDS) -> dict:
    messages = [{"role": "user", "content": query}]
    for round_number in range(1, max_rounds + 1):
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM}, *messages],
            tools=TOOLS,
            tool_choice="auto",
            parallel_tool_calls=True,
            max_tokens=700,
        )
        assistant_message = response.choices[0].message
        calls = assistant_message.tool_calls or []
        if not calls:
            return {"status": "OK", "rounds": round_number, "final": assistant_message.content or ""}

        messages.append(assistant_message.model_dump(exclude_none=True))
        outputs = []
        for call in calls:
            try:
                arguments = json.loads(call.function.arguments)
                if call.function.name == "verify_kyc":
                    payment_result = next((json.loads(item["content"]) for item in reversed(messages) if item.get("role") == "tool" and "customer_id" in item["content"]), None)
                    if not arguments.get("customer_id") and payment_result:
                        arguments["customer_id"] = payment_result.get("customer_id")
                    arguments.setdefault("purpose", "refund_check")
                if call.function.name == "process_refund":
                    arguments["dry_run"] = dry_run
                output = TOOL_HANDLERS[call.function.name](**arguments)
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                output = {"error": f"tool request rejected: {error}"}
            outputs.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(output)})
        messages.extend(outputs)

    fallback = escalate_to_human(f"iteration cap reached: {query[:60]}")
    return {"status": "CAP_HIT", "rounds": max_rounds, "final": f"ESCALATED {fallback['ticket_id']}"}


async def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = AsyncOpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    scenarios = [
        "Refund pay_TEST_OK amount $4500 because merchant requested money back.",
        "Refund pay_TEST_OLD amount $1200 because merchant requested money back.",
        "Refund pay_TEST_NOKY amount $900 because merchant requested money back.",
    ]
    for scenario in scenarios:
        result = await run_agent(client, scenario)
        print(f"[{result['status']:7s}] rounds={result['rounds']} :: {result['final'][:120]}")

    original_ledger_count = len(REFUND_LEDGER)
    dry_result = process_refund("pay_TEST_OK", 4500, "UAT check", dry_run=True)
    assert dry_result["status"] == "DRY_RUN" and len(REFUND_LEDGER) == original_ledger_count
    PAYMENTS["pay_TEST_IDEMPOTENCY"] = {
        "status": "captured", "amount_usd": 50, "customer_id": "cust_TEST_IDEMPOTENCY", "captured_at": "2026-05-10"
    }
    KYC["cust_TEST_IDEMPOTENCY"] = {"kyc_state": "verified"}
    first_refund = process_refund("pay_TEST_IDEMPOTENCY", 50, "repeatable demo", dry_run=False)
    ledger_size = len(REFUND_LEDGER)
    replay_refund = process_refund("pay_TEST_IDEMPOTENCY", 50, "repeatable demo", dry_run=False)
    assert first_refund == replay_refund and len(REFUND_LEDGER) == ledger_size
    cap = await run_agent(client, "Forced cap fallback test", max_rounds=0)
    assert cap["status"] == "CAP_HIT"
    print("Dry-run:", dry_result)
    print("Idempotent replay preserved ledger size:", ledger_size == len(REFUND_LEDGER))
    print("Cap test:", cap["final"])
    print("Ledger entries:", len(REFUND_LEDGER))
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
"""
[OK     ] rounds=2 :: analysisIt seems the tool didn't return check_refund_window and verify_kyc yet. I need to call check_refund_window for p
[OK     ] rounds=2 :: analysisThe tool calls are wrong: The developer says we must first lookup_payment, then check_refund_window and verify_k
[OK     ] rounds=2 :: analysisThe user wants a refund. We need to follow steps:

1. Lookup payment (done). Returns status captured, amount 900
Dry-run: {'refund_id': 'rfnd_TEST_07735897', 'status': 'DRY_RUN', 'amount_usd': 4500}
Idempotent replay preserved ledger size: True
Cap test: ESCALATED ST-REF-9DCE19E5
Ledger entries: 1

"""