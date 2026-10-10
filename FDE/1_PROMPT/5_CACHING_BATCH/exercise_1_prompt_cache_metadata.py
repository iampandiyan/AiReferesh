"""Exercise 1: repeat a stable prompt and inspect Together cache metadata.

Run independently with `python -m pip install openai` and TOGETHER_STUDY_API_KEY set.
Uses openai/gpt-oss-120b through Together's OpenAI-compatible chat endpoint.

Important: Anthropic's cache_control block is not part of this API request. Prompt-cache
behavior and usage fields are provider/model dependent. This script reports metadata
Together actually returns and does not claim a cache hit when the field is absent.

Lesson: keep reusable instructions stable and put changing input in user messages. Measure
cache usage from provider metadata instead of assuming a cache was created or read.
"""

import os

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
SYSTEM_PROMPT = ("You are a lending advisor. Follow these synthetic policy notes. "
                "State assumptions clearly and do not invent missing facts. "
                "For loan calculations, distinguish annual and monthly rates. "
                "Never repeat national identifiers. " * 120)
QUERIES = [
    "Estimate the monthly payment for a $3,600 loan at 14% APR over 36 months.",
    "Estimate the monthly payment for a $2,400 loan at 18% APR over 24 months.",
]


def cached_prompt_tokens(usage) -> int | None:
    details = getattr(usage, "prompt_tokens_details", None)
    if details is None:
        return None
    if isinstance(details, dict):
        return details.get("cached_tokens")
    return getattr(details, "cached_tokens", None)


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")

    for index, query in enumerate(QUERIES, 1):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": query}],
            max_tokens=180,
        )
        usage = response.usage
        cached = cached_prompt_tokens(usage) if usage else None
        print(
            f"call {index}: prompt_tokens={getattr(usage, 'prompt_tokens', 'n/a')} "
            f"cached_prompt_tokens={cached if cached is not None else 'not reported'} "
            f"completion_tokens={getattr(usage, 'completion_tokens', 'n/a')}"
        )
        print("response:", response.choices[0].message.content or "")

    print("A missing/zero cached-token field means this request did not report a cache read.")
    print("Do not add Anthropic cache_control parameters to this Together request.")


if __name__ == "__main__":
    main()