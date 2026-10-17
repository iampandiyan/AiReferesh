"""Exercise 1: score a small RAG set with four Ragas metrics.

Run with `python exercise_01_ragas_metrics.py`. For live evaluation, install
`ragas==0.4.3`, `langchain-openai`, and `langchain-community==0.3.31`, then set
TOGETHER_STUDY_API_KEY. Ragas 0.4.3 imports the legacy Community Vertex AI
module during startup, so pin Community to a release that still provides it.
Without a key, this script prints an explicitly labelled illustrative scorecard.

Behavior: evaluates one correct answer, one hallucination, and one wrong-context
answer. Live results come from Together's OpenAI-compatible endpoint and vary.

Lesson: inspect row-level metrics. Faithfulness should expose unsupported claims;
context precision and recall should expose irrelevant or missing retrieved evidence.
"""

import os


MODEL = "openai/gpt-oss-120b"
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
ROWS = [
    {
        "user_input": "What is AcmeCorp's retention window for KYC records?",
        "response": (
            "AcmeCorp retains KYC records for 5 years after account closure "
            "(Data-Protection Standard clause 4)."
        ),
        "retrieved_contexts": [
            "AcmeCorp Data-Protection Standard clause 4: KYC records are retained "
            "for 5 years after account closure."
        ],
        "reference": (
            "Per AcmeCorp Data-Protection Standard clause 4, KYC records are "
            "retained for 5 years after account closure."
        ),
    },
    {
        "user_input": "What is AcmeCorp's retention window for KYC records?",
        "response": "AcmeCorp retains KYC records for 10 years after account closure.",
        "retrieved_contexts": [
            "AcmeCorp Data-Protection Standard clause 4: KYC records are retained "
            "for 5 years after account closure."
        ],
        "reference": (
            "Per AcmeCorp Data-Protection Standard clause 4, KYC records are "
            "retained for 5 years after account closure."
        ),
    },
    {
        "user_input": "What is AcmeCorp's retention window for KYC records?",
        "response": "I could not find the KYC retention window in the retrieved policy text.",
        "retrieved_contexts": [
            "AcmeCorp Refund Policy Section 3.2: refund disputes are resolved "
            "within 10 working days."
        ],
        "reference": (
            "Per AcmeCorp Data-Protection Standard clause 4, KYC records are "
            "retained for 5 years after account closure."
        ),
    },
]
NOTES = ("correct", "hallucinated (10 years)", "wrong context")
OFFLINE_SCORES = [
    {
        "faithfulness": 0.98,
        "answer_relevancy": 0.96,
        "context_precision": 1.00,
        "context_recall": 1.00,
    },
    {
        "faithfulness": 0.30,
        "answer_relevancy": 0.92,
        "context_precision": 1.00,
        "context_recall": 1.00,
    },
    {
        "faithfulness": 0.90,
        "answer_relevancy": 0.40,
        "context_precision": 0.00,
        "context_recall": 0.00,
    },
]


def evaluate_with_together():
    """Run the Ragas 0.4.x metrics through Together's OpenAI-compatible API."""
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        return None

    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas import EvaluationDataset, evaluate
    from ragas.dataset_schema import SingleTurnSample
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        Faithfulness,
        LLMContextPrecisionWithReference,
        LLMContextRecall,
        ResponseRelevancy,
    )

    client = ChatOpenAI(
        model=MODEL,
        api_key=api_key,
        base_url="https://api.together.xyz/v1",
    )
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=api_key,
        base_url="https://api.together.xyz/v1",
    )
    dataset = EvaluationDataset(
        samples=[SingleTurnSample(**row) for row in ROWS]
    )
    return evaluate(
        dataset=dataset,
        metrics=[
            Faithfulness(),
            ResponseRelevancy(),
            LLMContextPrecisionWithReference(),
            LLMContextRecall(),
        ],
        llm=LangchainLLMWrapper(client),
        embeddings=LangchainEmbeddingsWrapper(embeddings),
    )


def main():
    result = evaluate_with_together()
    if result is not None:
        print(f"Mode: Together live Ragas evaluation | model: {MODEL}")
        print(result)
        print(result.to_pandas())
        return

    print(f"Mode: offline illustrative scores (no API key) | model: {MODEL}")
    print(f'{"row":>3} {"faith":>7} {"a_rel":>7} {"c_prec":>7} {"c_rec":>7}  note')
    for index, (row_scores, note) in enumerate(zip(OFFLINE_SCORES, NOTES)):
        values = " ".join(
            f"{row_scores[metric]:>7.2f}"
            for metric in (
                "faithfulness",
                "answer_relevancy",
                "context_precision",
                "context_recall",
            )
        )
        print(f"{index:>3} {values}  {note}")
    print(
        "\nRead the row-level scorecard: low faithfulness flags the hallucination; "
        "low context precision/recall flags the irrelevant context."
    )


if __name__ == "__main__":
    main()
