"""Exercise 1: add three code-mixed examples to an intent classifier.

Run independently: install the OpenAI SDK with `python -m pip install openai`,
set TOGETHER_STUDY_API_KEY, then run this file. No other exercise files are used.

Lesson: few-shot examples teach the boundary between labels; varied, representative
examples are more useful than several paraphrases of the same intent. Inputs here
use synthetic identifiers only.
"""

import json
import os
import re

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
LABELS = {"refund", "payment", "kyc", "escalate", "inquire"}

PROMPT_ZERO = """You are a Stripe merchant-support intent classifier.
Classify the message; do not draft a reply.
Choose exactly one: refund | payment | kyc | escalate | inquire.
Fraud or unauthorized charges must be escalated.
Return only JSON: {"intent": "...", "confidence": 0.0}.
"""

PROMPT_FEW = PROMPT_ZERO + """
[EXAMPLES]
Input: "Oye pay_TEST29Qw cuando llega mi refund, ya son 5 dias"
Output: {"intent": "refund", "confidence": 0.93}

Input: "la verificacion esta pendiente, merch_8821 no puede activar payouts"
Output: {"intent": "kyc", "confidence": 0.91}

Input: "en mi account hay 4 unauthorized swipes, parece fraud"
Output: {"intent": "escalate", "confidence": 0.97}

[FORMAT]
Return only {"intent": "refund|payment|kyc|escalate|inquire", "confidence": 0.0}.
"""


def parse_object(text: str) -> dict:
    match = re.search(r"\{.*?\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Model did not return a JSON object: {text!r}")
    return json.loads(match.group(0))


def main() -> None:
    examples = PROMPT_FEW.split("[EXAMPLES]")[1].split("[FORMAT]")[0]
    example_intents = re.findall(r'"intent"\s*:\s*"([a-z_]+)"', examples)
    assert len(example_intents) == 3 and len(set(example_intents)) == 3
    assert set(example_intents) == {"refund", "kyc", "escalate"}

    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")

    customer_message = "Oye pay_TEST73Ab, necesito saber cuando llega mi refund"
    customer_message1 = "give me documents"
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PROMPT_FEW},
            {"role": "user", "content": customer_message1},
        ],
        response_format={"type": "json_object"},
    )
    result = parse_object(response.choices[0].message.content or "")
    if result.get("intent") not in LABELS:
        raise ValueError(f"Unexpected intent: {result!r}")

    print("Message:", customer_message)
    print("Classification:", json.dumps(result, ensure_ascii=False))
    print("Lesson: use examples from distinct classes, then validate the output contract.")


if __name__ == "__main__":
    main()