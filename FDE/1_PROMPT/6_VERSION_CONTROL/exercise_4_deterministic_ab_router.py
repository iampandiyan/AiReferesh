"""Exercise 4: deterministic prompt A/B routing with version trace attributes.

Run independently with `python -m pip install openai opentelemetry-api` and set
TOGETHER_STUDY_API_KEY for the optional smoke request. Hashing and distribution checks
are local and run without a key. Uses openai/gpt-oss-120b through Together.

Lesson: hash-based assignment keeps a request in the same cohort across retries. Validate
that weights total 100, measure assignment distribution, and attach name/version to traces.
"""

import hashlib
import os
from collections import Counter

from openai import OpenAI
from opentelemetry import trace


MODEL = "openai/gpt-oss-120b"
PROMPTS = {
    "v2": "You are a lending advisor. Explain assumptions and avoid inventing facts.",
    "v3": "You are a lending advisor. Match the query language, explain assumptions, and avoid inventing facts.",
}
COHORTS = [("v3", 10), ("v2", 90)]
TRACER = trace.get_tracer("prompt-version-routing")


def pick_version(request_id: str, cohorts: list[tuple[str, int]]) -> str:
    if not cohorts or any(percent < 0 for _, percent in cohorts):
        raise ValueError("Cohorts must be non-empty and percentages non-negative.")
    if sum(percent for _, percent in cohorts) != 100:
        raise ValueError("Cohort percentages must sum to 100.")
    bucket = int(hashlib.sha256(request_id.encode("utf-8")).hexdigest(), 16) % 100
    cumulative = 0
    for version, percent in cohorts:
        cumulative += percent
        if bucket < cumulative:
            return version
    raise RuntimeError("No cohort selected; check percentages.")


def main() -> None:
    stable_request = "request-demo-7392"
    repeat_assignments = {pick_version(stable_request, COHORTS) for _ in range(100)}
    assert len(repeat_assignments) == 1

    counts = Counter(pick_version(f"synthetic-request-{index}", COHORTS) for index in range(1000))
    canary_share = counts["v3"] / 1000
    print("Deterministic repeated assignment:", repeat_assignments.pop())
    print("1000-request distribution:", dict(counts))
    print(f"v3 canary share: {canary_share:.1%}")
    assert abs(canary_share - 0.10) <= 0.03

    version = pick_version(stable_request, COHORTS)
    with TRACER.start_as_current_span("lending_advisor") as span:
        span.set_attribute("gen_ai.prompt.name", "lending-advisor")
        span.set_attribute("gen_ai.prompt.version", version)
        span.set_attribute("prompt.request_id", stable_request)
        print("Trace attributes set: gen_ai.prompt.name=lending-advisor, "
              f"gen_ai.prompt.version={version}")

    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        print("Together smoke call skipped; set TOGETHER_STUDY_API_KEY to run it.")
        return
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PROMPTS[version]},
            {"role": "user", "content": "When should an applicant provide income information?"},
        ],
        max_tokens=150,
    )
    print(f"Response from {version}:", response.choices[0].message.content or "")


if __name__ == "__main__":
    main()