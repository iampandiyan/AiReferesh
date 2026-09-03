"""
lab1_7_diagnose_qa_step.py
=============================
Isolates WHERE the text2cypher failure actually happened. Cypher
generation and Neo4j execution both worked correctly (confirmed in the
prior run's printed Full Context). This script tests whether the SAME
model, given the SAME retrieved context, answers correctly through our
own plain prompt -- to determine if GraphCypherQAChain's specific
default QA prompt template is the actual problem, not the model itself.
"""

from langchain_neo4j.chains.graph_qa.cypher import CYPHER_QA_PROMPT
from lab1_7_common import generate_answer

# The EXACT context GraphCypherQAChain retrieved in the prior run --
# copied directly from its printed "Full Context" output.
retrieved_context = [
    {'connected.id': 'Twodaysperweek', 'connected.type': 'Duration', 'connected.source_doc': 'DOC-02'},
    {'connected.id': 'Supervisorsignoff', 'connected.type': 'Approval', 'connected.source_doc': 'DOC-02'},
]
question = "What entities are connected to WorkFromHome?"

if __name__ == "__main__":
    print("=" * 60)
    print("GraphCypherQAChain's DEFAULT QA prompt template:")
    print("=" * 60)
    print(CYPHER_QA_PROMPT.template)

    print("\n" + "=" * 60)
    print("Testing the SAME context through OUR plain prompt instead:")
    print("=" * 60)
    context_str = "\n".join(str(row) for row in retrieved_context)
    answer = generate_answer(context_str, question)
    print(f"\nOur plain-prompt answer: {answer}")