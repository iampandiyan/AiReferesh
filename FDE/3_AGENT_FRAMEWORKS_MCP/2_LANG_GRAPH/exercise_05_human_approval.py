"""Exercise 5: run a refund workflow with a human-approval pause.

Run this file by itself after installing `openai` and `python-dotenv` and
adding TOGETHER_STUDY_API_KEY to a `.env` file. The in-memory state is local
to this script; no other exercise file is imported.

Behavior: a $120 refund proceeds automatically. A $620 refund pauses at the
approval step, then resumes after the sample human decision is "approved".
Lesson: human-in-the-loop work needs a clear pause point and an explicit resume
decision; the approval policy is separate from response generation.
"""

import os
import re
from pprint import pprint
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "You are AcmeCorp support. Explain the refund outcome politely and briefly. "
    "Do not change the supplied approval decision or refund amount."
)
HUMAN_APPROVAL_THRESHOLD_USD = 500.0


def create_client() -> OpenAI:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    return OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")


def amount_from_message(message: str) -> float:
    print("\n--- Extracting refund amount ---")
    print("Customer message:", message)
    match = re.search(r"\$?\s*(\d+(?:\.\d{1,2})?)", message)
    if not match:
        raise ValueError("A numeric refund amount is required in the sample message.")
    amount = float(match.group(1))
    print("Matched amount text:", match.group(1))
    print("Parsed refund amount:", amount)
    return amount


def draft_reply(client: OpenAI, amount: float, approved: bool) -> str:
    outcome = "approved and issued" if approved else "not approved"
    request_messages = [
        {"role": "system", "content": PROMPT_V1},
        {
            "role": "user",
            "content": f"Refund ${amount:.2f} was {outcome}. Give a concise explanation.",
        },
    ]
    print("\n--- Drafting customer reply ---")
    print(f"Amount: ${amount:.2f} | approved: {approved} | outcome: {outcome}")
    print("Messages sent to the model:")
    pprint(request_messages)
    response = client.chat.completions.create(
        model=MODEL,
        messages=request_messages,
    )
    details = response.choices[0].message.content
    if not details:
        raise RuntimeError("The model returned an empty reply.")
    reply = f"Refund of ${amount:.2f} has been {outcome}. {details}"
    print("Model details:", details)
    print("Final customer reply:", reply)
    return reply


def run_refund(client: OpenAI, customer_message: str) -> dict[str, Any]:
    print("\n=== Starting refund workflow ===")
    amount = amount_from_message(customer_message)
    print(
        f"Routing amount ${amount:.2f} against human-approval threshold "
        f"${HUMAN_APPROVAL_THRESHOLD_USD:.2f}"
    )
    if amount >= HUMAN_APPROVAL_THRESHOLD_USD:
        state: dict[str, Any] = {
            "refund_amount_usd": amount,
            "approval_status": "pending",
            "paused_for_approval": True,
        }
        print("Amount meets/exceeds threshold; pausing for human approval.")
        print("Paused workflow state:")
        pprint(state)
        return state

    state: dict[str, Any] = {
        "refund_amount_usd": amount,
        "approval_status": "approved",
        "paused_for_approval": False,
    }
    print("Amount is below threshold; auto-approving.")
    print("State before drafting reply:")
    pprint(state)
    state["reply"] = draft_reply(client, amount, approved=True)
    print("Completed workflow state:")
    pprint(state)
    return state


def resume_refund(
    client: OpenAI, state: dict[str, Any], human_decision: str
) -> dict[str, Any]:
    print("\n=== Resuming paused refund workflow ===")
    print("State before resume:")
    pprint(state)
    print("Human decision:", human_decision)
    if not state.get("paused_for_approval"):
        raise ValueError("This refund is not paused for human approval.")
    if human_decision not in ("approved", "rejected"):
        raise ValueError("Human decision must be 'approved' or 'rejected'.")
    state["approval_status"] = human_decision
    state["paused_for_approval"] = False
    print("State after applying human decision:")
    pprint(state)
    state["reply"] = draft_reply(
        client,
        state["refund_amount_usd"],
        approved=human_decision == "approved",
    )
    print("Completed resumed state:")
    pprint(state)
    return state


def main() -> None:
    client = create_client()
    print("\n######## LOW-VALUE REFUND EXAMPLE ########")
    low_value = run_refund(client, "Please refund $120 for the duplicate invoice.")
    print("Run A:", low_value["approval_status"], "|", low_value["reply"])
    assert low_value["approval_status"] == "approved"

    print("\n######## HIGH-VALUE REFUND EXAMPLE ########")
    high_value = run_refund(client, "Please refund $620 for the cancelled renewal.")
    assert high_value["paused_for_approval"]
    print(f"Run B paused for approval: ${high_value['refund_amount_usd']:.2f}")
    high_value = resume_refund(client, high_value, human_decision="approved")
    print("Run B:", high_value["approval_status"], "|", high_value["reply"])
    assert high_value["approval_status"] == "approved"
    assert high_value["reply"].startswith("Refund of $620.00 has been approved and issued.")


if __name__ == "__main__":
    main()

'''

######## LOW-VALUE REFUND EXAMPLE ########

=== Starting refund workflow ===

--- Extracting refund amount ---
Customer message: Please refund $120 for the duplicate invoice.
Matched amount text: 120
Parsed refund amount: 120.0
Routing amount $120.00 against human-approval threshold $500.00
Amount is below threshold; auto-approving.
State before drafting reply:
{'approval_status': 'approved',
 'paused_for_approval': False,
 'refund_amount_usd': 120.0}

--- Drafting customer reply ---
Amount: $120.00 | approved: True | outcome: approved and issued
Messages sent to the model:
[{'content': 'You are AcmeCorp support. Explain the refund outcome politely '
             'and briefly. Do not change the supplied approval decision or '
             'refund amount.',
  'role': 'system'},
 {'content': 'Refund $120.00 was approved and issued. Give a concise '
             'explanation.',
  'role': 'user'}]
Model details: Your refund of **$120.00** has been approved and the amount has been issued to your original payment method. If you have any further questions, please let us know.
Final customer reply: Refund of $120.00 has been approved and issued. Your refund of **$120.00** has been approved and the amount has been issued to your original payment method. If you have any further questions, please let us know.
Completed workflow state:
{'approval_status': 'approved',
 'paused_for_approval': False,
 'refund_amount_usd': 120.0,
 'reply': 'Refund of $120.00 has been approved and issued. Your refund of '
          '**$120.00** has been approved and the amount has been issued to '
          'your original payment method. If you have any further questions, '
          'please let us know.'}
Run A: approved | Refund of $120.00 has been approved and issued. Your refund of **$120.00** has been approved and the amount has been issued to your original payment method. If you have any further questions, please let us know.

######## HIGH-VALUE REFUND EXAMPLE ########

=== Starting refund workflow ===

--- Extracting refund amount ---
Customer message: Please refund $620 for the cancelled renewal.
Matched amount text: 620
Parsed refund amount: 620.0
Routing amount $620.00 against human-approval threshold $500.00
Amount meets/exceeds threshold; pausing for human approval.
Paused workflow state:
{'approval_status': 'pending',
 'paused_for_approval': True,
 'refund_amount_usd': 620.0}
Run B paused for approval: $620.00

=== Resuming paused refund workflow ===
State before resume:
{'approval_status': 'pending',
 'paused_for_approval': True,
 'refund_amount_usd': 620.0}
Human decision: approved
State after applying human decision:
{'approval_status': 'approved',
 'paused_for_approval': False,
 'refund_amount_usd': 620.0}

--- Drafting customer reply ---
Amount: $620.00 | approved: True | outcome: approved and issued
Messages sent to the model:
[{'content': 'You are AcmeCorp support. Explain the refund outcome politely '
             'and briefly. Do not change the supplied approval decision or '
             'refund amount.',
  'role': 'system'},
 {'content': 'Refund $620.00 was approved and issued. Give a concise '
             'explanation.',
  'role': 'user'}]
Model details: Your refund of **$620.00** has been approved and issued. The amount has been returned to the original payment method and should appear on your statement within a few business days. If you have any further questions, please let us know.
Final customer reply: Refund of $620.00 has been approved and issued. Your refund of **$620.00** has been approved and issued. The amount has been returned to the original payment method and should appear on your statement within a few business days. If you have any further questions, please let us know.
Completed resumed state:
{'approval_status': 'approved',
 'paused_for_approval': False,
 'refund_amount_usd': 620.0,
 'reply': 'Refund of $620.00 has been approved and issued. Your refund of '
          '**$620.00** has been approved and issued. The amount has been '
          'returned to the original payment method and should appear on your '
          'statement within a few business days. If you have any further '
          'questions, please let us know.'}
Run B: approved | Refund of $620.00 has been approved and issued. Your refund of **$620.00** has been approved and issued. The amount has been returned to the original payment method and should appear on your statement within a few business days. If you have any further questions, please let us know.
'''
