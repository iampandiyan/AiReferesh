"""Exercise 1: the minimum stateful chat flow.

Run this file by itself after installing `openai` and `python-dotenv` and
adding TOGETHER_STUDY_API_KEY to a `.env` file. It sends two turns to Together
and carries the complete message list from the first turn into the second.

Behavior: each assistant response is appended to state instead of replacing the
message history. The final state therefore contains both user/assistant turns.
Lesson: a list update needs an explicit append/merge rule; replacing the list
silently loses earlier conversation context.
"""

import os
from pprint import pprint
from typing import TypedDict

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "You are AcmeCorp support. Answer the customer's message clearly and briefly. "
    "Use only the conversation context provided."
)


class ChatState(TypedDict):
    messages: list[dict[str, str]]


def create_client() -> OpenAI:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    return OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")


def chatbot(client: OpenAI, state: ChatState) -> dict[str, list[dict[str, str]]]:
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
    update = {"messages": [{"role": "assistant", "content": reply}]}
    print("--- Update returned by chatbot ---")
    pprint(update)
    return update


def append_update(state: ChatState, update: dict[str, list[dict[str, str]]]) -> ChatState:
    new_state: ChatState = {"messages": [*state["messages"], *update["messages"]]}
    print("--- State after appending the update ---")
    pprint(new_state)
    return new_state


def main() -> None:
    client = create_client()
    state: ChatState = {"messages": [{"role": "user", "content": "Hi, I need help."}]}
    print("--- Initial state (before turn 1) ---")
    pprint(state)
    state = append_update(state, chatbot(client, state))
    print("After turn 1:", len(state["messages"]), "messages")

    state["messages"].append(
        {"role": "user", "content": "How can I check the status of my request?"}
    )
    print("--- State after adding the second user message ---")
    pprint(state)
    state = append_update(state, chatbot(client, state))
    print("After turn 2:", len(state["messages"]), "messages")
    print("Latest reply:", state["messages"][-1]["content"])
    assert len(state["messages"]) == 4, "Both user/assistant turns should be retained."


if __name__ == "__main__":
    main()

'''
--- Initial state (before turn 1) ---
{'messages': [{'content': 'Hi, I need help.', 'role': 'user'}]}

--- Messages sent to the model ---
[{'content': "You are AcmeCorp support. Answer the customer's message clearly "
             'and briefly. Use only the conversation context provided.',
  'role': 'system'},
 {'content': 'Hi, I need help.', 'role': 'user'}]
--- Update returned by chatbot ---
{'messages': [{'content': 'Hello! How can I assist you today? Please let '
                          'me\u202fknow the issue you’re experiencing.',
               'role': 'assistant'}]}
--- State after appending the update ---
{'messages': [{'content': 'Hi, I need help.', 'role': 'user'},
              {'content': 'Hello! How can I assist you today? Please let '
                          'me\u202fknow the issue you’re experiencing.',
               'role': 'assistant'}]}
After turn 1: 2 messages
--- State after adding the second user message ---
{'messages': [{'content': 'Hi, I need help.', 'role': 'user'},
              {'content': 'Hello! How can I assist you today? Please let '
                          'me\u202fknow the issue you’re experiencing.',
               'role': 'assistant'},
              {'content': 'How can I check the status of my request?',
               'role': 'user'}]}

--- Messages sent to the model ---
[{'content': "You are AcmeCorp support. Answer the customer's message clearly "
             'and briefly. Use only the conversation context provided.',
  'role': 'system'},
 {'content': 'Hi, I need help.', 'role': 'user'},
 {'content': 'Hello! How can I assist you today? Please let me\u202fknow the '
             'issue you’re experiencing.',
  'role': 'assistant'},
 {'content': 'How can I check the status of my request?', 'role': 'user'}]
--- Update returned by chatbot ---
{'messages': [{'content': 'You can view the status of any request by:\n'
                          '\n'
                          '1. **Logging into the AcmeCorp portal** – go '
                          'to\u202f'
                          '[portal.acmecorp.com](https://portal.acmecorp.com) '
                          'and sign in.  \n'
                          '2. Click **“My Requests”** in the top '
                          'navigation.  \n'
                          '3. Find your request in the list; the **“Status”** '
                          'column shows its current state (e.g., Open, In '
                          'Progress, Resolved).  \n'
                          '\n'
                          'If you have a ticket number, you can also enter it '
                          'directly in the **Search** box on the “My Requests” '
                          'page.\n'
                          '\n'
                          'Let me know if you need help accessing the portal '
                          'or locating a specific ticket!',
               'role': 'assistant'}]}
--- State after appending the update ---
{'messages': [{'content': 'Hi, I need help.', 'role': 'user'},
              {'content': 'Hello! How can I assist you today? Please let '
                          'me\u202fknow the issue you’re experiencing.',
               'role': 'assistant'},
              {'content': 'How can I check the status of my request?',
               'role': 'user'},
              {'content': 'You can view the status of any request by:\n'
                          '\n'
                          '1. **Logging into the AcmeCorp portal** – go '
                          'to\u202f'
                          '[portal.acmecorp.com](https://portal.acmecorp.com) '
                          'and sign in.  \n'
                          '2. Click **“My Requests”** in the top '
                          'navigation.  \n'
                          '3. Find your request in the list; the **“Status”** '
                          'column shows its current state (e.g., Open, In '
                          'Progress, Resolved).  \n'
                          '\n'
                          'If you have a ticket number, you can also enter it '
                          'directly in the **Search** box on the “My Requests” '
                          'page.\n'
                          '\n'
                          'Let me know if you need help accessing the portal '
                          'or locating a specific ticket!',
               'role': 'assistant'}]}
After turn 2: 4 messages
Latest reply: You can view the status of any request by:

1. **Logging into the AcmeCorp portal** – go to [portal.acmecorp.com](https://portal.acmecorp.com) and sign in.
2. Click **“My Requests”** in the top navigation.
3. Find your request in the list; the **“Status”** column shows its current state (e.g., Open, In Progress, Resolved).

If you have a ticket number, you can also enter it directly in the **Search** box on the “My Requests” page.

Let me know if you need help accessing the portal or locating a specific ticket!
'''
