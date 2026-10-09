"""Exercise 1: one tool call and the complete tool-result round trip.

Run independently with `python -m pip install openai` and TOGETHER_STUDY_API_KEY set.
Uses the Together OpenAI-compatible API and openai/gpt-oss-120b. All payment IDs
and amounts are synthetic; no real payment system is accessed.

Lesson: the model requests a tool; Python executes it and sends a matching tool result
back using the call ID. The model then uses that result to write its final response.
"""

import json
import os
import time

from openai import APIConnectionError, APIStatusError, OpenAI


MODEL = "openai/gpt-oss-120b"
PAYMENTS = {
    "pay_TEST_4421": {"status": "captured", "amount_usd": 4500},
    "pay_TEST_9981": {"status": "refunded", "amount_usd": 1200},
}
TOOLS = [{
    "type": "function",
    "function": {
        "name": "lookup_payment",
        "description": "Look up a synthetic payment's status and amount. Call for payment-status questions.",
        "parameters": {
            "type": "object",
            "properties": {"payment_id": {"type": "string"}},
            "required": ["payment_id"],
            "additionalProperties": False,
        },
    },
}]
SYSTEM = "Answer payment-status questions using lookup_payment. Do not guess payment facts."


def create_completion_with_retry(client: OpenAI, **kwargs):
    for attempt in range(4):
        try:
            return client.chat.completions.create(**kwargs)
        except APIStatusError as error:
            retryable = error.status_code == 429 or error.status_code >= 500
            if not retryable or attempt == 3:
                request_id = getattr(error, "request_id", None)
                detail = f" Together request ID: {request_id}." if request_id else ""
                raise RuntimeError(
                    f"Together API request failed with HTTP {error.status_code}.{detail} "
                    "If this is a 5xx error, retry later and include the request ID in a support report."
                ) from error
        except APIConnectionError:
            if attempt == 3:
                raise
        time.sleep(2 ** attempt)


def lookup_payment(payment_id: str) -> dict:
    return PAYMENTS.get(payment_id, {"status": "not_found", "amount_usd": 0})


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    messages = [{"role": "user", "content": "What's the status of pay_TEST_4421?"}]

    first = create_completion_with_retry(
        client,
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM}, *messages],
        tools=TOOLS,
        tool_choice={"type": "function", "function": {"name": "lookup_payment"}},
        max_tokens=500,
    )
    assistant_message = first.choices[0].message
    calls = assistant_message.tool_calls or []
    if not calls:
        raise RuntimeError("Model did not request the required lookup_payment tool.")

    messages.append(assistant_message.model_dump(exclude_none=True))
    for call in calls:
        if call.function.name != "lookup_payment":
            result = {"error": "unsupported tool"}
        else:
            arguments = json.loads(call.function.arguments)
            result = lookup_payment(arguments["payment_id"])
        messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})

    final = create_completion_with_retry(
        client,
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM}, *messages],
        max_tokens=300,
    )
    print(final.choices[0].message.content or "No final response returned.")


if __name__ == "__main__":
    main()

"""
analysisThe user asks: "What's the status of pay_TEST_4421?" We have called lookup_payment with payment_id "pay_TEST_4421". The result: status "captured", amount_usd 4500. We need to answer the user's question, providing status (and possibly amount?) The instruction says answer payment-status questions using lookup_payment. Do not guess. So we can respond: The payment is captured. Optionally include amount: $4,500. Provide concise answer.assistantfinalThe payment **pay_TEST_4421** has a status of **captured** (amount $4,500).
"""