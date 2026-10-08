import os
from pathlib import Path

from dotenv import load_dotenv
from together import Together

load_dotenv(Path(__file__).resolve().with_name(".env"))
api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
if not api_key:
    raise RuntimeError("TOGETHER_STUDY_API_KEY is not set in the adjacent .env file.")

client = Together(api_key=api_key)

PROMPT_V0 = "Classify this Stripe customer message as refund, not_refund, or escalate."

PROMPT_V1 = """
[SYSTEM]
You are a classifier for Stripe merchant-support inbound messages. Use US English spelling. Never invent customer details.

[ROLE]
Refund-intent triage agent. You only classify; you do not draft replies.

[CONTEXT]
Stripe merchants raise tickets in code-mixed, Spanish, and English. Refund windows are 5 business days from payment.

[INSTRUCTIONS]
1. Read the customer message.
2. Decide one of: refund, not_refund, escalate.
3. If the message mentions an unauthorized charge or fraud, always escalate.
4. Respond only with the JSON shape in [FORMAT]. No prose.

[EXAMPLES]
Input: "Oye me cobraron y el order se cancelo, quiero mi refund"
Output: {"intent": "refund", "confidence": 0.92}

Input: "Cuando llega el order?"
Output: {"intent": "not_refund", "confidence": 0.88}

Input: "Mi card tiene 4 unauthorized transactions"
Output: {"intent": "escalate", "confidence": 0.99}

[FORMAT]
Return ONLY: {"intent": "refund|not_refund|escalate", "confidence": 0.0-1.0}
"""

sections = ["[SYSTEM]", "[ROLE]", "[CONTEXT]", "[INSTRUCTIONS]", "[EXAMPLES]", "[FORMAT]"]
assert all(section in PROMPT_V1 for section in sections)
assert PROMPT_V1.count("refund|not_refund|escalate") == 1
instructions = PROMPT_V1.split("[INSTRUCTIONS]")[1].split("[EXAMPLES]")[0]
assert "always escalate" in instructions

customer_message = "!@#$%^&*((()))"
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": PROMPT_V1},
        {"role": "user", "content": customer_message},
    ],
)
print(PROMPT_V1)
print("\nModel classification:")
print("Customer Message:",customer_message)
print(response.choices[0].message.content)
print("OK - all six sections, format isolation, and fraud escalation rule checked.")