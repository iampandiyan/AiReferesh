"""
lab1_7_text2cypher.py
========================
Real production Text2Cypher flow: a natural-language question gets
translated into a Cypher query BY THE LLM, executed against Neo4j, and
the result is turned back into a natural-language answer -- using
LangChain's GraphCypherQAChain, confirmed importable from the current,
maintained langchain_neo4j package (not the archived langchain-experimental).
"""

from langchain_openai import ChatOpenAI
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
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
print("Detected graph schema:\n", graph.schema)

chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,  # prints the actual generated Cypher query -- we want to see this
    allow_dangerous_requests=True,  # required acknowledgment since the LLM writes real Cypher
)

if __name__ == "__main__":
    question = "What entities are connected to WorkFromHome?"
    result = chain.invoke({"query": question})
    print("\n\nFINAL ANSWER:")
    print(result["result"])