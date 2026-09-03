"""
lab1_7_fix_normalization.py
==============================
The fix: after each document's independent extraction, canonicalize
every node id against a small registry of known entities using
embedding similarity -- the SAME SentenceTransformer technique used
throughout this entire lab series -- before writing it into Neo4j.
"""

from sentence_transformers import SentenceTransformer
from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document
from lab1_7_common import (
    build_policy_variants, get_neo4j_driver, print_section,
    canonicalize_node_id, CANONICAL_DESCRIPTIONS,
)
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

if __name__ == "__main__":
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    canonical_embeddings = {
        key: embed_model.encode([desc], normalize_embeddings=True)[0]
        for key, desc in CANONICAL_DESCRIPTIONS.items()
    }

    variants = build_policy_variants()
    driver = get_neo4j_driver()

    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

        print_section("EXTRACTING + CANONICALIZING + LOADING ALL DOCUMENTS")
        for v in variants:
            doc = Document(page_content=v["text"])
            try:
                graph_docs = transformer.convert_to_graph_documents([doc])
            except Exception as e:
                print(f"EXTRACTION FAILED for {v['id']}: {type(e).__name__} -- skipping")
                continue
            gdoc = graph_docs[0]

            id_rewrites = {}
            for node in gdoc.nodes:
                canonical_id, score = canonicalize_node_id(node.id, embed_model, canonical_embeddings)
                id_rewrites[node.id] = canonical_id
                if canonical_id != node.id:
                    print(f"  CANONICALIZED: '{node.id}' -> '{canonical_id}' (similarity={score:.3f})")
                session.run(
                    "MERGE (n:Entity {id: $id}) SET n.type = $type, n.source_doc = $doc_id",
                    id=canonical_id, type=node.type, doc_id=v["id"],
                )
            for rel in gdoc.relationships:
                source_id = id_rewrites.get(rel.source.id, rel.source.id)
                target_id = id_rewrites.get(rel.target.id, rel.target.id)
                session.run(
                    """
                    MATCH (a:Entity {id: $source}), (b:Entity {id: $target})
                    MERGE (a)-[r:RELATED {type: $rel_type}]->(b)
                    """,
                    source=source_id, target=target_id, rel_type=rel.type,
                )
            print(f"Loaded {v['id']}: {len(gdoc.nodes)} nodes, {len(gdoc.relationships)} relationships")

        print_section("QUERY: Find everything connected to canonical 'WorkFromHome'")
        result = session.run(
            """
            MATCH (n:Entity {id: 'WorkFromHome'})-[r]-(connected)
            RETURN n.id AS entity, type(r) AS relationship, connected.id AS connected_to, connected.source_doc AS from_doc
            """
        )
        rows = list(result)
        print(f"Found {len(rows)} connections to the CANONICAL node, across ALL originally-differently-named documents:")
        for row in rows:
            print(f"  {row['entity']} -[{row['relationship']}]- {row['connected_to']} (from {row['from_doc']})")

    driver.close()