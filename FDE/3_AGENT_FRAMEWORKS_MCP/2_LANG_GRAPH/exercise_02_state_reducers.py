"""Exercise 2: choose an update rule for every state field.

Run this file by itself after installing `openai` and `python-dotenv` and
adding TOGETHER_STUDY_API_KEY to a `.env` file. This uses a small local
state-update function instead of depending on another exercise or a graph framework.

Behavior: messages append, while customer and workflow scalar fields overwrite
only when a node returns a new value.
Lesson: define reducer behavior deliberately. Appending conversation history
and overwriting a current intent are different operations.
"""

import os
from pprint import pprint
from typing import Literal, TypedDict

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "You are AcmeCorp support. Give a brief acknowledgement of the customer's "
    "support request, without making promises about refunds or approvals."
)


class EscalationState(TypedDict):
    messages: list[dict[str, str]]  # append reducer
    customer_id: str  # overwrite reducer
    customer_tier: Literal["free", "pro", "enterprise", "unknown"]  # overwrite reducer
    intent: Literal["refund_request", "billing_question", "feature_help", "unknown"]  # overwrite
    refund_amount_usd: float | None  # overwrite reducer
    approval_status: Literal["pending", "approved", "rejected"] | None  # overwrite reducer


class EscalationUpdate(TypedDict, total=False):
    messages: list[dict[str, str]]
    customer_id: str
    customer_tier: Literal["free", "pro", "enterprise", "unknown"]
    intent: Literal["refund_request", "billing_question", "feature_help", "unknown"]
    refund_amount_usd: float | None
    approval_status: Literal["pending", "approved", "rejected"] | None


def create_client() -> OpenAI:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    return OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")


def apply_update(state: EscalationState, update: EscalationUpdate) -> EscalationState:
    print("\n--- State before update ---")
    pprint(state)
    print("--- Incoming update ---")
    pprint(update)

    result: EscalationState = {
        "messages": list(state["messages"]),
        "customer_id": state["customer_id"],
        "customer_tier": state["customer_tier"],
        "intent": state["intent"],
        "refund_amount_usd": state["refund_amount_usd"],
        "approval_status": state["approval_status"],
    }
    if "messages" in update:
        result["messages"] = [*result["messages"], *update["messages"]]
    if "customer_id" in update:
        result["customer_id"] = update["customer_id"]
    if "customer_tier" in update:
        result["customer_tier"] = update["customer_tier"]
    if "intent" in update:
        result["intent"] = update["intent"]
    if "refund_amount_usd" in update:
        result["refund_amount_usd"] = update["refund_amount_usd"]
    if "approval_status" in update:
        result["approval_status"] = update["approval_status"]
    print("--- State after applying update ---")
    pprint(result)
    return result


def first_node(state: EscalationState) -> EscalationUpdate:
    update: EscalationUpdate = {
        "messages": [
            {
                "role": "assistant",
                "content": f"I have your request, {state['customer_id']}.",
            }
        ],
        "intent": "refund_request",
    }
    print("\n--- first_node update ---")
    pprint(update)
    return update


def second_node(client: OpenAI, state: EscalationState) -> EscalationUpdate:
    request_messages = [
        {"role": "system", "content": PROMPT_V1},
        *state["messages"],
    ]
    print("\n--- Messages sent to the model ---")
    pprint(request_messages)

    response = client.chat.completions.create(
        model=MODEL,
        messages=request_messages,
    )
    reply = response.choices[0].message.content
    if not reply:
        raise RuntimeError("The model returned an empty reply.")
    update: EscalationUpdate = {"messages": [{"role": "assistant", "content": reply}]}
    print("--- second_node update ---")
    pprint(update)
    return update


def main() -> None:
    client = create_client()
    state: EscalationState = {
        "messages": [{"role": "user", "content": "Please review my refund request."}],
        "customer_id": "C-1",
        "customer_tier": "unknown",
        "intent": "unknown",
        "refund_amount_usd": None,
        "approval_status": None,
    }
    print("--- Initial state ---")
    pprint(state)

    print("\n=== Apply first_node (messages append, intent overwrites) ===")
    state = apply_update(state, first_node(state))

    print("\n=== Apply second_node (assistant reply appends) ===")
    state = apply_update(state, second_node(client, state))

    print("\n=== Final state ===")
    pprint(state)
    assert len(state["messages"]) == 3
    assert state["intent"] == "refund_request"
    print("Message count:", len(state["messages"]))
    print("Current intent:", state["intent"])
    print("Latest reply:", state["messages"][-1]["content"])


if __name__ == "__main__":
    main()

'''
--- Initial state ---
{'approval_status': None,
 'customer_id': 'C-1',
 'customer_tier': 'unknown',
 'intent': 'unknown',
 'messages': [{'content': 'Please review my refund request.', 'role': 'user'}],
 'refund_amount_usd': None}

=== Apply first_node (messages append, intent overwrites) ===

--- first_node update ---
{'intent': 'refund_request',
 'messages': [{'content': 'I have your request, C-1.', 'role': 'assistant'}]}

--- State before update ---
{'approval_status': None,
 'customer_id': 'C-1',
 'customer_tier': 'unknown',
 'intent': 'unknown',
 'messages': [{'content': 'Please review my refund request.', 'role': 'user'}],
 'refund_amount_usd': None}
--- Incoming update ---
{'intent': 'refund_request',
 'messages': [{'content': 'I have your request, C-1.', 'role': 'assistant'}]}
--- State after applying update ---
{'approval_status': None,
 'customer_id': 'C-1',
 'customer_tier': 'unknown',
 'intent': 'refund_request',
 'messages': [{'content': 'Please review my refund request.', 'role': 'user'},
              {'content': 'I have your request, C-1.', 'role': 'assistant'}],
 'refund_amount_usd': None}

=== Apply second_node (assistant reply appends) ===

--- Messages sent to the model ---
[{'content': 'You are AcmeCorp support. Give a brief acknowledgement of the '
             "customer's support request, without making promises about "
             'refunds or approvals.',
  'role': 'system'},
 {'content': 'Please review my refund request.', 'role': 'user'},
 {'content': 'I have your request, C-1.', 'role': 'assistant'}]
--- second_node update ---
{'messages': [{'content': 'Thank you for reaching out.\u202fWe’ve received '
                          'your refund request and will review it shortly. If '
                          'we need any additional information, we’ll let you '
                          'know.',
               'role': 'assistant'}]}

--- State before update ---
{'approval_status': None,
 'customer_id': 'C-1',
 'customer_tier': 'unknown',
 'intent': 'refund_request',
 'messages': [{'content': 'Please review my refund request.', 'role': 'user'},
              {'content': 'I have your request, C-1.', 'role': 'assistant'}],
 'refund_amount_usd': None}
--- Incoming update ---
{'messages': [{'content': 'Thank you for reaching out.\u202fWe’ve received '
                          'your refund request and will review it shortly. If '
                          'we need any additional information, we’ll let you '
                          'know.',
               'role': 'assistant'}]}
--- State after applying update ---
{'approval_status': None,
 'customer_id': 'C-1',
 'customer_tier': 'unknown',
 'intent': 'refund_request',
 'messages': [{'content': 'Please review my refund request.', 'role': 'user'},
              {'content': 'I have your request, C-1.', 'role': 'assistant'},
              {'content': 'Thank you for reaching out.\u202fWe’ve received '
                          'your refund request and will review it shortly. If '
                          'we need any additional information, we’ll let you '
                          'know.',
               'role': 'assistant'}],
 'refund_amount_usd': None}

=== Final state ===
{'approval_status': None,
 'customer_id': 'C-1',
 'customer_tier': 'unknown',
 'intent': 'refund_request',
 'messages': [{'content': 'Please review my refund request.', 'role': 'user'},
              {'content': 'I have your request, C-1.', 'role': 'assistant'},
              {'content': 'Thank you for reaching out.\u202fWe’ve received '
                          'your refund request and will review it shortly. If '
                          'we need any additional information, we’ll let you '
                          'know.',
               'role': 'assistant'}],
 'refund_amount_usd': None}
Message count: 3
Current intent: refund_request
Latest reply: Thank you for reaching out. We’ve received your refund request and will review it shortly. If we need any additional information, we’ll let you know.
'''