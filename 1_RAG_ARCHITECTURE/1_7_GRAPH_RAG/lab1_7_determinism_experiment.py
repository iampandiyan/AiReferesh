"""
lab1_7_determinism_experiment.py
===================================
Tests whether LLMGraphTransformer + openai/gpt-oss-20b actually produces
deterministic output at temperature=0, by running the SAME document
through extraction multiple times and comparing the exact node id sets
produced each time. temperature=0 is supposed to mean "always pick the
most likely token" -- if the node sets differ across runs anyway, that
tells us the non-determinism is coming from somewhere other than
sampling randomness (e.g. reasoning-token variability, API-side
batching/hardware non-determinism).
"""

from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="openai/gpt-oss-20b",
    api_key=os.environ.get("TOGETHER_STUDY_API_KEY"),
    base_url="https://api.together.xyz/v1",
    temperature=0,
    max_tokens=8192,
)
transformer = LLMGraphTransformer(llm=llm)

TEST_TEXT = "Employees may work from home up to 2 days per week, subject to manager approval."
NUM_RUNS = 5

if __name__ == "__main__":
    print(f"Running the SAME document {NUM_RUNS} times through extraction, temperature=0:\n")
    print(f"Text: {TEST_TEXT}\n")

    all_node_sets = []

    for run_num in range(1, NUM_RUNS + 1):
        doc = Document(page_content=TEST_TEXT)
        try:
            graph_docs = transformer.convert_to_graph_documents([doc])
            node_ids = sorted([node.id for node in graph_docs[0].nodes])
            all_node_sets.append(node_ids)
            print(f"Run {run_num}: {node_ids}")
        except Exception as e:
            all_node_sets.append(None)
            print(f"Run {run_num}: FAILED -- {type(e).__name__}")

    print(f"\n{'=' * 60}\nAGGREGATE RESULT\n{'=' * 60}")
    successful_runs = [s for s in all_node_sets if s is not None]
    unique_sets = set(tuple(s) for s in successful_runs)
    print(f"Successful runs: {len(successful_runs)} / {NUM_RUNS}")
    print(f"Number of DISTINCT node-id sets produced across those runs: {len(unique_sets)}")
    if len(unique_sets) == 1:
        print("-> IDENTICAL output every time. temperature=0 is behaving deterministically for this document.")
    else:
        print("-> DIFFERENT output across runs despite temperature=0 and identical input.")
        print("-> This confirms non-determinism is real and not just anecdotal from one prior run.")
        for i, s in enumerate(unique_sets, 1):
            print(f"  Distinct set {i}: {list(s)}")