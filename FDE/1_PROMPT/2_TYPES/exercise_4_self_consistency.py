"""Exercise 4: compare one prediction with five-sample majority voting.

Run independently with the OpenAI SDK and TOGETHER_STUDY_API_KEY configured.
The ten synthetic lending cases are embedded in this file. No exercise data is shared.

Lesson: majority voting can reduce sensitivity to a single sampled answer, but it costs
roughly five times as many calls and is not guaranteed to improve accuracy. Disagreement
is a useful review signal; a confident majority is not proof that a prediction is right.
"""

import collections
import json
import os
import re

from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
LABELS = {"approve", "reject", "escalate", "inquire"}
HARD = [
    {"query": "Mi salary es 75000, necesito loan", "expected": "inquire"},
    {"query": "tengo installment 15000, approve mi loan de $3,600", "expected": "reject"},
    {"query": "FICO 780, necesito $6,000 personal loan", "expected": "approve"},
    {"query": "hice default en un loan hace 2 years", "expected": "escalate"},
    {"query": "no tengo salary slip, trabajo en cash", "expected": "inquire"},
    {"query": "necesito $12,000 con salary de 30000", "expected": "reject"},
    {"query": "mi loan fue reject y no dieron reason", "expected": "escalate"},
    {"query": "mi installment bounce el mes pasado", "expected": "escalate"},
    {"query": "puedo hacer joint loan con mi wife", "expected": "inquire"},
    {"query": "loan de $1,200 con salary de $1,200", "expected": "approve"},
]
SYSTEM = (
    "Classify the lending message into exactly one label: approve, reject, escalate, inquire. "
    'Return JSON only: {"intent": "..."}. Do not infer missing financial facts.'
)


def parse_intent(text: str) -> str:
    try:
        match = re.search(r"\{.*?\}", text, flags=re.DOTALL)
        intent = json.loads(match.group(0)).get("intent", "") if match else ""
        return intent if intent in LABELS else "PARSE_FAIL"
    except (json.JSONDecodeError, AttributeError, TypeError):
        return "PARSE_FAIL"


def sample_one(client: OpenAI, query: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": query}],
        temperature=0.7,
        max_tokens=100,
    )
    return parse_intent(response.choices[0].message.content or "")


def main() -> None:
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("Set the TOGETHER_STUDY_API_KEY environment variable first.")
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")

    correct_one = 0
    correct_vote = 0
    non_unanimous = 0
    print(f"{'#':2s} | expected  | k=1       | k=5 winner | agreement | samples")
    print("-" * 86)
    for index, case in enumerate(HARD, 1):
        single = sample_one(client, case["query"])
        samples = [sample_one(client, case["query"]) for _ in range(5)]
        counts = collections.Counter(samples)
        winner, votes = counts.most_common(1)[0]
        correct_one += single == case["expected"]
        correct_vote += winner == case["expected"]
        non_unanimous += votes < 5
        print(
            f"{index:2d} | {case['expected']:9s} | {single:9s} | {winner:10s} | "
            f"{votes}/5       | {samples}"
        )

    total = len(HARD)
    print(f"\nk=1 accuracy: {correct_one / total:.1%}")
    print(f"k=5 majority accuracy: {correct_vote / total:.1%}")
    print(f"Non-unanimous rows: {non_unanimous}/{total}; k=5 uses five times as many samples as k=1.")
    print("Routing lesson: consider human review for close votes such as 3/2; validate this policy on held-out data.")


if __name__ == "__main__":
    main()
"""
#  | expected  | k=1       | k=5 winner | agreement | samples
--------------------------------------------------------------------------------------
 1 | inquire   | PARSE_FAIL | PARSE_FAIL | 5/5       | ['PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL']
 2 | reject    | PARSE_FAIL | PARSE_FAIL | 4/5       | ['PARSE_FAIL', 'PARSE_FAIL', 'approve', 'PARSE_FAIL', 'PARSE_FAIL']
 3 | approve   | PARSE_FAIL | PARSE_FAIL | 5/5       | ['PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL']
 4 | escalate  | PARSE_FAIL | PARSE_FAIL | 5/5       | ['PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL']
 5 | inquire   | PARSE_FAIL | PARSE_FAIL | 5/5       | ['PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL']
 6 | reject    | PARSE_FAIL | PARSE_FAIL | 5/5       | ['PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL']
 7 | escalate  | PARSE_FAIL | PARSE_FAIL | 5/5       | ['PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL']
 8 | escalate  | PARSE_FAIL | PARSE_FAIL | 4/5       | ['PARSE_FAIL', 'inquire', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL']
 9 | inquire   | inquire   | inquire    | 5/5       | ['inquire', 'inquire', 'inquire', 'inquire', 'inquire']
10 | approve   | PARSE_FAIL | PARSE_FAIL | 5/5       | ['PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL', 'PARSE_FAIL']

k=1 accuracy: 10.0%
k=5 majority accuracy: 10.0%
Non-unanimous rows: 2/10; k=5 uses five times as many samples as k=1.
Routing lesson: consider human review for close votes such as 3/2; validate this policy on held-out data.
"""