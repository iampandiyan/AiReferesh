"""Exercise 8: generate a framework decision memo with the Together model.

Run independently after installing `openai` and setting TOGETHER_STUDY_API_KEY.

Behavior: asks for a one-page architecture-review memo for the internal-tools
agent scenario and prints the generated recommendation.
Lesson: LangGraph fits branching approval/rejection and durable human resume;
CrewAI is optimized for concurrent collaborators, and a raw SDK would require
hand-built state and checkpointing. Prefer the heavier framework only where
requirements justify it.
"""

import os

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
PROMPT_V1 = (
    "You are a pragmatic AI architecture reviewer. Write a concise one-page "
    "decision memo and make a specific framework recommendation. Explain how "
    "the choice handles the stated workflow, operational tradeoffs, and why "
    "simpler options are or are not sufficient."
)


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    customer_message = (
        "Recommend a framework for an internal-tools agent that must check "
        "three ERP systems, approve or reject the request, and route rejected "
        "requests to a human reviewer who may resume the run hours later. "
        "Recommend LangGraph on branching and durable-resume grounds. Explain "
        "why CrewAI's concurrent-collaborator pattern is not a fit and why a "
        "raw SDK would require hand-writing a state machine and durable "
        "checkpoints. Close by explaining that the heavier tool is justified "
        "only by requirements that force it."
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PROMPT_V1},
            {"role": "user", "content": customer_message},
        ],
        max_tokens=900,
        temperature=0.2,
    )
    print(response.choices[0].message.content or "No memo returned.")


if __name__ == "__main__":
    main()
