"""
lab1_4_naive_prompt_experiment.py
====================================
Isolates the actual causal factor behind the 0% hallucination rate seen
in the last two experiments: was it something inherent to the model, or
specifically the strict "say exactly: Not found..." instruction? Re-runs
the SAME semantic near-miss contexts through a naive prompt with no
explicit anti-hallucination instruction at all -- the kind of prompt
many RAG tutorials and early prototypes actually ship with.
"""
import re
from lab1_4_common import build_sections, generate_answer_naive
from lab1_4_hallucination_experiment import ACTION_GROUPS, find_semantic_near_miss, has_reasoning_leak

def is_actually_declining(answer):
    """Strip markdown formatting before checking for decline phrases --
    '**not**' breaks a literal 'not' substring check. Also broaden the
    phrase list based on real naive-prompt phrasing observed in testing."""
    clean = re.sub(r"[*_`]", "", answer).lower()
    decline_phrases = ["not found", "not specif", "cannot", "can't", "does not mention",
                        "not available", "not defined", "no information", "don't know",
                        "no specific", "not provided"]
    return any(phrase in clean for phrase in decline_phrases)

if __name__ == "__main__":
    sections = build_sections(num_sections=50, seed=42)

    wrong_transfer = 0
    declined_anyway = 0
    no_partner = 0
    leak_count = 0
    tested = 0

    for i, section in enumerate(sections):
        near_miss = find_semantic_near_miss(section, sections)
        if not near_miss:
            no_partner += 1
            continue

        question = section["query"]  # plain question, no pressure needed this time
        answer = generate_answer_naive(near_miss["rule_text"], question)
        tested += 1

        if has_reasoning_leak(answer):
            leak_count += 1

        transferred = str(near_miss["limit"]) in answer and not is_actually_declining(answer)
        wrong_transfer += int(transferred)
        declined_anyway += int(not transferred)

        print(f"\n--- SECTION {section['id']} ({i+1}/{len(sections)}) ---")
        print(f"Question: {question}")
        print(f"Context given (near-miss, same domain, different action): {near_miss['rule_text']}")
        print(f"LLM answer (NAIVE prompt): {answer}")
        print(f"Verdict: {'WRONG-TRANSFER HALLUCINATION' if transferred else 'declined/hedged anyway'}")

    print(f"\n\n{'=' * 70}\nNAIVE PROMPT AGGREGATE RESULTS\n{'=' * 70}")
    print(f"Sections tested: {tested} / {len(sections)} (skipped {no_partner} with no near-miss partner)")
    print(f"WRONG-TRANSFER hallucination (naive prompt, no anti-hallucination instruction): "
          f"{wrong_transfer} ({100*wrong_transfer/tested:.1f}%)")
    print(f"Declined or hedged anyway despite no explicit instruction: "
          f"{declined_anyway} ({100*declined_anyway/tested:.1f}%)")
    print(f"Reasoning-leak rate: {leak_count} ({100*leak_count/tested:.1f}%)")