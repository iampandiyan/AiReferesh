"""
lab1_7_extraction_test.py
============================
Verifies LLMGraphTransformer actually produces sensible extraction
results using our Together model, before building the full entity
disambiguation experiment. LLMGraphTransformer's package
(langchain-experimental) was archived in May 2026 -- still functional,
confirmed here, but no longer maintained.
"""

from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document
import os
from dotenv import load_dotenv

load_dotenv()

# Together's API is OpenAI-compatible, so we point ChatOpenAI at Together's
# base URL instead of OpenAI's -- this reuses the same model/key as every
# other lab in this series.
llm = ChatOpenAI(
    model="openai/gpt-oss-20b",
    api_key=os.environ.get("TOGETHER_STUDY_API_KEY"),
    base_url="https://api.together.xyz/v1",
    temperature=0,
)

transformer = LLMGraphTransformer(llm=llm)

text = """
Leave Policy Section 5: Work From Home. Employees may work from home up to 2 days
per week, subject to manager approval. Employees in probation period are NOT eligible
for work from home and must instead work from office for the first 6 months of employment.
"""

doc = Document(page_content=text)
graph_documents = transformer.convert_to_graph_documents([doc])

print("Extracted nodes:")
for node in graph_documents[0].nodes:
    print(f"  ({node.id}: {node.type})")

print("\nExtracted relationships:")
for rel in graph_documents[0].relationships:
    print(f"  ({rel.source.id}) -[{rel.type}]-> ({rel.target.id})")