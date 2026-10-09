"""Exercise 1: compare OpenAI and Anthropic schema wrapper formats.

This is a local schema exercise, so it needs no API key. Install Pydantic with
`python -m pip install pydantic` if it is not already available. It does not import
any other exercise file.

Lesson: the data contract is the same Pydantic JSON Schema; each provider wraps it in
its own request format. Keep the inner schema identical and adapt only the wrapper.
"""

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LoanIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purpose: Literal["home", "car", "personal", "business"]
    amount_usd: int = Field(gt=0, le=10_000_000)
    tenure_months: int = Field(ge=6, le=360)
    confidence: float = Field(ge=0.0, le=1.0)


def main() -> None:
    schema = LoanIntent.model_json_schema()
    openai_payload = {
        "type": "json_schema",
        "json_schema": {"name": "LoanIntent", "schema": schema, "strict": True},
    }
    anthropic_payload = {
        "name": "submit_loan_intent",
        "description": "Submit the parsed loan intent",
        "input_schema": schema,
    }

    print("=== OpenAI response_format wrapper ===")
    print(json.dumps(openai_payload, indent=2))
    print("\n=== Anthropic tool wrapper ===")
    print(json.dumps(anthropic_payload, indent=2))
    same_schema = openai_payload["json_schema"]["schema"] == anthropic_payload["input_schema"]
    print("\nWrapper differences:")
    print("- OpenAI: response_format.json_schema with a strict flag.")
    print("- Anthropic: tools[] entry with a name, required description, and input_schema.")
    print("- Inner JSON Schema identical:", same_schema)
    assert same_schema


if __name__ == "__main__":
    main()