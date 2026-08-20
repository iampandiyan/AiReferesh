"""
lab1_4_naive_prompt_case.py
==============================
Reproduces the ONE confirmed hallucination found across this lab's full
experimental journey: POL-2030's question, answered using POL-2009's
rule as context, under the naive prompt (no anti-hallucination
instruction).
"""
 
from lab1_4_common import build_sections, generate_answer_naive, print_lab_output
 
if __name__ == "__main__":
    sections = build_sections(num_sections=50, seed=42)
    target = next(s for s in sections if s["id"] == "POL-2030")
    wrong_source = next(s for s in sections if s["id"] == "POL-2009")
 
    question = target["query"]
    wrong_context = wrong_source["rule_text"]
 
    answer = generate_answer_naive(wrong_context, question)
 
    print_lab_output([target["rule_text"], wrong_context], question,
                      [(wrong_context, 0.0)], answer)
    print(f"\n>>> The correct answer would need POL-2030's own rule: {target['rule_text']}")
    print(f">>> Instead, the naive prompt was given POL-2009's UNRELATED rule and check")
    print(f">>> whether it performed unit-conversion math on the wrong number anyway.")
