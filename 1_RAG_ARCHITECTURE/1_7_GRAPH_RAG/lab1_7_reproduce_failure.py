"""
lab1_7_reproduce_failure.py
==============================
Loads the SAME inconsistently-named extractions from the disambiguation
experiment into real Neo4j, then runs a real Cypher query asking about
"work from home" -- and shows it silently missing evidence stored under
a differently-named node, exactly as production disambiguation failures
actually manifest.
"""

from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document
from lab1_7_common import build_policy_variants, get_neo4j_driver, print_section
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="openai/gpt-oss-20b",
    api_key=os.environ.get("TOGETHER_STUDY_API_KEY"),
    base_url="https://api.together.xyz/v1",
    temperature=0,
    max_tokens=8192,  # default (4096) is too small for a reasoning model's
                       # internal reasoning + structured tool-call JSON --
                       # confirmed by a real LengthFinishReasonError on DOC-03
)
transformer = LLMGraphTransformer(llm=llm)

if __name__ == "__main__":
    variants = build_policy_variants()
    driver = get_neo4j_driver()

    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")  # clean slate

        print_section("EXTRACTING AND LOADING ALL 8 DOCUMENTS INTO NEO4J")
        for v in variants:
            doc = Document(page_content=v["text"])
            try:
                graph_docs = transformer.convert_to_graph_documents([doc])
            except Exception as e:
                print(f"EXTRACTION FAILED for {v['id']}: {type(e).__name__}: {e}")
                continue
            gdoc = graph_docs[0]

            for node in gdoc.nodes:
                session.run(
                    "MERGE (n:Entity {id: $id}) SET n.type = $type, n.source_doc = $doc_id",
                    id=node.id, type=node.type, doc_id=v["id"],
                )
            for rel in gdoc.relationships:
                session.run(
                    """
                    MATCH (a:Entity {id: $source}), (b:Entity {id: $target})
                    MERGE (a)-[r:RELATED {type: $rel_type}]->(b)
                    """,
                    source=rel.source.id, target=rel.target.id, rel_type=rel.type,
                )
            print(f"Loaded {v['id']}: {len(gdoc.nodes)} nodes, {len(gdoc.relationships)} relationships")

        print_section("QUERY: Find everything connected to 'Work From Home'")
        result = session.run(
            """
            MATCH (n:Entity {id: 'Work From Home'})-[r]-(connected)
            RETURN n.id AS entity, type(r) AS relationship, connected.id AS connected_to, connected.source_doc AS from_doc
            """
        )
        rows = list(result)
        print(f"Found {len(rows)} connections to the node literally named 'Work From Home':")
        for row in rows:
            print(f"  {row['entity']} -[{row['relationship']}]- {row['connected_to']} (from {row['from_doc']})")

        print_section("REALITY CHECK: how many total nodes actually relate to this concept, under ANY name?")
        result = session.run(
            """
            MATCH (n:Entity)
            WHERE n.id IN ['Work From Home', 'Remote Work', 'Wfh_Arrangements', 'Wfh']
            RETURN n.id AS entity, n.source_doc AS from_doc
            """
        )
        for row in result:
            print(f"  {row['entity']} (from {row['from_doc']})")

    driver.close()