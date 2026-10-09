"""Exercise 6: six-action Stripe classifier with validation and PII masking.

Run independently with `python -m pip install openai pydantic` and
TOGETHER_STUDY_API_KEY set. Uses openai/gpt-oss-120b through Together. The synthetic
snapshot is embedded; this script does not need output from another exercise.

Lesson: discriminated unions constrain action-specific fields; validate every response,
mask PII before sending prompts, and use snapshot errors to find schema/prompt drift.
The included 36 cases are a compact worked slice; the grading rubric calls for 50+.
"""

import json
import os
import re
from collections import Counter
from datetime import date
from typing import Annotated, Literal, Union

from openai import OpenAI
from pydantic import AfterValidator, BaseModel, ConfigDict, Field


MODEL = "openai/gpt-oss-120b"


def strip_pii(text: str) -> str:
    text = re.sub(r"\b\d{9}\b", "XXXXXXXXX", text)
    return re.sub(r"\b[A-Z]\d{8}\b", "XXXXXXXXX", text)


MaskedStr = Annotated[str, AfterValidator(strip_pii)]


class RefundAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["refund"]
    payment_id: str = Field(pattern=r"^pay_[A-Za-z0-9]{10,16}$")
    amount_usd: int = Field(gt=0, le=10_000_000)


class KYCAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["kyc"]
    doc_type: Literal["ssn", "ein", "tax_id", "bank"]
    merchant_id: str = Field(pattern=r"^merch_[A-Za-z0-9]{6,12}$")


class PaymentAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["payment"]
    payment_id: str = Field(pattern=r"^pay_[A-Za-z0-9]{10,16}$")
    issue: Literal["failed", "pending", "duplicate", "amount_mismatch"]


class SettlementAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["settlement"]
    cycle_date: date
    issue: Literal["delayed", "missing", "partial", "reconcile"]


class EscalateAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["escalate"]
    reason: Annotated[MaskedStr, Field(min_length=4, max_length=500)]
    priority: Literal["low", "medium", "high"]


class InquireAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["inquire"]
    topic: Literal["pricing", "onboarding", "limits", "integration", "other"]


Action = Annotated[
    Union[RefundAction, KYCAction, PaymentAction, SettlementAction, EscalateAction, InquireAction],
    Field(discriminator="type"),
]


class AgentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Action


SYSTEM = (
    "Classify the Stripe merchant message into one action: refund, kyc, payment, "
    "settlement, escalate, inquire. Return only the required structured action. "
    "Use synthetic identifiers as supplied; never repeat personal identity numbers."
)
SNAPSHOT = [
    ("procesa reembolso de pay_29QwErTy12, 1500 dollars", "refund"),
    ("haz refund de pay_ZZ99XX1234, el customer pago dos veces", "refund"),
    ("necesito refund de pay_AA11BB22CC por 85 dolares", "refund"),
    ("quiero reembolso del payment pay_BB22CC33DD, 40 dollars", "refund"),
    ("refund pay_CC33DD44EE de 250, por favor", "refund"),
    ("regresa 19 dolares del pago pay_DD44EE55FF", "refund"),
    ("subir docs KYC de merch_ABC123", "kyc"),
    ("SSN verification falla para merch_XY9911", "kyc"),
    ("verifica identidad merchant merch_QWERTY", "kyc"),
    ("actualizar tax_id de merch_ASDFGH", "kyc"),
    ("documento bancario pendiente merch_ZXCVBN", "kyc"),
    ("no puedo completar KYC merch_HJKL12", "kyc"),
    ("payment pay_AA11BB22CC fallo pero cobraron", "payment"),
    ("charge de pay_PP88QQ77RR aparece pending", "payment"),
    ("payment pay_KK22LL33MM fue declined", "payment"),
    ("customer charged twice on pay_NN44OO55PP", "payment"),
    ("el cobro de pay_RR66SS77TT tiene amount mismatch", "payment"),
    ("transaction pay_UU88VV99WW no aparece", "payment"),
    ("settlement del 2026-05-18 no llego", "settlement"),
    ("payout del ciclo 2026-05-19 esta delayed", "settlement"),
    ("falta settlement del 2026-05-20", "settlement"),
    ("reconcile mi payout del 2026-05-21", "settlement"),
    ("partial settlement para el ciclo 2026-05-22", "settlement"),
    ("settlement payout missing del 2026-05-23", "settlement"),
    ("escala prioridad alta, sospecha de fraude", "escalate"),
    ("actividad no autorizada en mi merchant account", "escalate"),
    ("fraud alert, bloquea y escala", "escalate"),
    ("queja urgente por account hack, prioridad high", "escalate"),
    ("customer reporta unauthorized charge", "escalate"),
    ("possible stolen credentials, escalate please", "escalate"),
    ("cuales son los pricing limits para international cards", "inquire"),
    ("como funciona onboarding de un nuevo merchant", "inquire"),
    ("que integration options estan disponibles", "inquire"),
    ("donde veo los limites de pagos", "inquire"),
    ("necesito informacion general sobre Stripe", "inquire"),
    ("how do I integrate checkout?", "inquire"),
]


def client_from_environment() -> OpenAI:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set TOGETHER_STUDY_API_KEY before running this exercise.")
    return OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")


def classify(client: OpenAI, query: str) -> AgentResponse:
    safe_query = strip_pii(query)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": safe_query}],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "AgentResponse", "schema": AgentResponse.model_json_schema(), "strict": True},
        },
        max_tokens=300,
    )
    return AgentResponse.model_validate_json(response.choices[0].message.content or "")


def main() -> None:
    client = client_from_environment()
    counts: Counter = Counter()
    correct = 0
    for query, expected in SNAPSHOT:
        result = classify(client, query)
        predicted = result.action.type
        counts[(expected, predicted)] += 1
        correct += predicted == expected
        print(f"expected={expected:10s} predicted={predicted:10s} query={query}")

    print(f"\nSnapshot accuracy: {correct}/{len(SNAPSHOT)} = {correct / len(SNAPSHOT):.1%}")
    print("Confusion (expected -> predicted):")
    for (expected, predicted), count in sorted(counts.items()):
        suffix = " <-- miss" if expected != predicted else ""
        print(f"  {expected:10s} -> {predicted:10s} x{count}{suffix}")
    print("PII masking check:", strip_pii("SSN 234567890 passport A12345678"))


if __name__ == "__main__":
    main()