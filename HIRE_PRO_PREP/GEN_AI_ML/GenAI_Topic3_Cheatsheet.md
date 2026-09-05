# GenAI/AI-ML Cheatsheet — Topic 3 (RAG Architecture Libraries)

**Companion to:** GenAI_Topic3_RAG_Architecture.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

All examples below were executed for real — outputs shown are actual, not invented.

---

## `langchain_text_splitters.RecursiveCharacterTextSplitter`

**Initialization:**
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=30)
```

**Top methods/parameters:**
| Method/Parameter | Explanation |
|---|---|
| `chunk_size` | Target maximum characters per chunk |
| `chunk_overlap` | Characters shared between consecutive chunks — best-effort, depends on where separators fall |
| `separators` | Ordered list of split points to try first (default tries paragraphs, then sentences, then words) — customize for structured documents |
| `.split_text(text)` | Splits a raw string, returns a list of chunk strings |
| `.split_documents(docs)` | Splits LangChain `Document` objects, preserving `metadata` on each resulting chunk — the production-relevant method since real pipelines carry source/page metadata through |

**Verified example — `split_text`:**
```python
text = "This is sentence one. This is sentence two. This is sentence three."
splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
print(splitter.split_text(text))
```
Output: `['This is sentence one. This is sentence two. This', 'two. This is sentence three.']`

**Verified example — `split_documents` (metadata preserved):**
```python
from langchain_core.documents import Document

docs = [Document(page_content=text, metadata={"source": "demo"})]
split_docs = splitter.split_documents(docs)
for d in split_docs:
    print(d.page_content, "| metadata:", d.metadata)
```
Output:
```
This is sentence one. This is sentence two. This | metadata: {'source': 'demo'}
two. This is sentence three. | metadata: {'source': 'demo'}
```

**Verified example — custom `separators`:**
```python
custom_splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=0, separators=["\n\n", ". ", " "])
print(custom_splitter.split_text("Para one here.\n\nPara two goes here. More text follows."))
```
Output: `['Para one here.', 'Para two goes here. More text follows.']`

---

## `sklearn.feature_extraction.text.TfidfVectorizer` — Corpus vs Query Pattern (RAG-Specific)

**The critical RAG-relevant distinction:** fit the vectorizer ONCE on your knowledge base, then only `.transform()` (never `.fit_transform()`) on incoming queries — otherwise the query gets its own separate vocabulary space and can't be meaningfully compared to the corpus.

**Initialization:**
```python
from sklearn.feature_extraction.text import TfidfVectorizer
vec = TfidfVectorizer(stop_words='english')
```

**Top methods:**
| Method | Explanation |
|---|---|
| `.fit_transform(corpus)` | Learn vocabulary from the knowledge base AND vectorize it — do this once, at ingestion time |
| `.transform(query)` | Vectorize new text using the ALREADY-LEARNED vocabulary — this is what you call at query time |
| `stop_words='english'` | Removes common function words — prevents misleadingly high similarity from shared words like "the"/"is" (see Topic 3, Section 3) |

**Verified example (correct pattern):**
```python
corpus = ["cats are great pets", "dogs are loyal companions"]
corpus_vecs = vec.fit_transform(corpus)          # fit ONCE on the knowledge base
query_vec = vec.transform(["I love cats"])        # transform only - reuses corpus vocabulary

from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
print(np.round(cosine_similarity(query_vec, corpus_vecs), 4))   # [[0.5774 0.]]
```

**Verified example (the bug this pattern avoids):**
```python
wrong_vec = TfidfVectorizer(stop_words='english')
wrong_query_vec = wrong_vec.fit_transform(["I love cats"])   # WRONG - refits, new vocab space
print("wrong shape (different vocab space):", wrong_query_vec.shape)     # (1, 2)
print("correct shape (same vocab space as corpus):", query_vec.shape)    # (1, 6)
```
The mismatched shapes show why comparing `wrong_query_vec` against `corpus_vecs` would either error or produce meaningless numbers — they're not in the same vector space.

---

## `numpy.argsort` — Top-K Retrieval Pattern

**Top usage:**
| Usage | Explanation |
|---|---|
| `np.argsort(scores)` | Returns indices that would sort the array ascending |
| `np.argsort(scores)[::-1]` | Reverse to get descending order (highest similarity first) |
| `[:k]` | Slice to keep only the top k indices — this three-step chain is the standard "top-k retrieval" pattern used throughout RAG pipelines |

**Verified example:**
```python
scores = np.array([0.1, 0.9, 0.3, 0.7, 0.2])
top_k_idx = np.argsort(scores)[::-1][:3]
print(top_k_idx)          # [1 3 2]
print(scores[top_k_idx])  # [0.9 0.7 0.3]
```

---

## `langchain_neo4j` (GraphRAG) — Reference Only

**Not executed in this sandbox** — requires a running Neo4j Desktop instance. Matches your lab environment exactly.

```python
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain.llms import Together

graph = Neo4jGraph(url="bolt://localhost:7687", username="neo4j", password="your_password")

chain = GraphCypherQAChain.from_llm(
    llm=Together(model="openai/gpt-oss-20b"),
    graph=graph,
    verbose=True,
)

result = chain.invoke({"query": "your natural-language question here"})
```

| Class/Method | Explanation |
|---|---|
| `Neo4jGraph(url=, username=, password=)` | Connection object to your Neo4j instance |
| `GraphCypherQAChain.from_llm(llm=, graph=)` | Builds a chain that converts natural language → Cypher query → graph query → natural language answer |
| `.invoke({"query": ...})` | Runs the full text-to-Cypher-to-answer pipeline |

---

## Status
4 fully verified entries (RecursiveCharacterTextSplitter, TfidfVectorizer corpus/query pattern, numpy.argsort) plus 1 clearly marked reference-only entry (langchain_neo4j) for your own environment. Use alongside the main Topic 3 doc.
