"""Exercise 4: validate, re-prompt, repair formatting, then make a final attempt.

Run independently with `python -m pip install openai pydantic` and
TOGETHER_STUDY_API_KEY set. No notebook cells or sibling exercise files are needed.

Lesson: schema validation is the first rung; retries should carry the validation error,
format repair should not invent missing semantics, and exhausting recovery must be visible.
"""

import json
import logging
import os
import re
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError


MODEL = "openai/gpt-oss-120b"
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOG = logging.getLogger("recovery-ladder")


class SimpleClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Literal["loan", "kyc", "escalate", "inquire"]
    reason: str = Field(min_length=4, max_length=200)


SYSTEM = (
    "Classify this Meridian Capital message. Return one JSON object with intent "
    "loan, kyc, escalate, or inquire and a short reason. Do not invent missing facts."
)
TESTS = [
    "necesito un prestamo hipotecario de $6,000, TC12345678",
    "necesito un prestamo, cualquiera",
    "hazme todo, TC99887766, rapido",
]


def client_from_environment() -> OpenAI:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set TOGETHER_STUDY_API_KEY before running this exercise.")
    return OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")


def call_model(client: OpenAI, query: str, hint: str = "") -> str:
    user_text = query if not hint else f"{query}\n\nPrevious validation error: {hint}\nReturn corrected JSON."
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_text}],
        response_format={"type": "json_object"},
        max_tokens=250,
    )
    return response.choices[0].message.content or ""


def recover_json(text: str) -> str:
    """Strip fences/prose around an object; do not fabricate absent fields."""
    unfenced = re.sub(r"```(?:json)?|```", "", text, flags=re.IGNORECASE).strip()
    start, end = unfenced.find("{"), unfenced.rfind("}")
    if start < 0 or end < start:
        raise ValueError("No JSON object to repair")
    return unfenced[start : end + 1]


def classify_with_ladder(client: OpenAI, query: str) -> SimpleClassification:
    raw = call_model(client, query)
    try:
        result = SimpleClassification.model_validate_json(raw)
        LOG.info("rung=1 status=ok")
        return result
    except ValidationError as error:
        first_error = error.errors()[0]
        LOG.warning("rung=1 status=fail err=%s loc=%s", first_error["type"], first_error["loc"])

    raw = call_model(client, query, hint=str(first_error))
    try:
        result = SimpleClassification.model_validate_json(raw)
        LOG.info("rung=2 status=ok re-prompted")
        return result
    except ValidationError as error:
        second_error = error.errors()[0]
        LOG.warning("rung=2 status=fail err=%s loc=%s", second_error["type"], second_error["loc"])

    try:
        result = SimpleClassification.model_validate_json(recover_json(raw))
        LOG.info("rung=3 status=ok formatting-repair")
        return result
    except (ValueError, ValidationError) as error:
        LOG.warning("rung=3 status=fail err=%s", type(error).__name__)

    raw = call_model(client, query, hint="Previous attempts failed schema validation; produce the exact JSON fields.")
    try:
        result = SimpleClassification.model_validate_json(raw)
    except ValidationError as error:
        final_error = error.errors()[0]
        LOG.error("rung=4 status=fail err=%s loc=%s", final_error["type"], final_error["loc"])
        raise
    LOG.info("rung=4 status=ok final Together attempt")
    return result


def main() -> None:
    client = client_from_environment()
    for query in TESTS:
        result = classify_with_ladder(client, query)
        print(f"FINAL: {query} -> {result.model_dump_json()}")


if __name__ == "__main__":
    main()