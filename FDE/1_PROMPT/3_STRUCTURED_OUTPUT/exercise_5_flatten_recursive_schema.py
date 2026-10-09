"""Exercise 5: flatten a recursive message tree for bounded structured output.

Run independently with `python -m pip install openai pydantic` and
TOGETHER_STUDY_API_KEY set. This file includes its own nested/flat models and sample.

Lesson: recursive schemas are difficult for constrained decoders. A flat list with
parent IDs has a finite schema; preserve and verify the links when converting formats.
"""

import json
import os
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, model_validator


MODEL = "openai/gpt-oss-120b"


class MessageNested(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    author: Literal["merchant", "agent", "bot"]
    body: str = Field(min_length=1, max_length=4000)
    replies: list["MessageNested"] = Field(default_factory=list)

    @model_validator(mode="after")
    def cap_depth(self):
        def depth(message: "MessageNested") -> int:
            return 1 + max((depth(reply) for reply in message.replies), default=0)
        if depth(self) > 5:
            raise ValueError("recursion depth exceeds the supported maximum of 5")
        return self


class MessageFlat(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    parent_id: str | None
    author: Literal["merchant", "agent", "bot"]
    body: str = Field(min_length=1, max_length=4000)


class ThreadFlat(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thread_id: str = Field(pattern=r"^stripe_thr_[a-z0-9]{10}$")
    messages: list[MessageFlat] = Field(min_length=1, max_length=64)


def nested_to_flat(thread_id: str, root: MessageNested) -> ThreadFlat:
    flat: list[MessageFlat] = []

    def visit(node: MessageNested, parent_id: str | None) -> None:
        flat.append(MessageFlat(id=node.id, parent_id=parent_id, author=node.author, body=node.body))
        for reply in node.replies:
            visit(reply, node.id)

    visit(root, None)
    return ThreadFlat(thread_id=thread_id, messages=flat)


def flat_to_nested(thread: ThreadFlat) -> MessageNested:
    by_id = {message.id: message for message in thread.messages}
    children: dict[str | None, list[str]] = {}
    for message in thread.messages:
        children.setdefault(message.parent_id, []).append(message.id)
    roots = children.get(None, [])
    if len(roots) != 1:
        raise ValueError(f"Expected exactly one root message; got {len(roots)}")

    def build(message_id: str) -> MessageNested:
        message = by_id[message_id]
        return MessageNested(
            id=message.id,
            author=message.author,
            body=message.body,
            replies=[build(child_id) for child_id in children.get(message_id, [])],
        )

    return build(roots[0])


def main() -> None:
    root = MessageNested(
        id="m1",
        author="merchant",
        body="el settlement del 18 de mayo no llego",
        replies=[
            MessageNested(
                id="m2",
                author="bot",
                body="Checking status",
                replies=[MessageNested(id="m3", author="agent", body="esta en el ciclo T+2")],
            )
        ],
    )
    thread = nested_to_flat("stripe_thr_a1b2c3d4e5", root)
    round_trip = flat_to_nested(thread)
    assert round_trip == root
    print(f"Flat thread has {len(thread.messages)} messages; round-trip identity: {round_trip == root}")
    schema = ThreadFlat.model_json_schema()
    print("Flat schema object properties:", list(schema["properties"]))
    flat_message_schema = json.dumps(schema.get("$defs", {}).get("MessageFlat", {}))
    recursive_ref = "#/$defs/MessageFlat" in flat_message_schema
    print("MessageFlat schema contains a self-reference:", recursive_ref)
    assert not recursive_ref

    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set TOGETHER_STUDY_API_KEY to run the live schema-conformance call.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Return a valid flat thread with one merchant message and one agent reply."},
            {"role": "user", "content": "Create a thread about a delayed payout. Use thread_id stripe_thr_a1b2c3d4e5."},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "ThreadFlat", "schema": schema, "strict": True},
        },
        max_tokens=300,
    )
    generated = ThreadFlat.model_validate_json(response.choices[0].message.content or "")
    print("Together returned a valid flat thread:", generated.model_dump_json())


if __name__ == "__main__":
    main()