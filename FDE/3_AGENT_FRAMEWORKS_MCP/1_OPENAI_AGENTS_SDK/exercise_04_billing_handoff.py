"""Exercise 4: sequential handoff from triage to a billing specialist.

Run independently after installing `openai` and setting TOGETHER_STUDY_API_KEY.
The fake order and refund records are synthetic; no payment is issued.

Behavior: triage explicitly requests a handoff for billing, then the Python
orchestrator starts a separate billing conversation and runs its tools in order.
The printed parent/child labels make the nesting visible in this local example.
Lesson: handoff is sequential delegation in one application flow, not concurrent
collaboration. The Together Chat Completions API does not provide Agents SDK
trace spans, so this script labels the local execution rather than claiming a
provider trace was created.
"""

import json
import os

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "You are AcmeCorp's triage agent. If the user asks about a refund, invoice, "
    "or billing, call handoff_to_billing with the original request. Otherwise "
    "answer directly."
)
ORDERS = {
    "4823": {"order_id": "4823", "customer_id": "c_4823", "amount_usd": 129.0}
}
HANDOFF_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "handoff_to_billing",
            "description": "Delegate a billing or refund request to the billing specialist.",
            "parameters": {
                "type": "object",
                "properties": {"request": {"type": "string"}},
                "required": ["request"],
                "additionalProperties": False,
            },
        },
    }
]
BILLING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Confirm an order before a refund.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "issue_refund",
            "description": "Record a synthetic refund after confirming the order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "amount": {"type": "number"},
                },
                "required": ["order_id", "amount"],
                "additionalProperties": False,
            },
        },
    },
]


def execute_billing_tool(
    name: str, arguments: dict, confirmed_order_id: str | None
) -> dict:
    try:
        if name == "lookup_order":
            order = ORDERS.get(arguments["order_id"])
            return order or {"error": f"No order {arguments['order_id']!r}."}
        if name == "issue_refund":
            order_id = arguments["order_id"]
            amount = float(arguments["amount"])
            order = ORDERS.get(order_id)
            if order_id != confirmed_order_id:
                return {"error": "The order must be looked up successfully before refunding."}
            if not order:
                return {"error": f"Cannot refund unknown order {order_id!r}."}
            if amount <= 0 or amount > order["amount_usd"]:
                return {"error": "Refund amount must be positive and no greater than the order amount."}
            return {"refund_id": f"REF-{order_id}-{int(amount * 100)}", "amount_usd": amount}
        return {"error": f"Unsupported billing tool {name!r}."}
    except (KeyError, TypeError, ValueError) as error:
        return {"error": f"Invalid arguments for {name}: {error}"}


def run_billing_agent(client: OpenAI, request: str) -> str:
    print("  [nested billing_agent.run]")
    confirmed_order_id = None
    messages = [
        {
            "role": "system",
            "content": (
                "You are AcmeCorp's billing specialist. Always call lookup_order "
                "before issue_refund. Do not refund more than the confirmed order amount."
            ),
        },
        {"role": "user", "content": request},
    ]
    for _ in range(6):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=BILLING_TOOLS if confirmed_order_id else BILLING_TOOLS[:1],
            tool_choice="auto",
            max_tokens=500,
        )
        assistant_message = response.choices[0].message
        calls = assistant_message.tool_calls or []
        if not calls:
            return assistant_message.content or "No billing response returned."
        messages.append(assistant_message.model_dump(exclude_none=True))
        for call in calls:
            try:
                arguments = json.loads(call.function.arguments)
                result = execute_billing_tool(
                    call.function.name, arguments, confirmed_order_id
                )
                if call.function.name == "lookup_order" and "error" not in result:
                    confirmed_order_id = result["order_id"]
            except json.JSONDecodeError as error:
                result = {"error": f"Invalid JSON arguments: {error}"}
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
            )
    raise RuntimeError("The billing run exceeded its six-turn limit.")


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    customer_message = "Please refund order #4823 for $129."
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PROMPT_V1},
            {"role": "user", "content": customer_message},
        ],
        tools=HANDOFF_TOOL,
        tool_choice="auto",
        max_tokens=400,
    )
    assistant_message = response.choices[0].message
    calls = assistant_message.tool_calls or []
    handoff = next(
        (call for call in calls if call.function.name == "handoff_to_billing"),
        None,
    )
    if handoff is None:
        if calls:
            raise RuntimeError(f"Unexpected triage tool call: {calls[0].function.name}")
        print(f"[triage_agent.run] {assistant_message.content or 'No response returned.'}")
        return

    arguments = json.loads(handoff.function.arguments)
    print("[parent triage_agent.run] handing off sequentially")
    print(run_billing_agent(client, arguments["request"]))


if __name__ == "__main__":
    main()
