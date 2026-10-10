"""Exercise 3: separate stable RAG instructions from per-request context.

Run independently with `python -m pip install openai` and TOGETHER_STUDY_API_KEY set.
Uses Together chat completions. Cache-hit fields are printed only if returned by the
provider; this API does not accept Anthropic's cache_control block.

Lesson: keep versioned policy and examples in the stable system prefix. Put retrieved
chunks, timestamps, and the question in the user message so they do not invalidate it.
"""

import datetime
import os
import hashlib

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
SYSTEM_BLOCKS = [
    "You are a Meridian Capital lending advisor. Cite the provided policy when relevant.",
    "Synthetic policy: ask for consent before financial-data access; escalate uncertain cases.",
    "Synthetic privacy policy: do not repeat personal identifiers in responses.",
    "Examples: code-mixed Spanish/English questions should receive concise matching-language answers.",
]
STABLE_SYSTEM = "\n\n".join(SYSTEM_BLOCKS)
CASES = [
    ("Mi credit score es 680, $6,000 business loan - eligible?", ["Credit score 650+ may qualify for standard review.", "Business loan terms depend on verified income and tenure."]),
    ("Calculate monthly payment for $3,600 at 14%, 36 months.", ["Monthly payment depends on principal, monthly rate, and term."]),
    ("Como aplico para un home loan top-up?", ["Top-up eligibility requires an existing loan in good standing."]),
    ("For secured loans, is credit score reviewed?", ["Credit score may be reviewed alongside collateral and affordability."]),
    ("When can insurance be offered?", ["Offer related products only after required consent."]),
]


def cached_tokens(usage):
    details = getattr(usage, "prompt_tokens_details", None)
    if isinstance(details, dict):
        return details.get("cached_tokens")
    return getattr(details, "cached_tokens", None) if details else None


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    stable_hash = hashlib.sha256(STABLE_SYSTEM.encode("utf-8")).hexdigest()
    print("Stable-prefix SHA-256:", stable_hash)

    for index, (query, chunks) in enumerate(CASES, 1):
        volatile = (
            f"TODAY: {datetime.date.today().isoformat()}\n"
            f"RETRIEVED CHUNKS:\n- " + "\n- ".join(chunks)
            + f"\n\nUSER QUERY: {query}"
        )
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": STABLE_SYSTEM}, {"role": "user", "content": volatile}],
            max_tokens=200,
        )
        usage = response.usage
        print(
            f"call {index}: prompt={getattr(usage, 'prompt_tokens', 'n/a')} "
            f"cached={cached_tokens(usage) if cached_tokens(usage) is not None else 'not reported'}"
        )
        print("response:", response.choices[0].message.content or "")

    print("Cache-hit verification is provider-dependent; identical prefix does not guarantee reported cache usage.")


if __name__ == "__main__":
    main()