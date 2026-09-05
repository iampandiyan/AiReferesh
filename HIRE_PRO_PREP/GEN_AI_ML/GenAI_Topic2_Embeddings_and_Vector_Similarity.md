# GenAI/AI-ML Principles — Topic 2: Embeddings & Vector Similarity

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

This topic connects directly to your RAG lab environment (all-MiniLM-L6-v2, FAISS, pgvector). Every math/algorithm concept below is demonstrated with real, executed code using numpy/sklearn/faiss (no external model download needed — those run without network access). The one exception is the actual `sentence-transformers` embedding call, which needs to download model weights from Hugging Face — not reachable from this sandbox's network. That code is given in full, formatted exactly like the runnable examples, for you to run directly in your own lab environment where the model is already cached.

---

## 1. What Is an Embedding?

An embedding is a vector (list of numbers) that represents the *meaning* of something — a word, sentence, or document — such that similar meanings end up close together in that vector space, and unrelated meanings end up far apart.

**Toy illustration (2D "meaning space" for intuition — real embeddings have hundreds of dimensions):**
```python
import numpy as np

# Imagine 2 dimensions represent [animal-ness, royalty-ness] purely for intuition
king  = np.array([0.2, 0.9])
queen = np.array([0.2, 0.85])
dog   = np.array([0.95, 0.05])

print("king:", king, "| queen:", queen, "| dog:", dog)
```
Output: `king: [0.2 0.9] | queen: [0.2  0.85] | dog: [0.95 0.05]`
`king` and `queen` sit close together in this space; `dog` sits far away — that's the entire idea of an embedding in one picture.

---

## 2. Cosine Similarity vs L2 (Euclidean) Distance

**Cosine similarity** measures the angle between two vectors — it asks "do these point in the same direction?" Range: -1 (opposite) to 1 (identical direction), with 0 meaning orthogonal/unrelated.

```python
def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

print("cosine(king, queen):", round(cosine_sim(king, queen), 4))
print("cosine(king, dog):", round(cosine_sim(king, dog), 4))
```
Output:
```
cosine(king, queen): 0.9999
cosine(king, dog): 0.2679
```

**L2 (Euclidean) distance** measures the straight-line distance between two points — it asks "how far apart are these?" Range: 0 (identical) to infinity.

```python
def l2_dist(a, b):
    return np.linalg.norm(a - b)

print("L2(king, queen):", round(l2_dist(king, queen), 4))
print("L2(king, dog):", round(l2_dist(king, dog), 4))
```
Output:
```
L2(king, queen): 0.05
L2(king, dog): 1.1336
```

---

## 3. The Key Distinction: Cosine Ignores Magnitude, L2 Doesn't

This is one of the most commonly tested MCQ facts on this topic.

```python
v1 = np.array([1.0, 2.0])
v2 = np.array([2.0, 4.0])   # exact same direction as v1, just scaled 2x

print("cosine(v1, v2) [same direction, different magnitude]:", round(cosine_sim(v1, v2), 4))
print("L2(v1, v2):", round(l2_dist(v1, v2), 4))
```
Output:
```
cosine(v1, v2) [same direction, different magnitude]: 1.0
L2(v1, v2): 2.2361
```
Cosine similarity says these are *identical in meaning* (1.0 = perfect match) because it only cares about direction. L2 distance says they're clearly different points. **This is why cosine similarity is the standard choice for text embeddings** — a longer document isn't necessarily "different" from a shorter one about the same topic; direction (meaning) matters more than magnitude (roughly, "how much was said").

---

## 4. Normalized Vectors: Dot Product Becomes Cosine Similarity

When vectors are normalized to unit length (length = 1), the plain dot product equals cosine similarity exactly. This is why vector databases often normalize embeddings first — a plain dot product is cheaper to compute than the full cosine formula (no division needed at search time).

```python
def normalize(v):
    return v / np.linalg.norm(v)

king_n = normalize(king)
queen_n = normalize(queen)

print("dot product of normalized vectors:", round(np.dot(king_n, queen_n), 4))
print("cosine similarity (unnormalized):  ", round(cosine_sim(king, queen), 4))
```
Output:
```
dot product of normalized vectors: 0.9999
cosine similarity (unnormalized):   0.9999
```
Identical values confirm the identity — this is a genuine MCQ-testable fact, not just an implementation detail.

---

## 5. `sklearn.metrics.pairwise.cosine_similarity` — Computing a Full Similarity Matrix at Once

```python
from sklearn.metrics.pairwise import cosine_similarity

matrix = np.array([king, queen, dog])
sim_matrix = cosine_similarity(matrix)
print(np.round(sim_matrix, 4))
```
Output:
```
[[1.     0.9999 0.2679]
 [0.9999 1.     0.2799]
 [0.2679 0.2799 1.    ]]
```
The diagonal is always 1.0 (every vector is identical to itself) — a useful sanity check when debugging a similarity matrix.

---

## 6. Real Semantic Similarity with TF-IDF (Runs With No Network Needed)

TF-IDF isn't a modern neural embedding, but it IS a real, classic vectorization technique, and it demonstrates the same underlying idea (turn text into vectors, compare with cosine similarity) without needing a model download:

```python
from sklearn.feature_extraction.text import TfidfVectorizer

docs = [
    "The cat sat on the mat",
    "A cat was sitting on the mat",
    "The stock market crashed today",
]
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(docs)
sim = cosine_similarity(tfidf_matrix)

print("TF-IDF vector shape:", tfidf_matrix.shape)
print(np.round(sim, 4))
```
Output:
```
TF-IDF vector shape: (3, 11)
[[1.     0.5923 0.1646]
 [0.5923 1.     0.0828]
 [0.1646 0.0828 1.    ]]
```
Sentences 0 and 1 (both about a cat on a mat) score 0.59 similarity — far higher than either scores against the unrelated stock market sentence (0.16 and 0.08). This is the same pattern modern embeddings exploit, just with a much cruder, keyword-based method.

---

## 7. FAISS — Real Vector Index and Nearest-Neighbor Search

This runs for real without needing any model download — FAISS itself just needs example vectors, which can be random for demonstrating the mechanics:

```python
import faiss

np.random.seed(42)
dim = 8
vectors = np.random.random((100, dim)).astype('float32')

index = faiss.IndexFlatL2(dim)   # brute-force exact L2 search
index.add(vectors)
print("index.ntotal:", index.ntotal)

query = vectors[0:1]
distances, indices = index.search(query, k=5)
print("nearest neighbor indices:", indices)
print("nearest neighbor distances:", np.round(distances, 4))
```
Output:
```
index.ntotal: 100
nearest neighbor indices: [[ 0 23 53 39 27]]
nearest neighbor distances: [[0.     0.2564 0.487  0.5957 0.785 ]]
```
Index 0 finds itself first with distance 0 (querying with its own vector) — a useful sanity check when validating any vector search setup, including your pgvector lab work.

**FAISS with cosine similarity (normalize vectors, then use inner product):**
```python
normalized_vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
index_ip = faiss.IndexFlatIP(dim)   # inner product index
index_ip.add(normalized_vectors)

query_n = normalized_vectors[0:1]
sims, idxs = index_ip.search(query_n, k=3)
print("top-3 cosine-similar indices:", idxs)
print("top-3 cosine similarities:", np.round(sims, 4))
```
Output:
```
top-3 cosine-similar indices: [[ 0 23 53]]
top-3 cosine similarities: [[1.     0.9525 0.9081]]
```
**MCQ-relevant fact:** `IndexFlatL2` and `IndexFlatIP` are both *brute-force, exact* search — O(n) per query. Your lab series' HNSW-based pgvector speedup (confirmed ~35x at 5,000 rows) exists precisely because brute-force doesn't scale — approximate nearest-neighbor structures like HNSW trade a small amount of accuracy for massive speed gains at larger scale.

---

## 8. Real Sentence Embeddings — Reference Code for Your Environment

The code below is the actual pattern from your RAG lab series. It is **not executed in this sandbox** — the `sentence-transformers` library needs to download model weights from Hugging Face, and this sandbox's network only allows a fixed list of domains (PyPI, GitHub, npm, etc.) that doesn't include Hugging Face. Run this directly in your `rag-labs` conda environment, where the model is already cached from your earlier lab work:

```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

sentences = [
    "The cat sat on the mat",
    "A cat was sitting on the mat",
    "The stock market crashed today",
]

embeddings = model.encode(sentences)
print("embedding shape:", embeddings.shape)   # expect (3, 384) - MiniLM-L6-v2 produces 384-dim vectors

sim = cosine_similarity(embeddings)
print(np.round(sim, 4))
# expect sentence 0 & 1 to score much higher similarity than either vs sentence 2,
# and noticeably higher than the TF-IDF version above since real embeddings
# capture semantic meaning, not just shared keywords
```

**Together AI embedding call (matches your lab environment's provider setup):**
```python
from together import Together
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

client = Together()  # reads TOGETHER_API_KEY from environment

response = client.embeddings.create(
    model="togethercomputer/m2-bert-80M-8k-retrieval",
    input=["The cat sat on the mat", "A cat was sitting on the mat"]
)

emb1 = np.array(response.data[0].embedding)
emb2 = np.array(response.data[1].embedding)
sim = cosine_similarity([emb1], [emb2])
print("similarity:", sim[0][0])
```

---

## 9. Dimensionality Trade-offs (Conceptual — No Code Needed)

| Model | Dimensions | Trade-off |
|---|---|---|
| `all-MiniLM-L6-v2` | 384 | Fast, small storage footprint, good enough semantic quality for most RAG use cases — your lab environment's choice |
| OpenAI `text-embedding-ada-002` | 1536 | Higher quality on some benchmarks, but 4x storage, slower similarity search at scale |
| OpenAI `text-embedding-3-large` | 3072 (configurable smaller) | Even higher dimensional, supports dimension reduction via truncation |

**MCQ-relevant point:** higher dimensionality is NOT strictly better — it increases storage cost and search latency, and past a certain point offers diminishing semantic quality returns. This is a real engineering trade-off, not just "bigger number wins."

---

## 10. Traps & Misconceptions (MCQ-Relevant)

1. **"Cosine similarity and cosine distance are the same thing"** — FALSE. Cosine distance = 1 − cosine similarity. A similarity of 1.0 (identical) corresponds to a distance of 0.
2. **"L2 distance and cosine similarity always rank results the same way"** — FALSE in general (only guaranteed identical ranking when all vectors are normalized to the same length — see Section 4).
3. **"Embeddings capture exact keyword matches"** — FALSE, that's what TF-IDF/BM25 do. Embeddings capture semantic meaning — "car" and "automobile" can have high similarity despite sharing no characters.
4. **"A higher-dimensional embedding is always more accurate"** — FALSE, see Section 9 — it's a trade-off against storage and speed, not a free upgrade.
5. **"FAISS's `IndexFlatL2` scales well to millions of vectors"** — FALSE, it's brute-force exact search, O(n) per query — this is exactly why your lab series' HNSW-based pgvector approach exists for anything beyond small-to-medium scale.

---

## 11. Rapid-Fire Self-Check (MCQ Simulation)

1. What's the range of cosine similarity values? *(-1 to 1)*
2. If vector A is exactly the same direction as vector B but twice as long, what's their cosine similarity? *(1.0 — cosine ignores magnitude entirely)*
3. What operation becomes equivalent to cosine similarity once vectors are normalized to unit length? *(Plain dot product)*
4. Why might a production RAG system choose HNSW indexing over FAISS's `IndexFlatL2`? *(Flat/brute-force search is O(n) per query — doesn't scale; HNSW trades a small accuracy loss for approximate search that's dramatically faster at scale)*
5. Name one reason a team might choose a 384-dimension embedding model over a 1536-dimension one. *(Lower storage cost and faster similarity search, often with only a small quality trade-off for the given use case)*

---

## Status
All math/algorithm concepts (cosine similarity, L2 distance, normalization, TF-IDF, FAISS search) verified with real executed code. The `sentence-transformers` and Together AI embedding calls are given as complete, copy-ready code for your own environment, clearly marked as not executed here due to this sandbox's network restrictions (Hugging Face isn't in the allowed domain list) — consistent with your lab series' standing rule of disclosing limitations honestly rather than silently substituting something else.

Ready for the companion **Cheatsheet — Topic 2** or straight into **Topic 3: RAG Architecture** whenever you want to continue.
