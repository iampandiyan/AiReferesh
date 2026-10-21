"""Exercise 6: patch a mistaken classification and replay from a checkpoint.

Run this file by itself after installing `openai` and `python-dotenv` and
adding TOGETHER_STUDY_API_KEY to a `.env` file. SQLite is used only inside this
script to record the sample's state snapshots.

Behavior: a deliberately simple classifier misses a refund request that does
not contain the word "refund". The script restores the checkpoint after account
retrieval, patches intent, and continues without repeating that lookup.
Lesson: replay from the right checkpoint and keep routing deterministic; a
checkpoint after completed work avoids rerunning that work.
"""

import json
import os
import sqlite3
from pprint import pprint
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "You are AcmeCorp support. Give a concise message explaining that this "
    "refund request requires human review."
)
HUMAN_APPROVAL_THRESHOLD_USD = 500.0


def create_client() -> OpenAI:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    return OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")


def classify_intent(message: str) -> str:
    lowered = message.lower()
    print("\n--- Classifying customer message ---")
    print("Original message:", message)
    print("Lowercase message:", lowered)
    if "refund" in lowered:
        print("Found 'refund'; classified as refund_request.")
        return "refund_request"
    if "invoice" in lowered or "bill" in lowered:
        print("Found 'invoice' or 'bill'; classified as billing_question.")
        return "billing_question"
    print("No known keyword found; classified as feature_help.")
    return "feature_help"


def route_after_propose(state: dict[str, Any]) -> str:
    print("\n--- Routing state ---")
    pprint(state)
    if state["intent"] != "refund_request":
        print("Intent is not a refund; route to confirm_to_customer.")
        return "confirm_to_customer"
    amount = state.get("refund_amount_usd") or 0.0
    print(
        f"Refund amount: ${amount:.2f}; human-approval threshold: "
        f"${HUMAN_APPROVAL_THRESHOLD_USD:.2f}"
    )
    if amount >= HUMAN_APPROVAL_THRESHOLD_USD:
        print("Amount meets/exceeds threshold; route to request_human_approval.")
        return "request_human_approval"
    print("Amount is below threshold; route to auto_execute.")
    return "auto_execute"


def main() -> None:
    message = "The renewal went through after I cancelled - I want my $700 back."
    print("=== Starting time-travel / checkpoint replay demo ===")
    print("Sample message:", message)
    history = sqlite3.connect(":memory:")
    history.execute(
        "CREATE TABLE snapshots (step TEXT PRIMARY KEY, state_json TEXT NOT NULL)"
    )
    print("Created in-memory SQLite snapshots table.")
    lookup_count = 0

    state: dict[str, Any] = {
        "customer_id": "cust-7-pro",
        "message": message,
        "intent": classify_intent(message),
        "customer_tier": "unknown",
        "refund_amount_usd": 700.0,
        "approval_status": None,
    }
    print("\n--- State after initial classification ---")
    pprint(state)
    print("Saving checkpoint: after_classify")
    history.execute(
        "INSERT INTO snapshots VALUES (?, ?)",
        ("after_classify", json.dumps(state)),
    )

    state["customer_tier"] = "pro"
    lookup_count += 1
    print("\nRetrieved account; customer_tier changed to 'pro'.")
    print("Account lookup count:", lookup_count)
    print("State after account retrieval:")
    pprint(state)
    print("Saving checkpoint: after_retrieve_account")
    history.execute(
        "INSERT INTO snapshots VALUES (?, ?)",
        ("after_retrieve_account", json.dumps(state)),
    )
    print("Initial intent:", state["intent"])
    print("Initial route:", route_after_propose(state))

    # Rewind to the checkpoint after account retrieval, so the lookup is not repeated.
    print("\n--- Rewinding to the after_retrieve_account checkpoint ---")
    row = history.execute(
        "SELECT state_json FROM snapshots WHERE step = ?",
        ("after_retrieve_account",),
    ).fetchone()
    if row is None:
        raise RuntimeError("Required account-retrieval checkpoint is missing.")
    print("Raw checkpoint JSON:")
    print(row[0])
    replayed = json.loads(row[0])
    print("Restored state before patch:")
    pprint(replayed)
    print("Patching intent from", repr(replayed["intent"]), "to 'refund_request'.")
    replayed["intent"] = "refund_request"
    print("Restored state after patch:")
    pprint(replayed)
    approval_route = route_after_propose(replayed)
    print("Replayed intent:", replayed["intent"], "| route:", approval_route)
    print("Account lookups:", lookup_count)
    assert approval_route == "request_human_approval"
    assert lookup_count == 1, "Replay should not repeat completed account retrieval."

    client = create_client()
    request_messages = [
        {"role": "system", "content": PROMPT_V1},
        {"role": "user", "content": message},
    ]
    print("\n--- Requesting customer update from model ---")
    print("Messages sent to the model:")
    pprint(request_messages)
    response = client.chat.completions.create(
        model=MODEL,
        messages=request_messages,
    )
    reply = response.choices[0].message.content
    if not reply:
        raise RuntimeError("The model returned an empty reply.")
    print("Customer update:", reply)
    history.close()
    print("Closed in-memory SQLite connection.")


if __name__ == "__main__":
    main()

'''
=== Starting time-travel / checkpoint replay demo ===
Sample message: The renewal went through after I cancelled - I want my $700 back.
Created in-memory SQLite snapshots table.

--- Classifying customer message ---
Original message: The renewal went through after I cancelled - I want my $700 back.
Lowercase message: the renewal went through after i cancelled - i want my $700 back.
No known keyword found; classified as feature_help.

--- State after initial classification ---
{'approval_status': None,
 'customer_id': 'cust-7-pro',
 'customer_tier': 'unknown',
 'intent': 'feature_help',
 'message': 'The renewal went through after I cancelled - I want my $700 back.',
 'refund_amount_usd': 700.0}
Saving checkpoint: after_classify

Retrieved account; customer_tier changed to 'pro'.
Account lookup count: 1
State after account retrieval:
{'approval_status': None,
 'customer_id': 'cust-7-pro',
 'customer_tier': 'pro',
 'intent': 'feature_help',
 'message': 'The renewal went through after I cancelled - I want my $700 back.',
 'refund_amount_usd': 700.0}
Saving checkpoint: after_retrieve_account
Initial intent: feature_help

--- Routing state ---
{'approval_status': None,
 'customer_id': 'cust-7-pro',
 'customer_tier': 'pro',
 'intent': 'feature_help',
 'message': 'The renewal went through after I cancelled - I want my $700 back.',
 'refund_amount_usd': 700.0}
Intent is not a refund; route to confirm_to_customer.
Initial route: confirm_to_customer

--- Rewinding to the after_retrieve_account checkpoint ---
Raw checkpoint JSON:
{"customer_id": "cust-7-pro", "message": "The renewal went through after I cancelled - I want my $700 back.", "intent": "feature_help", "customer_tier": "pro", "refund_amount_usd": 700.0, "approval_status": null}
Restored state before patch:
{'approval_status': None,
 'customer_id': 'cust-7-pro',
 'customer_tier': 'pro',
 'intent': 'feature_help',
 'message': 'The renewal went through after I cancelled - I want my $700 back.',
 'refund_amount_usd': 700.0}
Patching intent from 'feature_help' to 'refund_request'.
Restored state after patch:
{'approval_status': None,
 'customer_id': 'cust-7-pro',
 'customer_tier': 'pro',
 'intent': 'refund_request',
 'message': 'The renewal went through after I cancelled - I want my $700 back.',
 'refund_amount_usd': 700.0}

--- Routing state ---
{'approval_status': None,
 'customer_id': 'cust-7-pro',
 'customer_tier': 'pro',
 'intent': 'refund_request',
 'message': 'The renewal went through after I cancelled - I want my $700 back.',
 'refund_amount_usd': 700.0}
Refund amount: $700.00; human-approval threshold: $500.00
Amount meets/exceeds threshold; route to request_human_approval.
Replayed intent: refund_request | route: request_human_approval
Account lookups: 1

--- Requesting customer update from model ---
Messages sent to the model:
[{'content': 'You are AcmeCorp support. Give a concise message explaining that '
             'this refund request requires human review.',
  'role': 'system'},
 {'content': 'The renewal went through after I cancelled - I want my $700 '
             'back.',
  'role': 'user'}]
Customer update: I’m sorry to hear about the renewal issue. Your refund request will need to be reviewed by a member of our support team. I’ve escalated it for you, and you’ll hear back shortly with an update. Thank you for your patience.
Closed in-memory SQLite connection.
'''