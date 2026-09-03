"""
lab1_7_disambiguation_experiment.py
======================================
Measures how often LLMGraphTransformer extracts DIFFERENT node id
strings for the SAME real-world entity, across documents that describe
it with different surface phrasing. Each document is extracted
independently (as a real ingestion pipeline would process documents
one at a time), so nothing forces consistent naming across calls.
"""

from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document
from collections import defaultdict
from lab1_7_common import build_policy_variants
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="openai/gpt-oss-20b",
    api_key=os.environ.get("TOGETHER_STUDY_API_KEY"),
    base_url="https://api.together.xyz/v1",
    temperature=0,
)
transformer = LLMGraphTransformer(llm=llm)

if __name__ == "__main__":
    variants = build_policy_variants()
    surface_forms_by_canonical = defaultdict(set)

    for v in variants:
        print(f"\n{'=' * 60}\n{v['id']} ({v['canonical_action']})\n{'=' * 60}")
        print(f"Text: {v['text']}")

        doc = Document(page_content=v["text"])
        graph_docs = transformer.convert_to_graph_documents([doc])

        node_ids = [node.id for node in graph_docs[0].nodes]
        print(f"Extracted node ids: {node_ids}")

        # Record every node id that plausibly refers to the canonical action
        # entity this document is about (simple substring heuristic for
        # this lab's known vocabulary -- production systems use embedding
        # similarity or an LLM judge for this matching step instead).
        for node_id in node_ids:
            lowered = node_id.lower()
            if v["canonical_action"] == "work_from_home" and any(
                kw in lowered for kw in ["work from home", "remote work", "telecommut", "wfh"]
            ):
                surface_forms_by_canonical["work_from_home"].add(node_id)
            elif v["canonical_action"] == "probation" and any(
                kw in lowered for kw in ["probation", "trial period", "evaluation window", "new-hire", "new hire"]
            ):
                surface_forms_by_canonical["probation"].add(node_id)

    print(f"\n\n{'=' * 60}\nAGGREGATE RESULTS\n{'=' * 60}")
    for canonical, surface_forms in surface_forms_by_canonical.items():
        print(f"\nCanonical entity '{canonical}' was extracted as {len(surface_forms)} DIFFERENT node id(s):")
        for s in surface_forms:
            print(f"  - {s!r}")
        if len(surface_forms) > 1:
            print(f"  !!! DISAMBIGUATION FAILURE: {len(surface_forms)} different node ids for what should be ONE entity.")
            print(f"  !!! A multi-hop query mentioning any ONE of these names will silently miss the others.")