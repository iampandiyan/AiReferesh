"""Exercise 8: Rank unlabeled production traces for manual triage.

Run: python exercise_08_flag_unlabeled_traffic.py
Optional live judge: python exercise_08_flag_unlabeled_traffic.py --live

Behavior: Scores 30 traces without reading an expected answer. The default
uses standard-library heuristics (weak retrieval, hedging, missing citation,
and thumbs-down). --live asks Together's openai/gpt-oss-120b to judge each
trace; it requires TOGETHER_STUDY_API_KEY and makes 30 calls.

Lesson: Reference-free signals can prioritize investigation but cannot prove
an answer is wrong. Validate triage scores against human review and track
false positives. Live LLM judge scores are also estimates, not ground truth.
"""

import argparse
import os
from collections import namedtuple


MODEL = "openai/gpt-oss-120b"
Trace = namedtuple("Trace", "id query max_cos answer thumbs_down")
TRACES = [
    Trace("t01", "erasure rights under GDPR", 0.81, "Under GDPR Art. 17 a subject may request erasure. [gdpr-17-erasure]", False),
    Trace("t02", "cuota de prestamo si pago tarde", 0.32, "I'm not sure, this might depend on the loan terms.", True),
    Trace("t03", "lawful basis for processing", 0.77, "Consent or another lawful basis applies. [gdpr-consent]", False),
    Trace("t04", "penalty for late erasure", 0.41, "The penalty is unclear; possibly a fine.", False),
    Trace("t05", "PEP screening at onboarding", 0.74, "Enhanced due diligence is required for PEPs. [occ-kyc-pep]", False),
    Trace("t06", "reembolso tarde recargo", 0.29, "No estoy seguro. As far as I know there may be a fee.", True),
    Trace("t07", "LCR floor for banks", 0.79, "Banks maintain an LCR of at least 100 percent. [occ-liquidity-lcr]", False),
    Trace("t08", "capital buffer for small banks", 0.44, "It might be around 2.5 percent, I think.", False),
    Trace("t09", "audit fields to log", 0.72, "Log model version, input, output, reviewer. [nist-ai-rmf-audit]", False),
    Trace("t10", "does OCC require annual PEP", 0.66, "Possibly, but I cannot confirm from the documents.", True),
    Trace("t11", "right to correction", 0.76, "Inaccurate data may be corrected. [gdpr-16-correction]", False),
    Trace("t12", "erasure timeline days", 0.48, "The controller must erase, timeline unknown.", False),
    Trace("t13", "total capital ratio floor", 0.83, "The total capital ratio floor is set. [occ-capital-basel-3]", False),
    Trace("t14", "AI transaction approval", 0.39, "Unclear which rule applies here.", True),
    Trace("t15", "out-of-band confirm rule", 0.71, "AI-initiated transactions need out-of-band confirm. [nist-ai-rmf-confirm]", False),
    Trace("t16", "consentimiento GDPR", 0.35, "I think consent is needed, may depend on context.", False),
    Trace("t17", "data minimization duty", 0.69, "Controllers minimize data and limit purpose. [gdpr-5-minimization]", False),
    Trace("t18", "liquidity ratio minimum", 0.62, "The LCR minimum is possibly 100 percent.", True),
    Trace("t19", "grievance officer contact", 0.68, "A contact point is published. [gdpr-grievance]", False),
    Trace("t20", "grievance response window", 0.47, "Response within some days, unclear exactly.", False),
    Trace("t21", "explanation at decision time", 0.73, "A human-readable explanation is generated. [nist-ai-rmf-explain]", False),
    Trace("t22", "KYC onboarding documents", 0.58, "Enhanced due diligence for PEPs. [occ-kyc-pep]", True),
    Trace("t23", "DPIA requirement", 0.70, "A DPIA is required for high-risk processing. [gdpr-accountability]", False),
    Trace("t24", "audit fields required", 0.51, "Log model version, input, output. [nist-ai-rmf-audit]", False),
    Trace("t25", "erasure vs correction", 0.67, "Erasure in [gdpr-17-erasure], correction in [gdpr-16-correction].", False),
    Trace("t26", "prestamo mora interes", 0.30, "No documents found; I'm not sure.", True),
    Trace("t27", "capital adequacy Basel", 0.80, "Total capital ratio floor per [occ-capital-basel-3].", False),
    Trace("t28", "explainability at decision time", 0.45, "Explanations required, though details unclear.", False),
    Trace("t29", "lawful basis processing", 0.72, "Consent or another lawful basis. [gdpr-consent]", False),
    Trace("t30", "out of band confirm scope", 0.55, "It may depend on transaction type.", True),
]
HEDGES = (
    "not sure", "might", "possibly", "unclear", "cannot confirm",
    "as far as i know", "unknown", "i think", "may depend",
)


def judge_heuristic(trace):
    score, reasons = 0.0, []
    if trace.max_cos < 0.5:
        score += 2.0
        reasons.append(f"weak retrieval ({trace.max_cos:.2f})")
    hedges = sum(hedge in trace.answer.lower() for hedge in HEDGES)
    if hedges:
        score += 0.6 * hedges
        reasons.append(f"{hedges} hedge token(s)")
    if "[" not in trace.answer:
        score += 1.0
        reasons.append("no chunk citation")
    if trace.thumbs_down:
        score += 1.5
        reasons.append("user thumbs-down")
    return score, reasons


def judge_together(trace):
    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        raise RuntimeError("--live requires TOGETHER_STUDY_API_KEY.")

    from together import Together

    client = Together(api_key=api_key)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Score from 0 to 3 how likely this RAG answer is wrong or "
                    "unfaithful. Judge faithfulness and relevance only; no gold "
                    "answer is provided. Reply with one number."
                ),
            },
            {"role": "user", "content": f"Question: {trace.query}\nAnswer: {trace.answer}"},
        ],
        max_tokens=10,
    )
    text = (response.choices[0].message.content or "").strip()
    try:
        score = float(text)
    except ValueError as error:
        raise ValueError(f"Together judge returned a non-numeric score: {text!r}") from error
    if not 0 <= score <= 3:
        raise ValueError(f"Together judge score must be between 0 and 3, got {score}.")
    return score, ["Together LLM judge"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Use Together to judge every trace (30 API calls).")
    args = parser.parse_args()
    judge = judge_together if args.live else judge_heuristic

    ranked = []
    for trace in TRACES:
        score, reasons = judge(trace)
        ranked.append((round(score, 1), trace.id, trace.query, reasons))
    ranked.sort(key=lambda row: (-row[0], row[1]))
    flagged = [row for row in ranked if row[0] >= 2.0]

    print(f"{len(flagged)} of {len(TRACES)} traces flagged for hand triage (score >= 2.0):\n")
    for score, trace_id, query, reasons in ranked[:10]:
        mark = "FLAG" if score >= 2.0 else "ok  "
        print(f"  {mark} {score:4.1f}  {trace_id}  {query[:34]:<34} {'; '.join(reasons)}")
    print(f"\nScoring mode: {'Together ' + MODEL if args.live else 'offline heuristic'}")


if __name__ == "__main__":
    main()
