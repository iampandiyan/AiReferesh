"""Exercise 4: Decompose a comparison into independently grounded sub-queries.

Run: python exercise_04_multi_hop_decomposition.py

Behavior: Uses Together (openai/gpt-oss-120b) to decompose and synthesize when
TOGETHER_STUDY_API_KEY is set. Otherwise, deterministic prompts and a simple
local token-overlap retriever keep the exercise runnable offline. No exercise
file or local dataset is imported.

Lesson: A single retrieval for a multi-entity comparison can overrepresent one
side. Retrieve for each sub-question, inspect which sources were found, and
ground the synthesis in both sides. Token overlap is only a toy retriever.
"""

import json
import os


MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = "Use only the supplied retrieved evidence. Cite its chunk ids inline."
CORPUS = [
    ("gdpr-accountability", "GDPR Art. 5(2): the data controller is accountable for compliance, including AI-driven decisions. Art. 35 requires a DPIA for high-risk processing."),
    ("gdpr-grievance", "GDPR Art. 13: every data controller shall publish a contact point and respond to data-subject requests within about 30 days."),
    ("nist-ai-rmf-confirm", "NIST AI RMF: financial transactions initiated by AI require out-of-band confirmation by the customer or a designated approver."),
    ("nist-ai-rmf-audit", "NIST AI RMF (MANAGE function): AI-system decisions affecting credit shall be auditable; institutions shall log model version, input, output, and human reviewer (if any)."),
    ("nist-ai-rmf-explain", "NIST AI RMF (MEASURE function): model decisions in credit and KYC shall include a human-readable explanation generated at decision time."),
    ("occ-kyc-pep", "OCC KYC bulletin: PEP screening required at onboarding and annually."),
    ("gdpr-consent", "GDPR Art. 6/7: processing of personal data requires consent or another lawful basis enumerated in Art. 6."),
]


def together_chat(system_prompt, customer_message, max_tokens=400):
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
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def decompose(query):
    system_prompt = (
        "Decompose the comparison into 2-3 atomic sub-questions, at least one "
        "for each named framework. Return a JSON list of strings only."
    )
    response = together_chat(system_prompt, f"Query: {query}", max_tokens=250)
    if response is None:
        return [
            "What does GDPR say about AI-system accountability?",
            "What does the NIST AI RMF say about AI-system accountability?",
        ]
    try:
        questions = json.loads(response)
    except json.JSONDecodeError as error:
        raise ValueError("Together decomposition response was not valid JSON.") from error
    if not isinstance(questions, list) or not all(isinstance(item, str) for item in questions):
        raise ValueError("Together decomposition must be a JSON list of question strings.")
    if len(questions) < 2:
        raise ValueError("Together decomposition must return at least two sub-questions.")
    return questions


def retrieve_stub(sub_question, limit=3):
    """Rank corpus text by simple case-insensitive token overlap."""
    terms = set(sub_question.lower().split())
    scored = [
        (len(terms & set(text.lower().split())), -index, chunk_id, text)
        for index, (chunk_id, text) in enumerate(CORPUS)
    ]
    scored.sort(reverse=True)
    return [(chunk_id, text) for _, _, chunk_id, text in scored[:limit]]


def synthesize(query, contexts):
    blocks = []
    for sub_question, documents in contexts:
        chunks = "\n".join(f"[{chunk_id}] {text}" for chunk_id, text in documents)
        blocks.append(f"Sub-question: {sub_question}\nRetrieved:\n{chunks}")
    payload = "\n\n".join(blocks)
    response = together_chat(
        PROMPT_V1,
        f"{payload}\n\nOriginal comparison: {query}",
        max_tokens=500,
    )
    if response is not None:
        return response

    gdpr_ids = sorted({chunk_id for _, docs in contexts for chunk_id, _ in docs if chunk_id.startswith("gdpr-")})
    nist_ids = sorted({chunk_id for _, docs in contexts for chunk_id, _ in docs if chunk_id.startswith("nist-")})
    return (
        "Offline illustrative synthesis: GDPR evidence concerns controller "
        f"accountability ({', '.join(gdpr_ids) or 'no GDPR chunk retrieved'}); "
        "NIST AI RMF evidence concerns auditable decisions and controls "
        f"({', '.join(nist_ids) or 'no NIST chunk retrieved'})."
    )


def main():
    query = "Compare GDPR and the NIST AI RMF on AI-system accountability obligations."
    sub_questions = decompose(query)
    contexts = [(question, retrieve_stub(question)) for question in sub_questions]
    print("Sub-questions:")
    for question, documents in contexts:
        print(f"\n- {question}\n  Retrieved: {[chunk_id for chunk_id, _ in documents]}")
    cited_frameworks = {
        "GDPR": any(chunk_id.startswith("gdpr-") for _, docs in contexts for chunk_id, _ in docs),
        "NIST AI RMF": any(chunk_id.startswith("nist-") for _, docs in contexts for chunk_id, _ in docs),
    }
    print(f"\nBoth frameworks retrieved: {all(cited_frameworks.values())}")
    print("\nFinal answer:\n" + synthesize(query, contexts))
    print(f"\nModel: {MODEL}; Together live mode: {'on' if os.environ.get('TOGETHER_STUDY_API_KEY') else 'off'}")


if __name__ == "__main__":
    main()
