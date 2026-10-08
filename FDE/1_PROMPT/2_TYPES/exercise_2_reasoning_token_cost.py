"""Exercise 2: compare concise, step-by-step, and tagged calculation prompts.

Run independently with the OpenAI SDK and TOGETHER_STUDY_API_KEY configured.
Only synthetic financial figures are used; this script does not save model output.

Lesson: explicit worked calculations can improve auditability but consume more output
tokens. Ask for a short, checkable calculation rather than storing private reasoning.
The example below is internally consistent: (1,500 + 2,400) / 7,500 = 52%, so REJECT.
"""

import os
import re

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
QUERY = (
    "Monthly gross income is $7,500. Existing monthly debt payments are $1,500. "
    "The proposed loan adds a $2,400 monthly payment. Is the applicant eligible "
    "under a 50% DTI limit?"
)
BASE = """You are a lending eligibility classifier. DTI is total monthly debt payments
divided by monthly gross income. The maximum eligible DTI is 50%. Return the decision
and the numeric DTI. Do not treat annual income as monthly income.
"""
PROMPTS = {
    "plain": BASE + "Answer in one short sentence, ending with APPROVE or REJECT.",
    "step-by-step": BASE
    + "Show the DTI arithmetic briefly, then give one decision: APPROVE or REJECT.",
    "calculation-tags": BASE
    + "Put the arithmetic in <calculation>...</calculation>, then give one final line "
    "with the DTI and APPROVE or REJECT. Keep the calculation concise.",
}


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")

    results = []
    for label, system_prompt in PROMPTS.items():
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": QUERY},
            ],
        )
        content = response.choices[0].message.content or ""
        usage = response.usage
        results.append(
            {
                "label": label,
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
                "decision": re.search(r"\b(APPROVE|REJECT)\b", content.upper()),
                "preview": content.replace("\n", " ")[:100],
            }
        )

    print(f"{'variant':20s} | input | output | decision | response")
    print("-" * 95)
    for result in results:
        decision = result["decision"].group(1) if result["decision"] else "MISSING"
        print(
            f"{result['label']:20s} | {result['input_tokens']:5d} | "
            f"{result['output_tokens']:6d} | {decision:8s} | {result['preview']}"
        )
    print("Expected decision: REJECT, because 3,900 / 7,500 = 52% > 50%.")
    print("Compare measured output tokens; the exact token tax varies by response.")


if __name__ == "__main__":
    main()

"""
variant              | input | output | decision | response
-----------------------------------------------------------------------------------------------
plain                |   181 |    104 | REJECT   | DTI is 52% – REJECT.
step-by-step         |   185 |    260 | REJECT   | **DTI calculation**  \[ \text{DTI} = \frac{\text{Existing debt} + \text{Proposed payment}}{\text{Mon
calculation-tags     |   200 |    222 | REJECT   | <calculation>(1500 + 2400) / 7500 = 3900 / 7500 = 0.52 = 52%</calculation> 52% REJECT
Expected decision: REJECT, because 3,900 / 7,500 = 52% > 50%.
Compare measured output tokens; the exact token tax varies by response.
"""