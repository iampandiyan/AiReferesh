"""Exercise 3: test the approval router at its boundaries.

Run this file by itself after installing `openai` and `python-dotenv` and
adding TOGETHER_STUDY_API_KEY to a `.env` file. The router is deterministic
and makes no model calls; the Together call in main is a separate explanation step.

Behavior: non-refunds go directly to customer confirmation; refunds of $500
or more require approval; smaller or missing amounts are auto-approved.
Lesson: boundary tests catch off-by-one policy errors. Keep routing pure so a
replay produces the same decision every time.
"""

import os
from pprint import pprint
from typing import TypedDict

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "Explain in one concise sentence why a customer-support refund router "
    "should use deterministic threshold checks."
)
HUMAN_APPROVAL_THRESHOLD_USD = 500.0


class RouteState(TypedDict):
    intent: str
    refund_amount_usd: float | None


def create_client() -> OpenAI:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    return OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")


def route_after_propose(state: RouteState) -> str:
    print("\n--- Router input ---")
    pprint(state)

    if state["intent"] != "refund_request":
        print(
            f"Intent is {state['intent']!r}, not 'refund_request'; "
            "route to customer confirmation."
        )
        return "confirm_to_customer"

    amount = state.get("refund_amount_usd") or 0.0
    print(
        f"Refund amount: {amount}; approval threshold: "
        f"{HUMAN_APPROVAL_THRESHOLD_USD}"
    )
    if amount >= HUMAN_APPROVAL_THRESHOLD_USD:
        print(
            f"{amount} >= {HUMAN_APPROVAL_THRESHOLD_USD}; "
            "human approval is required."
        )
        return "request_human_approval"
    print(
        f"{amount} < {HUMAN_APPROVAL_THRESHOLD_USD}; "
        "refund can be auto-executed."
    )
    return "auto_execute"


def main() -> None:
    cases = {
        0.0: "auto_execute",
        499.99: "auto_execute",
        500.0: "request_human_approval",
        500.01: "request_human_approval",
        None: "auto_execute",
    }
    for amount, expected in cases.items():
        state: RouteState = {
            "intent": "refund_request",
            "refund_amount_usd": amount,
        }
        print(f"\n=== Test refund amount: {amount} ===")
        actual = route_after_propose(state)
        assert actual == expected, f"{amount} -> {actual}, expected {expected}"
        print(f"Expected route: {expected}")
        print(f"Actual route:   {actual}")
        print("Test passed.")

    non_refund_state: RouteState = {
        "intent": "billing_question",
        "refund_amount_usd": 9999.0,
    }
    print("\n=== Test non-refund intent ===")
    non_refund_route = route_after_propose(non_refund_state)
    assert non_refund_route == "confirm_to_customer"
    print("Expected route: confirm_to_customer")
    print(f"Actual route:   {non_refund_route}")
    print("Test passed.")

    print("\n=== Requesting the model's explanation of the threshold ===")
    client = create_client()
    request_messages = [
        {"role": "system", "content": PROMPT_V1},
        {"role": "user", "content": "Why is a fixed $500 approval boundary useful?"},
    ]
    print("Messages sent to the model:")
    pprint(request_messages)
    response = client.chat.completions.create(
        model=MODEL,
        messages=request_messages,
    )
    explanation = response.choices[0].message.content
    if not explanation:
        raise RuntimeError("The model returned an empty explanation.")
    print("Model explanation:", explanation)


if __name__ == "__main__":
    main()

'''

=== Test refund amount: 0.0 ===

--- Router input ---
{'intent': 'refund_request', 'refund_amount_usd': 0.0}
Refund amount: 0.0; approval threshold: 500.0
0.0 < 500.0; refund can be auto-executed.
Expected route: auto_execute
Actual route:   auto_execute
Test passed.

=== Test refund amount: 499.99 ===

--- Router input ---
{'intent': 'refund_request', 'refund_amount_usd': 499.99}
Refund amount: 499.99; approval threshold: 500.0
499.99 < 500.0; refund can be auto-executed.
Expected route: auto_execute
Actual route:   auto_execute
Test passed.

=== Test refund amount: 500.0 ===

--- Router input ---
{'intent': 'refund_request', 'refund_amount_usd': 500.0}
Refund amount: 500.0; approval threshold: 500.0
500.0 >= 500.0; human approval is required.
Expected route: request_human_approval
Actual route:   request_human_approval
Test passed.

=== Test refund amount: 500.01 ===

--- Router input ---
{'intent': 'refund_request', 'refund_amount_usd': 500.01}
Refund amount: 500.01; approval threshold: 500.0
500.01 >= 500.0; human approval is required.
Expected route: request_human_approval
Actual route:   request_human_approval
Test passed.

=== Test refund amount: None ===

--- Router input ---
{'intent': 'refund_request', 'refund_amount_usd': None}
Refund amount: 0.0; approval threshold: 500.0
0.0 < 500.0; refund can be auto-executed.
Expected route: auto_execute
Actual route:   auto_execute
Test passed.

=== Test non-refund intent ===

--- Router input ---
{'intent': 'billing_question', 'refund_amount_usd': 9999.0}
Intent is 'billing_question', not 'refund_request'; route to customer confirmation.
Expected route: confirm_to_customer
Actual route:   confirm_to_customer
Test passed.

=== Requesting the model's explanation of the threshold ===
Messages sent to the model:
[{'content': 'Explain in one concise sentence why a customer-support refund '
             'router should use deterministic threshold checks.',
  'role': 'system'},
 {'content': 'Why is a fixed $500 approval boundary useful?', 'role': 'user'}]
Model explanation: A fixed $500 approval boundary provides a clear, objective rule that lets the system instantly route small refunds to automated approval while flagging larger ones for manual review, minimizing ambiguity, speeding decisions, and ensuring consistent risk control.
'''