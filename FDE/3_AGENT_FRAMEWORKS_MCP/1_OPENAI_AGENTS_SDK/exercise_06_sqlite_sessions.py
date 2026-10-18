"""Exercise 6: persist two support turns with a SQLite conversation session.

Run independently after installing `openai` and setting TOGETHER_STUDY_API_KEY.
The standard-library SQLite database is created beside this script when run.

Behavior: turn 2 is sent together with prior conversation messages, so "refund
it" can refer to order #4823 without repeating the identifier. A new session ID
is used each run to keep demonstrations isolated.
Lesson: an LLM call has no automatic memory. Persist and replay conversation
history explicitly, and keep session boundaries associated with the right user.
"""

import os
import sqlite3
import uuid
from pathlib import Path

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "You are AcmeCorp support. Be concise, use conversation context to resolve "
    "follow-up references, and do not claim that a refund was actually processed."
)
DATABASE = Path(__file__).with_name("acmecorp_sessions.db")


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    session_id = str(uuid.uuid4())
    customer_turns = [
        "Pro plan, my invoice is missing for order #4823.",
        "Actually, just refund it.",
    ]

    with sqlite3.connect(DATABASE) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_messages (
                session_id TEXT NOT NULL,
                turn_number INTEGER NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                PRIMARY KEY (session_id, turn_number, role)
            )
            """
        )
        for turn_number, customer_message in enumerate(customer_turns, 1):
            history = connection.execute(
                """
                SELECT role, content
                FROM conversation_messages
                WHERE session_id = ?
                ORDER BY turn_number, CASE role WHEN 'user' THEN 0 ELSE 1 END
                """,
                (session_id,),
            ).fetchall()
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_V1},
                    *[{"role": role, "content": content} for role, content in history],
                    {"role": "user", "content": customer_message},
                ],
                max_tokens=400,
            )
            answer = response.choices[0].message.content
            if not answer:
                raise RuntimeError("The model returned an empty response.")
            connection.executemany(
                """
                INSERT INTO conversation_messages
                    (session_id, turn_number, role, content)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (session_id, turn_number, "user", customer_message),
                    (session_id, turn_number, "assistant", answer),
                ],
            )
            print(f"turn {turn_number}: {answer}")


if __name__ == "__main__":
    main()
