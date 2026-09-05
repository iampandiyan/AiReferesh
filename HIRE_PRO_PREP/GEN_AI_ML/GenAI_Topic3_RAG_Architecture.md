# GenAI/AI-ML Principles — Topic 3: RAG Architecture

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

This is the topic where your actual lab work (Labs 1.1–1.7) gives you a real edge — most candidates will know RAG only as a buzzword. The concepts below are demonstrated with real, executed code wherever computable without network access (chunking, retrieval, TF-IDF-based grounding), and reference your actual confirmed lab findings where the full pipeline needs your live environment.

---

## 1. What Is RAG, and Why Does It Exist?

**Retrieval-Augmented Generation** combines two systems: a retriever that finds relevant information from a knowledge base, and a language model that generates an answer *grounded in* that retrieved information — instead of relying purely on what the model memorized during training.

**Why it matters:** an LLM's internal knowledge is frozen at training time and can be wrong, outdated, or simply absent for niche/private data (like your company's internal SWIFT documentation). RAG lets the model answer correctly about things it was never trained on, by handing it the relevant text at query time.

The full pipeline: **Document → Chunking → Embedding → Vector Index → Retrieval → Generation (grounded in retrieved chunks)**

---

## 2. Chunking — Splitting Documents to Fit the Context Window

Documents are usually too long to embed or feed to an LLM as a single unit, so they're split into smaller "chunks." Per your lab series' standing rule, this should always use a library-based splitter, never hand-rolled logic.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

document = """RAG stands for Retrieval-Augmented Generation. It combines a retrieval system with a language model.
The retrieval system finds relevant documents from a knowledge base. The language model then generates an answer
grounded in those retrieved documents. This reduces hallucination compared to relying purely on the model's
internal parametric knowledge, which can be outdated or simply wrong for niche topics. Chunking is the process
of splitting large documents into smaller pieces that fit within the retriever's and the model's context window."""

splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=30)
chunks = splitter.split_text(document)
for i, c in enumerate(chunks):
    print(f"chunk {i} (len={len(c)}): {c!r}")
```
Output:
```
chunk 0 (len=100): 'RAG stands for Retrieval-Augmented Generation. It combines a retrieval system with a language model.'
chunk 1 (len=112): 'The retrieval system finds relevant documents from a knowledge base. The language model then generates an answer'
chunk 2 (len=107): "grounded in those retrieved documents. This reduces hallucination compared to relying purely on the model's"
chunk 3 (len=110): "internal parametric knowledge, which can be outdated or simply wrong for niche topics. Chunking is the process"
chunk 4 (len=112): "of splitting large documents into smaller pieces that fit within the retriever's and the model's context window."
```

### The real effect of `chunk_overlap`

I initially assumed overlap would change the *chunk count* — that assumption was wrong and worth showing honestly. Overlap's real effect is **shared boundary text between consecutive chunks**, which only becomes visible with the right document structure:

```python
single_para = ("RAG stands for Retrieval-Augmented Generation. It combines a retrieval system with a language model. "
"The retrieval system finds relevant documents from a knowledge base. The language model then generates an answer "
"grounded in those retrieved documents. This reduces hallucination compared to relying purely on internal knowledge.")

overlap_splitter = RecursiveCharacterTextSplitter(chunk_size=120, chunk_overlap=40)
overlap_chunks = overlap_splitter.split_text(single_para)
for i, c in enumerate(overlap_chunks):
    print(f"chunk {i}: {c!r}")
```
Output:
```
chunk 0: 'RAG stands for Retrieval-Augmented Generation. It combines a retrieval system with a language model. The retrieval'
chunk 1: 'with a language model. The retrieval system finds relevant documents from a knowledge base. The language model then'
chunk 2: 'knowledge base. The language model then generates an answer grounded in those retrieved documents. This reduces'
chunk 3: 'those retrieved documents. This reduces hallucination compared to relying purely on internal knowledge.'
```
Notice chunk 0 ends with `"The retrieval"` and chunk 1 starts with the exact same phrase — that's the overlap actually working. **MCQ-relevant caveat I discovered while verifying this:** `RecursiveCharacterTextSplitter` splits along separators (paragraphs, newlines, sentences) first — if your document has natural line breaks near the chunk boundary, the overlap may not manifest as literal repeated text the way this clean single-paragraph example shows. Overlap is best-effort, not a hard guarantee, because the splitter still respects separator boundaries first.

---

## 3. End-to-End Retrieval Pipeline (Real, Computable Without Network Access)

This uses TF-IDF instead of neural embeddings (see GenAI Topic 2) purely so it runs without a model download — the retrieval *mechanics* are identical to what your FAISS/pgvector lab environment does with real embeddings.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

knowledge_base = [
    "RAG reduces hallucination by grounding answers in retrieved documents.",
    "Chunking splits documents into smaller pieces for the context window.",
    "The stock market had a volatile trading session today.",
    "Cosine similarity measures the angle between two vectors.",
    "Parent document expansion retrieves a wider context around a matched small chunk.",
]

# stop_words='english' matters here - without it, short queries get misleadingly
# high similarity to unrelated docs purely from shared common words like "the", "what", "is"
vectorizer = TfidfVectorizer(stop_words='english')
kb_vectors = vectorizer.fit_transform(knowledge_base)

def retrieve(query, k=2):
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, kb_vectors)[0]
    top_k_idx = np.argsort(sims)[::-1][:k]
    return [(knowledge_base[i], round(sims[i], 4)) for i in top_k_idx]

query = "How does RAG prevent the model from making things up?"
for doc, score in retrieve(query, k=2):
    print(f"score={score}  ->  {doc}")
```
Output:
```
score=0.3878  ->  RAG reduces hallucination by grounding answers in retrieved documents.
score=0.0     ->  Parent document expansion retrieves a wider context around a matched small chunk.
```
**Real thing I caught while building this:** my first version used plain `TfidfVectorizer()` without stop-word removal, and it gave a completely unrelated query ("What is the capital of a fictional planet Zortan?") a similarity score around 0.24 against multiple unrelated documents — purely from shared function words like "the," "is," "a." Adding `stop_words='english'` fixed this to a correct 0.0 across the board. This is a genuine, MCQ-relevant preprocessing trap, not just a code style choice.

---

## 4. Grounding vs Hallucination

**Grounded answer:** the model's response is based on and traceable to retrieved context.
**Hallucination:** the model generates a confident-sounding answer that isn't supported by any retrieved (or real) information.

This illustrative mock (not a real LLM call) shows the *structural* difference in how a grounded system should behave — refusing or hedging when retrieval confidence is low, rather than always answering confidently:

```python
def grounded_answer(query, retrieved_docs, threshold=0.15):
    best_doc, best_score = retrieved_docs[0]
    if best_score < threshold:
        return "I don't have enough information in the retrieved context to answer this confidently."
    return f"Based on retrieved context: {best_doc}"

def hallucinating_answer(query):
    # illustrates the failure mode: answering confidently regardless of whether it actually knows anything
    return "The answer is definitely 42, and RAG was invented in 1823 by a computer scientist named Zorg."

results = retrieve(query, k=2)
print("grounded:", grounded_answer(query, results))

irrelevant_query = "What is the capital of a fictional planet Zortan?"
irrelevant_results = retrieve(irrelevant_query, k=2)
print("grounded (low-confidence case):", grounded_answer(irrelevant_query, irrelevant_results))
print("hallucinating mock (for contrast):", hallucinating_answer(irrelevant_query))
```
Output:
```
grounded: Based on retrieved context: RAG reduces hallucination by grounding answers in retrieved documents.
grounded (low-confidence case): I don't have enough information in the retrieved context to answer this confidently.
hallucinating mock (for contrast): The answer is definitely 42, and RAG was invented in 1823 by a computer scientist named Zorg.
```
**This directly matches your Lab 1.4 confirmed result:** 0% hallucination under strict prompting, with the single failure being arithmetic overreach — not the model inventing facts, but overstepping what strict grounding should allow. The threshold-based refusal pattern above is a simplified version of that same discipline.

---

## 5. Multi-Hop / Decomposed Retrieval

Some questions require combining facts from multiple documents — a single retrieval pass often fails because no single chunk contains the full answer. Decomposing the question into sub-questions, retrieving for each separately, and combining the results is the standard fix.

```python
def decompose_question(question):
    # In a real pipeline, an LLM performs this decomposition step;
    # hardcoded here to demonstrate the RETRIEVAL pattern that follows.
    return [
        "Who wrote the RAG grounding technique documentation?",
        "What company do they work for?",
    ]

sub_questions = decompose_question("What company does the author of the RAG documentation work for?")
for sq in sub_questions:
    hits = retrieve(sq, k=1)
    print(f"sub-question: {sq}\n  top hit: {hits[0]}")
```
Output:
```
sub-question: Who wrote the RAG grounding technique documentation?
  top hit: ('RAG reduces hallucination by grounding answers in retrieved documents.', 0.5484)
sub-question: What company do they work for?
  top hit: ('Parent document expansion retrieves a wider context around a matched small chunk.', 0.0)
```
The second sub-question returns a 0.0-confidence, irrelevant hit — an honest demonstration that decomposition alone doesn't guarantee success; it depends on the knowledge base actually containing the needed information for each sub-question. **This directly matches your Lab 1.5 confirmed result:** single-shot bridge-entity question accuracy was only 2%, but decomposed 2-hop retrieval brought it to 96% — the dramatic improvement comes from giving each sub-question its own focused retrieval pass instead of hoping one query surfaces everything.

---

## 6. Re-ranking

After initial retrieval (fast but approximate), a cross-encoder re-ranker re-scores the top candidates more precisely before they're passed to the LLM — trading a bit of speed for better relevance ordering.

**Your Lab 1.2 confirmed finding is directly relevant here:** cross-encoder reranking produced identical scores across both FAISS and pgvector backends — meaning re-ranking quality is independent of which vector store did the initial retrieval, since re-ranking operates on the *retrieved text*, not the vector index internals.

---

## 7. GraphRAG — Reference Only (Matches Your Neo4j Lab Environment)

An alternative to pure vector retrieval: extract entities and relationships into a knowledge graph, then query the graph structure directly (e.g., via generated Cypher queries) instead of relying only on semantic similarity. This is not executed here — it needs your Neo4j Desktop instance and `langchain_neo4j` setup. Full reference code matching your lab pattern:

```python
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain.llms import Together  # or whichever LLM wrapper your lab environment uses

graph = Neo4jGraph(url="bolt://localhost:7687", username="neo4j", password="your_password")

chain = GraphCypherQAChain.from_llm(
    llm=Together(model="openai/gpt-oss-20b"),
    graph=graph,
    verbose=True,
)

result = chain.invoke({"query": "Which settlement center processed the most MT548 status updates last month?"})
print(result)
```
**Directly matches your Lab 1.7 confirmed findings:** 0% naming consistency across independently-extracted documents (a real, confirmed limitation of naive entity extraction), with embedding-based canonicalization as a partial fix — and Text2Cypher failures traced to incomplete `RETURN` clauses, fixed with a custom Cypher-generation prompt. Worth remembering as a concrete example if an interview question asks about GraphRAG's practical challenges, not just its theory.

---

## 8. Traps & Misconceptions (MCQ-Relevant)

1. **"RAG eliminates hallucination completely"** — FALSE. It reduces it significantly by grounding answers, but doesn't guarantee zero hallucination — your own Lab 1.4 result (0% hallucination, one arithmetic overreach) shows even a well-grounded system can still fail in adjacent ways.
2. **"Bigger chunks are always better since they contain more context"** — FALSE. Bigger chunks dilute the specific match a retriever is looking for and can push relevant + irrelevant content into the same chunk, hurting retrieval precision. This is the exact class of problem "parent document expansion" (Lab 1.3) exists to solve — retrieve small precise chunks, then expand to their parent for full context only after a match is found.
3. **"More retrieved documents = better answers"** — FALSE. Irrelevant retrieved context can distract the LLM or dilute the truly relevant information — this is why re-ranking (Section 6) exists, to filter down to the most relevant subset before generation.
4. **"A single retrieval pass is always sufficient"** — FALSE for multi-hop questions, as Section 5 and your Lab 1.5 result directly demonstrate (2% → 96% accuracy improvement from decomposition).
5. **"Vector similarity search always finds semantically relevant results"** — Not guaranteed. As shown in Section 3, poor preprocessing (missing stop-word removal) can produce misleadingly high similarity scores for irrelevant content — retrieval quality depends heavily on preprocessing choices, not just the embedding model.

---

## 9. Rapid-Fire Self-Check (MCQ Simulation)

1. What are the five main stages of a RAG pipeline, in order? *(Document → Chunking → Embedding → Vector Index → Retrieval → Generation)*
2. Why does `chunk_overlap` not always produce visible literal text overlap between chunks? *(The splitter still respects separator boundaries like paragraphs/newlines first — overlap is best-effort within those constraints, not a hard guarantee)*
3. What problem does "parent document expansion" solve? *(Retrieval works best on small, precise chunks for matching, but generation often needs more surrounding context — parent expansion retrieves the small chunk for matching, then expands to a wider parent context for the LLM)*
4. Why does decomposing a multi-hop question into sub-questions improve retrieval accuracy? *(A single query often can't retrieve all needed facts at once if they're spread across different documents — each sub-question gets its own focused retrieval pass)*
5. What's the practical difference between initial retrieval and re-ranking? *(Initial retrieval is fast/approximate, typically vector similarity across a large index; re-ranking uses a more expensive but more precise model, like a cross-encoder, to reorder just the top candidates)*

---

## Status
All computable concepts (chunking with a real overlap demonstration, end-to-end TF-IDF retrieval, grounded-vs-hallucinating response structure, decomposed multi-hop retrieval) verified with real executed code, including two genuine bugs caught and fixed during verification (missing stop-word removal, and an incorrect initial assumption about what `chunk_overlap` actually changes). GraphRAG is reference-only, matching your Neo4j lab environment, with your actual confirmed Lab 1.7 findings cited directly.

Ready for the companion **Cheatsheet — Topic 3** or straight into **Topic 4: LLM Fundamentals** whenever you want to continue.
