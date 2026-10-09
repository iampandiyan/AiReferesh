"""Exercise 3: compare JSON-schema output with forced function-tool output.

Run independently with `python -m pip install openai pydantic` and
TOGETHER_STUDY_API_KEY set in the environment. Uses Together's OpenAI-compatible API
and openai/gpt-oss-120b. The code-mixed cases are embedded here.

Lesson: a discriminated union gives each action a clear shape. Compare outputs from
two structured-output interfaces, then validate both locally before scoring agreement.
"""

import json
import os
import re
from typing import Annotated, Literal, Union

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field


MODEL = "openai/gpt-oss-120b"
MAX_COMPLETION_TOKENS = 1200


class LoanAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["loan"]
    purpose: Literal["home", "car", "personal", "business"]
    amount_usd: int = Field(gt=0, le=10_000_000)
    customer_id: str = Field(pattern=r"^TC\d{8}$")


class KYCAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["kyc"]
    doc_type: Literal["ssn", "passport"]
    customer_id: str = Field(pattern=r"^TC\d{8}$")


class EscalateAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["escalate"]
    reason: str = Field(min_length=4)
    priority: Literal["low", "medium", "high"]


class InquireAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["inquire"]
    topic: Literal["interest_rate", "eligibility", "documents", "tenure", "other"]


Action = Annotated[
    Union[LoanAction, KYCAction, EscalateAction, InquireAction],
    Field(discriminator="type"),
]


class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Action


QUERIES = [
    ("necesito un prestamo hipotecario de $6,000, TC12345678", "loan"),
    ("quiero verificar mi SSN, ID TC55554444", "kyc"),
    ("cual es la elegibilidad para prestamo personal?", "inquire"),
    ("el agente me dio info incorrecta, escala prioridad alta", "escalate"),
    ("actualizar mi pasaporte, TC11223344", "kyc"),
    ("cual es el plazo maximo?", "inquire"),
    ("prestamo personal de $2,400, TC22334455", "loan"),
    ("cual es la tasa de interes del prestamo hipotecario?", "inquire"),
    ("verificar pasaporte TC66778899", "kyc"),
    ("prestamo de negocio $60,000, TC77889900", "loan"),
    ("que documentos necesito?", "inquire"),
    ("escala, prioridad baja, quiero callback", "escalate"),
    ("prestamo de auto $9,600, TC44556677", "loan"),
    ("sirve el SSN para el KYC?", "kyc"),
    ("quiero revisar mi elegibilidad", "inquire"),
    ("prestamo hipotecario $30,000, TC88990011", "loan"),
    ("verificar mi pasaporte, TC99001122", "kyc"),
    ("escala media, problema de settlement", "escalate"),
    ("es posible un prestamo adicional?", "inquire"),
    ("prestamo personal $3,600, TC33445566", "loan"),
]
SYSTEM = (
    "Classify a code-mixed Meridian Capital query into exactly one action. "
    "Return an object with this shape: {\"action\": {\"type\": \"loan|kyc|escalate|inquire\", ...}}. "
    "The action must be an object, never a string. Put every action field inside action. "
    "Use only the exact type labels loan, kyc, escalate, or inquire. Amounts are USD."
)
TOOL = [{
    "type": "function",
    "function": {
        "name": "submit_classification",
        "description": "Return a validated Meridian Capital action.",
        "parameters": Classification.model_json_schema(),
    },
}]


def client_from_environment() -> OpenAI:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set TOGETHER_STUDY_API_KEY before running this exercise.")
    return OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")


def classify_json_mode(client: OpenAI, query: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": query}],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "Classification",
                "schema": Classification.model_json_schema(),
                "strict": True,
            },
        },
        max_tokens=MAX_COMPLETION_TOKENS,
    )
    choice = response.choices[0]
    if choice.finish_reason == "length":
        raise RuntimeError(
            f"JSON-mode response was truncated at {MAX_COMPLETION_TOKENS} tokens; "
            "increase MAX_COMPLETION_TOKENS."
        )
    result = Classification.model_validate_json(choice.message.content or "")
    return result.action.type


def classify_tool_mode(client: OpenAI, query: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": query}],
        tools=TOOL,
        tool_choice={"type": "function", "function": {"name": "submit_classification"}},
        max_tokens=MAX_COMPLETION_TOKENS,
    )
    choice = response.choices[0]
    if choice.finish_reason == "length":
        raise RuntimeError(
            f"Tool-mode response was truncated at {MAX_COMPLETION_TOKENS} tokens; "
            "increase MAX_COMPLETION_TOKENS."
        )
    calls = choice.message.tool_calls or []
    if not calls:
        raise ValueError("Model did not return the required classification tool call.")
    result = Classification.model_validate(json.loads(calls[0].function.arguments))
    return result.action.type


def main() -> None:
    client = client_from_environment()
    print(f"Comparing JSON mode and function-tool mode with {MODEL}\n")
    print(f"{'query':54s} | {'JSON':10s} | {'tool':10s} | agree")
    print("-" * 91)
    agreements = 0
    json_correct = 0
    tool_correct = 0
    for query, expected in QUERIES:
        json_action = classify_json_mode(client, query)
        tool_action = classify_tool_mode(client, query)
        same = json_action == tool_action
        agreements += same
        json_correct += json_action == expected
        tool_correct += tool_action == expected
        print(f"{query[:54]:54s} | {json_action:10s} | {tool_action:10s} | {'Y' if same else 'N'}")
    print(f"\nInterface agreement: {agreements}/{len(QUERIES)}")
    print(f"Accuracy vs embedded labels: JSON mode {json_correct}/{len(QUERIES)}, "
          f"tool mode {tool_correct}/{len(QUERIES)}")
    print("Agreement compares two interfaces using the same model, not independent providers.")


if __name__ == "__main__":
    main()