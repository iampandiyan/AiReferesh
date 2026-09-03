"""
lab1_7_fix_return_clause.py
==============================
The fix: a custom Cypher generation prompt that explicitly requires
the anchor entity's own identity to be included in every RETURN
clause, so the context handed to the QA step is self-contained.
Confirmed root cause: GraphCypherQAChain's default Cypher generation
returned only the CONNECTED node's properties, never the entity that
was actually asked about -- a strict grounding prompt then correctly
declined on genuinely incomplete context.
"""

from langchain_openai import ChatOpenAI
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_core.prompts import PromptTemplate
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

graph = Neo4jGraph(
    url=os.environ.get("NEO4J_URI"),
    username=os.environ.get("NEO4J_USERNAME"),
    password=os.environ.get("NEO4J_PASSWORD"),
)
graph.refresh_schema()

CUSTOM_CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template="""Task: Generate a Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
IMPORTANT: The RETURN clause must ALWAYS include the ANCHOR entity's own
id property (the entity named in the question), not just the properties
of connected nodes. A result missing the anchor entity's identity is
INCOMPLETE and unusable, even if the connected data is otherwise correct.

Schema:
{schema}

Question: {question}
Cypher query:""",
)

chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    cypher_prompt=CUSTOM_CYPHER_PROMPT,
    verbose=True,
    allow_dangerous_requests=True,
)

if __name__ == "__main__":
    question = "What entities are connected to WorkFromHome?"
    result = chain.invoke({"query": question})
    print("\n\nFINAL ANSWER:")
    print(result["result"])