"""Exercise 5: a bounded ReAct refund agent with two local tools.

Run independently with the OpenAI SDK and TOGETHER_STUDY_API_KEY configured.
Balances are deterministic synthetic fixtures; this does not access payment systems.

Lesson: tools should have narrow contracts, side effects should be controlled, and every
agent loop needs a hard iteration cap plus a deterministic fallback. In production, add
authorization, idempotency, audit logging, and human review before any real refund action.
"""

import hashlib
import json
import os
import re

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
MAX_ITERATIONS = 5
BALANCES = {"merch_RZP_42": 3400, "merch_RZP_99": 12000, "merch_RZP_BUG": 0}
SYSTEM = """You are a refund triage agent. Use the tools, not guessed balances.
1. Call lookup_balance once for the merchant.
2. If balance is at least the requested refund amount, answer APPROVE.
3. Otherwise call escalate_to_human, then answer ESCALATED with its ticket id.
Never claim a refund was issued. Return a concise final status.
"""
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_balance",
            "description": "Look up the synthetic settled balance for a merchant.",
            "parameters": {
                "type": "object",
                "properties": {"merchant_id": {"type": "string"}},
                "required": ["merchant_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Create a deterministic synthetic review ticket.",
            "parameters": {
                "type": "object",
                "properties": {"reason": {"type": "string"}},
                "required": ["reason"],
                "additionalProperties": False,
            },
        },
    },
]


def lookup_balance(merchant_id: str) -> int:
    return BALANCES.get(merchant_id, -1)


def escalate_to_human(reason: str) -> str:
    digest = hashlib.sha256(reason.encode("utf-8")).hexdigest()[:8].upper()
    return f"TICKET-{digest}"


def run_react(client: OpenAI, query: str, max_iterations: int = MAX_ITERATIONS) -> dict:
    messages = [{"role": "user", "content": query}]
    tool_names = []
    for iteration in range(max_iterations):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM}, *messages],
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=300,
        )
        message = response.choices[0].message
        calls = message.tool_calls or []
        if not calls:
            return {
                "status": "OK",
                "iterations": iteration + 1,
                "tools": tool_names,
                "final": message.content or "No final response returned.",
            }

        messages.append(message.model_dump(exclude_none=True))
        for call in calls:
            try:
                arguments = json.loads(call.function.arguments)
                if call.function.name == "lookup_balance":
                    output = lookup_balance(arguments["merchant_id"])
                    tool_names.append("lookup_balance")
                elif call.function.name == "escalate_to_human":
                    output = escalate_to_human(arguments["reason"])
                    tool_names.append("escalate_to_human")
                else:
                    output = "ERROR: unsupported tool"
            except (json.JSONDecodeError, KeyError, TypeError) as error:
                output = f"ERROR: invalid tool arguments ({error})"
            messages.append({"role": "tool", "tool_call_id": call.id, "content": str(output)})

    ticket = escalate_to_human(f"iteration cap reached: {query[:80]}")
    return {
        "status": "CAP_HIT",
        "iterations": max_iterations,
        "tools": tool_names,
        "final": f"ESCALATED {ticket}",
    }


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")

    scenarios = [
        "Refund $2,000 for merch_RZP_99; sufficient-balance case.",
        "Refund $5,000 for merch_RZP_42; insufficient-balance case.",
        "Refund $1,000 for merch_RZP_BUG; zero-balance edge case.",
    ]
    for scenario in scenarios:
        result = run_react(client, scenario)
        print(
            f"[{result['status']:7s}] iterations={result['iterations']} "
            f"tools={result['tools']} :: {result['final'][:100]}"
        )

    # Exercise the cap fallback without spending another API call.
    cap_result = run_react(client, "Synthetic forced cap demonstration", max_iterations=0)
    assert cap_result["status"] == "CAP_HIT"
    print(f"[CAP TEST] {cap_result['final']}")
    print("Operational note: monitor iteration counts; repeated cap hits need investigation.")


if __name__ == "__main__":
    main()

"""
[OK     ] iterations=2 tools=['lookup_balance'] :: analysisBalance 12000 > 2000, approve.assistantfinalAPPROVE
[OK     ] iterations=2 tools=['lookup_balance', 'escalate_to_human'] :: analysisWe need to call lookup_balance correctly. The tool expects JSON with merchant_id string. The
[OK     ] iterations=2 tools=['lookup_balance', 'lookup_balance', 'lookup_balance', 'lookup_balance', 'lookup_balance'] :: analysisWe have multiple calls. The system probably only needs one call. The result is "0". Balance
[CAP TEST] ESCALATED TICKET-9121648D
Operational note: monitor iteration counts; repeated cap hits need investigation.
"""