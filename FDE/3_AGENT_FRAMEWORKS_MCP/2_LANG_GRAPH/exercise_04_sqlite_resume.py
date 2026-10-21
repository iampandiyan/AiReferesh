"""Exercise 4: resume a workflow from a SQLite checkpoint.

Run this file in two separate processes:
  python exercise_04_sqlite_resume.py first
  python exercise_04_sqlite_resume.py resume
Both commands must use the same --db path (it defaults to a stable temp-file
path). Install `openai` and `python-dotenv` and add TOGETHER_STUDY_API_KEY to a
`.env` file before running.

Behavior: the first run stores customer_tier, intent, refund amount, and the
next step before pausing. The second run reloads that data and completes it.
Lesson: a disk-backed checkpoint survives process restarts; process-local
memory does not. Reuse the same thread ID to continue the same conversation.
"""

import argparse
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from pprint import pprint
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "You are AcmeCorp support. Write a concise customer-facing update confirming "
    "that the approved refund has been issued."
)
THREAD_ID = "acme-restart-01"
DEFAULT_DB = Path(tempfile.gettempdir()) / "acme_langgraph_exercise_04.sqlite"


def create_client() -> OpenAI:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    return OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")


def connect(db_path: Path) -> sqlite3.Connection:
    print(f"Opening SQLite database: {db_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS checkpoints "
        "(thread_id TEXT PRIMARY KEY, state_json TEXT NOT NULL, next_node TEXT NOT NULL)"
    )
    print("Checkpoint table is ready.")
    return connection


def save_checkpoint(connection: sqlite3.Connection, state: dict[str, Any]) -> None:
    print("\n--- State being saved ---")
    pprint(state)
    next_node = "request_human_approval"
    print(f"Saving checkpoint for thread {THREAD_ID!r}; next node: {next_node!r}")
    connection.execute(
        "INSERT OR REPLACE INTO checkpoints (thread_id, state_json, next_node) "
        "VALUES (?, ?, ?)",
        (THREAD_ID, json.dumps(state), next_node),
    )
    connection.commit()
    print("Checkpoint committed to SQLite.")


def load_checkpoint(connection: sqlite3.Connection) -> dict[str, Any]:
    print(f"\nLoading checkpoint for thread {THREAD_ID!r}...")
    row = connection.execute(
        "SELECT state_json, next_node FROM checkpoints WHERE thread_id = ?",
        (THREAD_ID,),
    ).fetchone()
    if row is None:
        raise RuntimeError("No checkpoint found. Run this script with the 'first' command.")
    print("Raw database row:")
    pprint(row)
    state = json.loads(row[0])
    print("State decoded from JSON:")
    pprint(state)
    state["next_node"] = row[1]
    print("State with the saved next node:")
    pprint(state)
    return state


def run_first(connection: sqlite3.Connection) -> None:
    print("\n=== FIRST PROCESS: create and save checkpoint ===")
    state = {
        "thread_id": THREAD_ID,
        "customer_id": "cust-9-pro",
        "customer_tier": "pro",
        "intent": "refund_request",
        "refund_amount_usd": 620.0,
        "approval_status": "pending",
    }
    print("Workflow state before checkpoint:")
    pprint(state)
    save_checkpoint(connection, state)
    print("Paused before human approval.")
    print("Saved tier:", state["customer_tier"], "| intent:", state["intent"])
    print("Now start a fresh process with the 'resume' command.")


def run_resume(client: OpenAI, connection: sqlite3.Connection) -> None:
    print("\n=== RESUME PROCESS: load and continue checkpoint ===")
    state = load_checkpoint(connection)
    next_node = state.pop("next_node")
    print(f"Next node loaded from checkpoint: {next_node!r}")
    if next_node != "request_human_approval":
        raise RuntimeError("Checkpoint is not waiting for human approval.")

    print("\nState before applying the human approval decision:")
    pprint(state)
    state["approval_status"] = "approved"
    print("State after applying the human approval decision:")
    pprint(state)

    request_messages = [
        {"role": "system", "content": PROMPT_V1},
        {
            "role": "user",
            "content": (
                f"Customer {state['customer_id']} has an approved refund of "
                f"${state['refund_amount_usd']:.2f}. Confirm it."
            ),
        },
    ]
    print("\nMessages sent to the model:")
    pprint(request_messages)
    response = client.chat.completions.create(
        model=MODEL,
        messages=request_messages,
    )
    reply = response.choices[0].message.content
    if not reply:
        raise RuntimeError("The model returned an empty reply.")
    state["reply"] = reply
    print("\nState after adding the model reply:")
    pprint(state)
    next_node = "complete"
    print(f"Saving resumed state; next node: {next_node!r}")
    connection.execute(
        "UPDATE checkpoints SET state_json = ?, next_node = ? WHERE thread_id = ?",
        (json.dumps(state), next_node, THREAD_ID),
    )
    connection.commit()
    print("Updated checkpoint committed to SQLite.")
    print("Resumed thread:", state["thread_id"])
    print("Persisted tier:", state["customer_tier"], "| intent:", state["intent"])
    print("Approval:", state["approval_status"])
    print("Reply:", reply)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("first", "resume"))
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    connection = connect(args.db)
    try:
        if args.command == "first":
            run_first(connection)
        else:
            run_resume(create_client(), connection)
    finally:
        connection.close()


if __name__ == "__main__":
    main()

'''
ython exercise_03_router_boundaries.py

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

ython exercise_04_sqlite_resume.py first
Opening SQLite database: C:\Users\Pandiyan\AppData\Local\Temp\acme_langgraph_exercise_04.sqlite
Checkpoint table is ready.

=== FIRST PROCESS: create and save checkpoint ===
Workflow state before checkpoint:
{'approval_status': 'pending',
 'customer_id': 'cust-9-pro',
 'customer_tier': 'pro',
 'intent': 'refund_request',
 'refund_amount_usd': 620.0,
 'thread_id': 'acme-restart-01'}

--- State being saved ---
{'approval_status': 'pending',
 'customer_id': 'cust-9-pro',
 'customer_tier': 'pro',
 'intent': 'refund_request',
 'refund_amount_usd': 620.0,
 'thread_id': 'acme-restart-01'}
Saving checkpoint for thread 'acme-restart-01'; next node: 'request_human_approval'
Checkpoint committed to SQLite.
Paused before human approval.
Saved tier: pro | intent: refund_request
Now start a fresh process with the 'resume' command.

(fde-lab) C:\Storage\AI Development\GITCHECKOUT\AiReferesh\FDE\3_AGENT_FRAMEWORKS_MCP\2_LANG_GRAPH>python exercise_04_sqlite_resume.py resume
Opening SQLite database: C:\Users\Pandiyan\AppData\Local\Temp\acme_langgraph_exercise_04.sqlite
Checkpoint table is ready.

=== RESUME PROCESS: load and continue checkpoint ===

Loading checkpoint for thread 'acme-restart-01'...
Raw database row:
('{"thread_id": "acme-restart-01", "customer_id": "cust-9-pro", '
 '"customer_tier": "pro", "intent": "refund_request", "refund_amount_usd": '
 '620.0, "approval_status": "pending"}',
 'request_human_approval')
State decoded from JSON:
{'approval_status': 'pending',
 'customer_id': 'cust-9-pro',
 'customer_tier': 'pro',
 'intent': 'refund_request',
 'refund_amount_usd': 620.0,
 'thread_id': 'acme-restart-01'}
State with the saved next node:
{'approval_status': 'pending',
 'customer_id': 'cust-9-pro',
 'customer_tier': 'pro',
 'intent': 'refund_request',
 'next_node': 'request_human_approval',
 'refund_amount_usd': 620.0,
 'thread_id': 'acme-restart-01'}
Next node loaded from checkpoint: 'request_human_approval'

State before applying the human approval decision:
{'approval_status': 'pending',
 'customer_id': 'cust-9-pro',
 'customer_tier': 'pro',
 'intent': 'refund_request',
 'refund_amount_usd': 620.0,
 'thread_id': 'acme-restart-01'}
State after applying the human approval decision:
{'approval_status': 'approved',
 'customer_id': 'cust-9-pro',
 'customer_tier': 'pro',
 'intent': 'refund_request',
 'refund_amount_usd': 620.0,
 'thread_id': 'acme-restart-01'}

Messages sent to the model:
[{'content': 'You are AcmeCorp support. Write a concise customer-facing update '
             'confirming that the approved refund has been issued.',
  'role': 'system'},
 {'content': 'Customer cust-9-pro has an approved refund of $620.00. Confirm '
             'it.',
  'role': 'user'}]

State after adding the model reply:
{'approval_status': 'approved',
 'customer_id': 'cust-9-pro',
 'customer_tier': 'pro',
 'intent': 'refund_request',
 'refund_amount_usd': 620.0,
 'reply': 'Hello,\n'
          '\n'
          'We’re pleased to let you know that your approved refund of '
          '**$620.00** has been processed and the funds are on their way to '
          'your original payment method. You should see the credit appear in '
          'your account within the next few business days.\n'
          '\n'
          'If you have any questions or need further assistance, please don’t '
          'hesitate to reach out.\n'
          '\n'
          'Thank you for choosing AcmeCorp!',
 'thread_id': 'acme-restart-01'}
Saving resumed state; next node: 'complete'
Updated checkpoint committed to SQLite.
Resumed thread: acme-restart-01
Persisted tier: pro | intent: refund_request
Approval: approved
Reply: Hello,

We’re pleased to let you know that your approved refund of **$620.00** has been processed and the funds are on their way to your original payment method. You should see the credit appear in your account within the next few business days.

If you have any questions or need further assistance, please don’t hesitate to reach out.

Thank you for choosing AcmeCorp!
'''