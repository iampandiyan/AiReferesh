import os
from pathlib import Path

from dotenv import load_dotenv
from together import Together

load_dotenv(Path(__file__).resolve().with_name(".env"))
api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
if not api_key:
    raise RuntimeError("TOGETHER_STUDY_API_KEY is not set in the adjacent .env file.")

client = Together(api_key=api_key)

BROKEN = """
[SYSTEM]
You are a Stripe merchant-support agent.

[ROLE]
You answer merchant tickets about payments, refunds, KYC, and settlements.

[CONTEXT]
Stripe processes payments for 10M+ merchants. The platform supports cards, bank transfers, and wallets. Settlement happens on T+2 by default. Merchants often write in code-mixed Spanish and English. We must respond in the same language and script the merchant used so the reply is intelligible to non-English-comfortable merchants. KYC is mandatory under regulator guidelines. Refund windows are 5 business days from payment time.

[INSTRUCTIONS]
1. Read the merchant message.
2. Identify the issue type.
3. Draft a 2-3 sentence reply.

[EXAMPLES]
Input: "Oye el settlement no llego ni despues de T+2"
Output: "Estamos revisando tu settlement, update en 2 horas."

[FORMAT]
Reply with 2-3 sentences only. No JSON.
"""

FIXED = """
[SYSTEM]
You are a Stripe merchant-support agent.

[ROLE]
You answer merchant tickets about payments, refunds, KYC, and settlements.

[CONTEXT]
Stripe processes payments for 10M+ merchants. The platform supports cards, bank transfers, and wallets. Settlement happens on T+2 by default. KYC is mandatory under regulator guidelines. Refund windows are 5 business days from payment time.

[INSTRUCTIONS]
1. Read the merchant message.
2. Identify the issue type.
3. Draft a 2-3 sentence reply.
4. ALWAYS reply in the exact language the merchant used. If code-mixed Spanish-English, mirror code-mixed. If pure Spanish, reply in Spanish. If English, reply in US English.

[EXAMPLES]
Input: "Oye el settlement no llego ni despues de T+2"
Output: "Estamos revisando tu settlement, update en 2 horas."

Reminder: reply in the merchant's language. code-mixed in -> code-mixed out.

[FORMAT]
Reply with 2-3 sentences only. No JSON.
"""

context = FIXED.split("[CONTEXT]")[1].split("[INSTRUCTIONS]")[0]
instructions = FIXED.split("[INSTRUCTIONS]")[1].split("[EXAMPLES]")[0]
example_section = FIXED.split("[EXAMPLES]")[1].split("[FORMAT]")[0]
assert "respond in the same language" not in context
assert "ALWAYS reply in the exact language" in instructions
assert "Reminder: reply in the merchant's language" in example_section

message = "Oye el settlement no llego ni despues de T+2"
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": FIXED},
        {"role": "user", "content": message},
    ],
)
print("Failure mode: the language rule is distant in CONTEXT, so the model may neglect it on short queries.")
print("\nFixed prompt response:")
print(response.choices[0].message.content)
print("OK - the language rule is in INSTRUCTIONS and repeated immediately before FORMAT.")