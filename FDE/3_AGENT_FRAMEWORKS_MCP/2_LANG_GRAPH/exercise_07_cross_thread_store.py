"""Exercise 7: keep customer preferences across separate support threads.

Run this file by itself after installing `openai` and `python-dotenv` and
adding TOGETHER_STUDY_API_KEY to a `.env` file. The simple in-memory store is
implemented in this file; it does not depend on any other exercise.

Behavior: thread acme-t1 saves a customer's contact preference. A fresh thread,
acme-t2, reads it using the same customer namespace.
Lesson: a thread-scoped checkpoint stores short-term conversation state;
a customer-keyed Store shares long-term preferences across threads. This demo
store is process-local; use a persistent backend when data must survive restarts.
"""

import os
from pprint import pprint
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "You are AcmeCorp support. Greet the returning customer and respect their "
    "saved contact preference."
)
CUSTOMER_ID = "cust-42-ent"


class PreferenceStore:
    def __init__(self) -> None:
        self._values: dict[tuple[str, str, str], dict[str, Any]] = {}

    def put(
        self, namespace: tuple[str, str], key: str, value: dict[str, Any]
    ) -> None:
        store_key = (*namespace, key)
        print("\n--- Writing preference to store ---")
        print("Namespace:", namespace)
        print("Preference key:", key)
        print("Combined store key:", store_key)
        print("Value being saved:")
        pprint(value)
        self._values[store_key] = value
        print("Store contents after write:")
        pprint(self._values)

    def get(
        self, namespace: tuple[str, str], key: str
    ) -> dict[str, Any] | None:
        store_key = (*namespace, key)
        print("\n--- Reading preference from store ---")
        print("Namespace:", namespace)
        print("Preference key:", key)
        print("Combined store key:", store_key)
        value = self._values.get(store_key)
        print("Value returned:")
        pprint(value)
        return value


def create_client() -> OpenAI:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    return OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")


def main() -> None:
    store = PreferenceStore()
    namespace = ("customer_preferences", CUSTOMER_ID)
    print("=== Cross-thread customer preference demo ===")
    print("Customer namespace:", namespace)
    print("Initial store contents:")
    pprint(store._values)

    # The thread ID is deliberately not part of the store namespace.
    thread_t1 = "acme-t1"
    print(f"\n--- Thread {thread_t1} saves a preference ---")
    store.put(namespace, "contact_channel", {"channel": "email"})
    print(f"{thread_t1} saved: email")

    thread_t2 = "acme-t2"
    print(f"\n--- Thread {thread_t2} loads the preference ---")
    preference = store.get(namespace, "contact_channel")
    if preference is None:
        raise RuntimeError("No saved contact preference was found.")
    print(f"{thread_t2} loaded: {preference['channel']}")
    assert preference["channel"] == "email"

    client = create_client()
    request_messages = [
        {"role": "system", "content": PROMPT_V1},
        {
            "role": "user",
            "content": (
                f"Customer {CUSTOMER_ID} is returning. Their saved contact "
                f"channel is {preference['channel']}."
            ),
        },
    ]
    print("\n--- Requesting a greeting from the model ---")
    print("Messages sent to the model:")
    pprint(request_messages)
    response = client.chat.completions.create(
        model=MODEL,
        messages=request_messages,
    )
    reply = response.choices[0].message.content
    if not reply:
        raise RuntimeError("The model returned an empty reply.")
    print("Greeting:", reply)


if __name__ == "__main__":
    main()

'''
=== Cross-thread customer preference demo ===
Customer namespace: ('customer_preferences', 'cust-42-ent')
Initial store contents:
{}

--- Thread acme-t1 saves a preference ---

--- Writing preference to store ---
Namespace: ('customer_preferences', 'cust-42-ent')
Preference key: contact_channel
Combined store key: ('customer_preferences', 'cust-42-ent', 'contact_channel')
Value being saved:
{'channel': 'email'}
Store contents after write:
{('customer_preferences', 'cust-42-ent', 'contact_channel'): {'channel': 'email'}}
acme-t1 saved: email

--- Thread acme-t2 loads the preference ---

--- Reading preference from store ---
Namespace: ('customer_preferences', 'cust-42-ent')
Preference key: contact_channel
Combined store key: ('customer_preferences', 'cust-42-ent', 'contact_channel')
Value returned:
{'channel': 'email'}
acme-t2 loaded: email

--- Requesting a greeting from the model ---
Messages sent to the model:
[{'content': 'You are AcmeCorp support. Greet the returning customer and '
             'respect their saved contact preference.',
  'role': 'system'},
 {'content': 'Customer cust-42-ent is returning. Their saved contact channel '
             'is email.',
  'role': 'user'}]
Greeting: Hello cust‑42‑ent! 👋

Welcome back to AcmeCorp. I’ve noted that you prefer to be contacted by **email**, so I’ll be sure to follow up with any details or next steps through that channel.

If there’s anything specific you’d like assistance with today, just let me know and I’ll get everything prepared for you (and send any necessary information to your email address).

Looking forward to helping you!
'''