"""Exercise 1: Measure the lost-in-the-middle effect with a long context.

Run: python exercise_01_lost_in_the_middle.py

Behavior: Builds a roughly 30K-token context using a word-count estimate and
places the answer sentence at 5%, 50%, and 95%. If
TOGETHER_STUDY_API_KEY is set, it makes five Together calls per position using
openai/gpt-oss-120b. Without a key, it prints a deterministic illustrative
U-shaped result; those counts are not model measurements.

Lesson: Relevant evidence can be used less reliably when buried in the middle
of a long context. Token counts and recall vary by tokenizer and model, so
measure them rather than treating the offline illustration as a benchmark.
Live mode sends 15 long-context requests and may incur charges.
"""

import os


MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = "Answer only from the supplied context. If the answer is absent, say UNKNOWN."
FILLER = (
    "The OCC, in exercise of its supervisory authority, directs that all "
    "national banks shall maintain capital adequacy as per Basel III norms. "
    "This circular supersedes earlier guidance. "
)
NEEDLE = (
    "The AcmeCorp lending limit for unsecured loans to MSMEs in regional "
    "cities is USD 30,000 as of 13 Nov 2025."
)
QUESTION = "What is the AcmeCorp lending limit for unsecured MSME loans in regional markets?"
TRIALS = 5
TARGET_TOKENS_ESTIMATE = 30_000


def together_chat(system_prompt, customer_message, max_tokens=120):
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


def build_context(needle_position_pct, target_tokens=TARGET_TOKENS_ESTIMATE):
    target_words = int(target_tokens * 0.75)
    filler_blob = (FILLER * 5000)[: target_words * 6]
    insert_at = int(len(filler_blob) * needle_position_pct / 100)
    context = filler_blob[:insert_at] + " " + NEEDLE + " " + filler_blob[insert_at:]
    return context, insert_at


def ask(context):
    prompt = f"<context>\n{context}\n</context>\n\nQuestion: {QUESTION}"
    return together_chat(PROMPT_V1, prompt)


def main():
    live = bool(os.environ.get("TOGETHER_STUDY_API_KEY"))
    simulated_recall = {5: 5, 50: 2, 95: 5}

    for position in (5, 50, 95):
        context, insertion_offset = build_context(position)
        estimated_words = len(context.split())
        if live:
            hits = sum("30,000" in (ask(context) or "").lower() for _ in range(TRIALS))
            result_kind = "live recall"
        else:
            hits = simulated_recall[position]
            result_kind = "illustrative offline simulation (not a model measurement)"
        print(
            f"position {position:>3}% | char offset {insertion_offset:,} | "
            f"about {estimated_words:,} words (~{TARGET_TOKENS_ESTIMATE:,} tokens estimated) | "
            f"{hits}/{TRIALS} {result_kind}"
        )

    print(f"\nModel: {MODEL}; Together live mode: {'on' if live else 'off'}")
    if not live:
        print("Set TOGETHER_STUDY_API_KEY to run the 15 live long-context trials.")


if __name__ == "__main__":
    main()
