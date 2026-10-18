"""Exercise 3: support-ticket triage with three recoverable tools.

Run independently after installing `openai` and setting TOGETHER_STUDY_API_KEY.
All customers, orders, and escalation IDs are synthetic and in memory.

Behavior: tool errors are returned as values so the model can recover. The
account-compromise sample should call escalate_to_human. The loop is capped at
eight model turns.
Lesson: inspect the final response, not an intermediate tool error; a useful
tool error can guide recovery without aborting the conversation.
"""

import json
import os

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "You are AcmeCorp's frontline support agent. Use customer and order tools "
    "before answering when relevant. Read error values and recover if possible. "
    "Escalate suspected account compromise to a human."
)
CUSTOMERS = {
    "c_4823": {"tier": "pro", "name": "Mei Lin"},
    "c_1001": {"tier": "free", "name": "Alex Roy"},
    "c_9999": {"tier": "enterprise", "name": "AcmeCorp Lead"},
}
ORDERS = {
    "4823": {
        "order_id": "4823",
        "customer_id": "c_4823",
        "amount_usd": 129.0,
        "invoice_status": "pending",
    },
    "5511": {
        "order_id": "5511",
        "customer_id": "c_1001",
        "amount_usd": 29.0,
        "invoice_status": "issued",
    },
}
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_customer_tier",
            "description": "Look up a customer's plan tier.",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up an order by its ID.",
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
            "name": "escalate_to_human",
            "description": "Escalate account compromise or a serious unresolved issue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "customer_id": {"type": "string"},
                },
                "required": ["reason", "customer_id"],
                "additionalProperties": False,
            },
        },
    },
]


def get_customer_tier(customer_id: str) -> dict:
    customer = CUSTOMERS.get(customer_id)
    return {"tier": customer["tier"]} if customer else {
        "error": f"No customer {customer_id!r}."
    }


def lookup_order(order_id: str) -> dict:
    return ORDERS.get(order_id, {"error": f"No order {order_id!r}."})


def escalate_to_human(reason: str, customer_id: str) -> dict:
    return {"case_id": "ESC-9201", "reason": reason, "customer_id": customer_id}


def execute_tool(name: str, arguments: dict) -> dict:
    try:
        if name == "get_customer_tier":
            return get_customer_tier(arguments["customer_id"])
        if name == "lookup_order":
            return lookup_order(arguments["order_id"])
        if name == "escalate_to_human":
            return escalate_to_human(arguments["reason"], arguments["customer_id"])
        return {"error": f"Unsupported tool {name!r}."}
    except (KeyError, TypeError) as error:
        return {"error": f"Invalid arguments for {name}: {error}"}


def run_ticket(client: OpenAI, customer_message: str) -> str:
    messages = [
        {"role": "system", "content": PROMPT_V1},
        {"role": "user", "content": customer_message},
    ]
    for _ in range(8):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=700,
        )
        assistant_message = response.choices[0].message
        calls = assistant_message.tool_calls or []
        if not calls:
            return assistant_message.content or "No response returned."
        messages.append(assistant_message.model_dump(exclude_none=True))
        for call in calls:
            try:
                arguments = json.loads(call.function.arguments)
            except json.JSONDecodeError as error:
                result = {"error": f"Invalid JSON arguments: {error}"}
            else:
                result = execute_tool(call.function.name, arguments)
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
            )
    raise RuntimeError("The triage run exceeded its eight-turn limit.")


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    sample_tickets = [
        "I'm on Pro plan, my invoice is missing. Order #4823.",
        "How do I upgrade? I am on the free plan, customer id c_1001.",
        "Where is my order? The number is 5511.",
        "I think account c_9999 is compromised; someone changed my email.",
    ]
    for index, customer_message in enumerate(sample_tickets, 1):
        print(f"[ticket {index}] {run_ticket(client, customer_message)}")


if __name__ == "__main__":
    main()
