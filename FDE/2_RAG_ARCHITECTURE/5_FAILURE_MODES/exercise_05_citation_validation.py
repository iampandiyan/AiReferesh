"""Exercise 5: Validate citations, retry invalid answers, and fail closed.

Run: python exercise_05_citation_validation.py

Behavior: Checks strict JSON answers against retrieved chunk ids and retries
invalid citations up to twice. With TOGETHER_STUDY_API_KEY it calls
openai/gpt-oss-120b. Offline, deterministic sample responses exercise both a
valid answer and persistent hallucinated citations without network access.

Lesson: A model's citation text is not proof that a source was retrieved.
Validate every id against the actual retrieved set, provide explicit feedback,
and refuse to return an unsupported answer when retries are exhausted.
"""

import json
import os
from dataclasses import dataclass, field


MODEL = "openai/gpt-oss-120b"
SYSTEM = """Answer compliance questions using only the supplied chunks.
Return strict JSON: {"answer": "<text>", "citations": ["<chunk-id>", ...]}.
Every answer claim must be supported by a supplied chunk id. Never invent ids.
If context is insufficient, return {"answer": "INSUFFICIENT_CONTEXT", "citations": []}."""
OFFLINE_RESPONSES = {
    "What erasure rights does GDPR give?": [
        {"answer": "A data subject may request erasure when consent is withdrawn.", "citations": ["gdpr-12"]},
    ],
    "What is the GDPR penalty for non-erasure?": [
        {"answer": "The penalty is described in [gdpr-99].", "citations": ["gdpr-99"]},
        {"answer": "The penalty is described in [gdpr-99].", "citations": ["gdpr-99"]},
        {"answer": "The penalty is described in [gdpr-99].", "citations": ["gdpr-99"]},
    ],
}


@dataclass
class Verdict:
    ok: bool
    answer: str = ""
    citations: list[str] = field(default_factory=list)
    invalid: list[str] = field(default_factory=list)
    attempts: int = 0


def together_chat(system_prompt, customer_message):
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        return None

    from together import Together

    client = Together(api_key=api_key)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": customer_message},
        ],
        max_tokens=400,
    )
    return response.choices[0].message.content or ""


def ask_once(query, retrieved, feedback="", offline_attempt=0):
    chunks = "\n".join(f"<chunk id='{chunk_id}'>{text}</chunk>" for chunk_id, text in retrieved)
    user_message = f"<chunks>\n{chunks}\n</chunks>\n\nQuestion: {query}"
    if feedback:
        user_message += f"\n\nPrevious-attempt feedback: {feedback}"

    response = together_chat(SYSTEM, user_message)
    if response is not None:
        try:
            value = json.loads(response)
        except json.JSONDecodeError as error:
            raise ValueError("Together response was not valid JSON.") from error
        if not isinstance(value, dict):
            raise ValueError("Together response must be a JSON object.")
        return value

    samples = OFFLINE_RESPONSES[query]
    return samples[min(offline_attempt, len(samples) - 1)]


def answer_with_validation(query, retrieved, max_retries=2):
    valid_ids = {chunk_id for chunk_id, _ in retrieved}
    feedback = ""
    invalid = []
    for attempt in range(max_retries + 1):
        response = ask_once(query, retrieved, feedback, offline_attempt=attempt)
        answer = response.get("answer", "")
        citations = response.get("citations", [])
        if not isinstance(answer, str) or not isinstance(citations, list) or not all(
            isinstance(citation, str) for citation in citations
        ):
            raise ValueError("Answer must be a string and citations must be a list of strings.")
        if answer == "INSUFFICIENT_CONTEXT":
            return Verdict(ok=True, answer=answer, citations=[], attempts=attempt + 1)

        invalid = [citation for citation in citations if citation not in valid_ids]
        if not invalid:
            return Verdict(ok=True, answer=answer, citations=citations, attempts=attempt + 1)
        feedback = (
            f"Invalid citation(s): {invalid}. Use only retrieved ids: "
            f"{sorted(valid_ids)}. If unsupported, return INSUFFICIENT_CONTEXT."
        )

    return Verdict(
        ok=False,
        answer="FAIL_CLOSED_HALLUCINATION",
        invalid=invalid,
        attempts=max_retries + 1,
    )


def main():
    retrieved = [
        ("gdpr-12", "A data subject may request erasure when consent is withdrawn."),
        ("gdpr-13", "The grievance officer contact and response window are specified."),
    ]
    valid = answer_with_validation("What erasure rights does GDPR give?", retrieved)
    print("Happy path:", valid)
    assert valid.ok and valid.citations == ["gdpr-12"]

    sparse = [("gdpr-13", "The chunk describes a grievance contact and response window.")]
    invalid = answer_with_validation("What is the GDPR penalty for non-erasure?", sparse)
    print("Persistent hallucination:", invalid)
    assert not invalid.ok and invalid.attempts == 3 and invalid.invalid == ["gdpr-99"]
    print(f"\nModel: {MODEL}; Together live mode: {'on' if os.environ.get('TOGETHER_STUDY_API_KEY') else 'off'}")


if __name__ == "__main__":
    main()
