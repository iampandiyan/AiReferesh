"""
lab1_7_verify_context_hypothesis.py
======================================
Tests the hypothesis directly: does the SAME model answer correctly
if the context explicitly names the source entity, instead of only
returning the connected node's properties (which is what the
generated Cypher's RETURN clause actually did)?
"""

from lab1_7_common import generate_answer

question = "What entities are connected to WorkFromHome?"

# Version A: exactly what GraphCypherQAChain actually returned (source entity name absent)
context_a = (
    "{'connected.id': 'Twodaysperweek', 'connected.type': 'Duration', 'connected.source_doc': 'DOC-02'}\n"
    "{'connected.id': 'Supervisorsignoff', 'connected.type': 'Approval', 'connected.source_doc': 'DOC-02'}"
)

# Version B: same facts, but self-contained -- explicitly names the source entity
context_b = (
    "WorkFromHome is connected to Twodaysperweek (type: Duration, from DOC-02).\n"
    "WorkFromHome is connected to Supervisorsignoff (type: Approval, from DOC-02)."
)

if __name__ == "__main__":
    print("=== Version A: source entity name ABSENT from context (as GraphCypherQAChain returned it) ===")
    print(generate_answer(context_a, question))

    print("\n=== Version B: source entity name EXPLICITLY included in context ===")
    print(generate_answer(context_b, question))