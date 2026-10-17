"""Exercise 7: HyDE with Together chat completions and an honest offline demo.

Run: python exercise_07_hyde_together.py
Optional live mode: set TOGETHER_STUDY_API_KEY, then run this script.
Install the client dependencies with: pip install together python-dotenv

Behavior: uses Together's OpenAI-compatible chat-completions endpoint with model
openai/gpt-oss-120b to draft a hypothetical answer. Without the key it labels
and uses a deterministic offline draft. The key is loaded from a .env file next
to this script or from the process environment.

Lesson: HyDE embeds a hypothetical answer rather than the short query. It can
help paraphrases, but generated details can also hallucinate and hurt retrieval.
Compare per query and include the additional model-call cost.
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from together import Together


load_dotenv(Path(__file__).resolve().with_name(".env"))

MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "Write a concise hypothetical answer for retrieval. Use only the supplied "
    "question; do not invent regulatory section numbers or claim the answer is verified."
)
PARAPHRASE_QUERIES = [
    ("what rights does a person have over their information", "data subject"),
    ("how can I move my personal information", "portability"),
    ("can a customer ask for their records to be removed", "erasure"),
]
DOCUMENTS = [
    "GDPR gives data subjects rights to access personal data.",
    "Individuals may request erasure of personal information under GDPR.",
    "The right to portability lets people transfer their personal data.",
    "AML bulletin 4.5.2 describes beneficial ownership checks.",
]


def together_chat(system_prompt, customer_message):
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        return None
    client = Together(api_key=api_key)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": customer_message},
        ],
    )
    return response.choices[0].message.content or ""


def draft_hypothesis(query):
    customer_message = f"Draft a 2-3 sentence hypothetical answer to this query: {query}"
    response = together_chat(PROMPT_V1, customer_message)
    if response is not None:
        return response, "Together live"
    return (
        f"A data subject may have rights relating to {query}, including access, "
        "correction, erasure, and portability of personal information.",
        "offline illustrative draft (no API key)",
    )


def words(text):
    return set(re.findall(r"[a-z]+", text.lower()))


def retrieve(text, k=3):
    query_terms = words(text)
    ranked = sorted(
        enumerate(DOCUMENTS),
        key=lambda item: (-len(query_terms & words(item[1])), item[0]),
    )
    return [doc for _, doc in ranked[:k]]


def main():
    wins = ties = losses = 0
    for query, gold in PARAPHRASE_QUERIES:
        draft, mode = draft_hypothesis(query)
        direct_hit = any(gold in doc.lower() for doc in retrieve(query))
        hyde_hit = any(gold in doc.lower() for doc in retrieve(draft))
        if hyde_hit and not direct_hit:
            wins += 1
            result = "WIN"
        elif direct_hit and not hyde_hit:
            losses += 1
            result = "LOSS"
        else:
            ties += 1
            result = "TIE"
        print(f"\nQuery: {query}\nMode: {mode}\nHyDE draft: {draft}")
        print(f"Direct hit={direct_hit}; HyDE hit={hyde_hit}: {result}")

    print(f"\nSummary: {wins} win / {ties} tie / {losses} loss")
    print("Live Together calls use model openai/gpt-oss-120b; API usage may incur charges.")
    print("HyDE is most useful for hard paraphrases; on exact identifiers the draft can dilute the literal token.")


if __name__ == "__main__":
    main()
"""
Mode: Together live
HyDE draft: A person typically has the right to access the personal information held about them, to request corrections, and to ask that it be deleted or limited in use. They may also be entitled to receive clear notice about how their data is processed, to obtain a portable copy, and to object to certain types of processing. These rights aim to give individuals control over their own information.
Direct hit=True; HyDE hit=True: TIE

Query: how can I move my personal information
Mode: Together live
HyDE draft: You can typically export or transfer your personal information by using the data‑download or portability tools provided in your account settings, or by submitting a formal request to the service’s support team. Follow the provider’s instructions for selecting the data you want, choosing a format (such as CSV or JSON), and specifying the destination (e.g., a new platform or a secure storage location). If the service does not offer a self‑service option, request a data‑transfer in writing and provide the necessary details for the receiving party.
Direct hit=True; HyDE hit=True: TIE

Query: can a customer ask for their records to be removed
Mode: Together live
HyDE draft: Yes, a customer can typically request that an organization delete or remove their personal records, subject to applicable privacy laws and the company’s data‑retention policies. Whether the request can be fully honored may depend on legal requirements to keep certain information for a prescribed period (e.g., tax, fraud‑prevention, or contractual obligations). If no such retention obligation exists, the organization should comply with the deletion request in a timely manner.
Direct hit=True; HyDE hit=True: TIE

Summary: 0 win / 3 tie / 0 loss
Live Together calls use model openai/gpt-oss-120b; API usage may incur charges.
HyDE is most useful for hard paraphrases; on exact identifiers the draft can dilute the literal token.
"""