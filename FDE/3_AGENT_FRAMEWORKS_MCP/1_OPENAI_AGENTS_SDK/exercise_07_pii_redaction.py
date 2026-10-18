"""Exercise 7: redact PII before sending support text to the model.

Run independently after installing `openai` and setting TOGETHER_STUDY_API_KEY.
The sample contains synthetic card-shaped and email values only.

Behavior: redaction is performed at the input boundary; only the cleaned ticket
is sent to Together. High-sensitivity tracing is disabled in this example by
not emitting or transmitting application traces.
Lesson: redacting only inside tools is too late if raw input is already logged.
For a DPIA, document who can access provider logs and any trace dashboard, how
long records persist, and the applicable retention/access controls. Together
Chat Completions does not expose the Agents SDK RunConfig tracing switch.
"""

import os
import re

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "You are AcmeCorp support. Answer based only on the redacted ticket text. "
    "Do not ask the customer to repeat any sensitive payment details."
)
CARD_PATTERN = re.compile(r"\b(?:\d[ -]?){13,16}\b")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
NATIONAL_ID_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def redact(text: str) -> str:
    text = CARD_PATTERN.sub("[REDACTED_CARD]", text)
    text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    return NATIONAL_ID_PATTERN.sub("[REDACTED_ID]", text)


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    raw_customer_message = (
        "My card 4111 1111 1111 1111 was double-charged; email me at "
        "mei@acme.example. My ID is 123-45-6789."
    )
    customer_message = redact(raw_customer_message)
    tracing_disabled = True
    if not tracing_disabled:
        raise RuntimeError("This high-sensitivity example must not emit traces.")
    print(f"Redacted message sent to the model: {customer_message}")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PROMPT_V1},
            {"role": "user", "content": customer_message},
        ],
        max_tokens=300,
    )
    print(response.choices[0].message.content or "No response returned.")


if __name__ == "__main__":
    main()
