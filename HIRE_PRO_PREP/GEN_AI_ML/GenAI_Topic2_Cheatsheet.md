# GenAI/AI-ML Cheatsheet — Topic 2 (Embeddings & Vector Similarity Libraries)

**Companion to:** GenAI_Topic2_Embeddings_and_Vector_Similarity.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

All examples below were executed for real — outputs shown are actual, not invented. The two reference-only entries at the end (`sentence-transformers`, Together AI) are marked exactly as such, matching Topic 2's disclosed network limitation.

---

## `numpy.linalg`

**Initialization:**
```python
import numpy as np
```

**Top functions:**
| Function | Explanation |
|---|---|
| `np.linalg.norm(v)` | Magnitude (length) of a vector — the denominator in cosine similarity, and the whole calculation for L2 distance when applied to `(a - b)` |
| `np.dot(a, b)` | Dot product — numerator of cosine similarity, and equals cosine similarity directly once vectors are normalized |

**Verified example:**
```python
v = np.array([3.0, 4.0])
print(np.linalg.norm(v))    # 5.0  (classic 3-4-5 triangle)

a = np.array([1,2,3]); b = np.array([4,5,6])
print(np.dot(a,b))          # 32
```

---

## `sklearn.metrics.pairwise.cosine_similarity`

**Initialization:**
```python
from sklearn.metrics.pairwise import cosine_similarity
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `cosine_similarity(matrix)` | Computes the full pairwise similarity matrix for a set of vectors in one call — diagonal is always 1.0 |
| `cosine_similarity(matrix_a, matrix_b)` | Compares two different sets of vectors against each other (not just within one set) |

**Verified example:**
```python
X = np.array([[1,0],[0,1],[1,1]])
print(np.round(cosine_similarity(X), 4))
# [[1.     0.     0.7071]
#  [0.     1.     0.7071]
#  [0.7071 0.7071 1.    ]]
```

---

## `sklearn.metrics.pairwise.euclidean_distances`

**Initialization:**
```python
from sklearn.metrics.pairwise import euclidean_distances
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `euclidean_distances(matrix)` | Full pairwise L2 distance matrix — diagonal is always 0.0 (distance from a point to itself) |

**Verified example:**
```python
print(np.round(euclidean_distances(X), 4))
# [[0.     1.4142 1.    ]
#  [1.4142 0.     1.    ]
#  [1.     1.     0.    ]]
```

---

## `sklearn.feature_extraction.text.TfidfVectorizer`

**Initialization:**
```python
from sklearn.feature_extraction.text import TfidfVectorizer
vec = TfidfVectorizer()
```

**Top methods:**
| Method | Explanation |
|---|---|
| `.fit_transform(docs)` | Learn vocabulary from the documents AND convert them to TF-IDF vectors in one call |
| `.get_feature_names_out()` | The vocabulary — which column corresponds to which word |
| `.toarray()` | Convert the sparse matrix output to a regular dense numpy array (only do this for small data — sparse matrices exist precisely to avoid this memory cost at scale) |

**Verified example:**
```python
docs = ["cat sat mat", "dog ran fast"]
tfidf = vec.fit_transform(docs)
print(tfidf.shape)                        # (2, 6)
print(vec.get_feature_names_out())        # ['cat' 'dog' 'fast' 'mat' 'ran' 'sat']
print(np.round(tfidf.toarray()[0], 4))    # [0.5774 0. 0. 0.5774 0. 0.5774]
```

---

## `faiss.IndexFlatL2`

**Initialization:**
```python
import faiss
dim = 4
index = faiss.IndexFlatL2(dim)
```

**Top methods:**
| Method | Explanation |
|---|---|
| `.add(vectors)` | Add vectors to the index |
| `.search(query, k)` | Return the k nearest neighbors by L2 distance — brute-force exact search |
| `.ntotal` | Number of vectors currently in the index |

**Verified example:**
```python
vecs = np.random.RandomState(0).random((10, dim)).astype('float32')
index.add(vecs)
print(index.ntotal)   # 10

D, I = index.search(vecs[:1], k=3)
print(np.round(D,4), I)   # distances: [[0. 0.1487 0.1681]]  indices: [[0 9 1]]
```

---

## `faiss.IndexFlatIP`

**Initialization:**
```python
index_ip = faiss.IndexFlatIP(dim)
```

**Top usage:**
| Usage | Explanation |
|---|---|
| Inner-product search on normalized vectors | Equivalent to cosine similarity search — normalize vectors first (see Topic 2, Section 4), since raw inner product alone is magnitude-sensitive |

**Verified example:**
```python
norm_vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
index_ip.add(norm_vecs)
D2, I2 = index_ip.search(norm_vecs[:1], k=3)
print(np.round(D2,4), I2)   # similarities: [[1. 0.9741 0.9601]]  indices: [[0 9 5]]
```

---

## `faiss.IndexIVFFlat` (approximate index — the pattern behind your lab's HNSW speedup)

**Initialization:**
```python
quantizer = faiss.IndexFlatL2(dim)
nlist = 5   # number of clusters/cells to partition vectors into
index_ivf = faiss.IndexIVFFlat(quantizer, dim, nlist)
index_ivf.train(vecs)   # IVF indexes must be trained before adding data - unlike Flat indexes
index_ivf.add(vecs)
```

**Top methods:**
| Method | Explanation |
|---|---|
| `.train(vectors)` | Required step for IVF-based indexes — learns the cluster centroids used to narrow the search space |
| `.nprobe` | How many clusters to search at query time — higher = more accurate but slower, this is the accuracy/speed knob |
| `.search(query, k)` | Approximate nearest-neighbor search — only checks vectors in the most relevant clusters, not the whole index |

**Verified example (with an honest real warning shown, not hidden):**
```python
index_ivf.nprobe = 2
D3, I3 = index_ivf.search(vecs[:1], k=3)
print(np.round(D3,4), I3)
```
Output:
```
WARNING clustering 10 points to 5 centroids: please provide at least 195 training points
[[0. 0.1487 0.1681]] [[0 9 1]]
```
This warning is real and instructive — FAISS itself is telling you that 10 training points is too few for 5 clusters to be meaningful (rule of thumb: ~39 points per centroid minimum). At this toy scale the result happens to match the brute-force search, but at production scale with too little training data, IVF accuracy degrades — a genuine operational trap worth knowing, not just an MCQ fact.

---

## `sentence_transformers.SentenceTransformer` — Reference Only

**Not executed in this sandbox** — requires downloading model weights from Hugging Face, which isn't reachable from here. Run directly in your `rag-labs` environment where the model is already cached.

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(["some text", "more text"])
```

| Method | Explanation |
|---|---|
| `SentenceTransformer(model_name)` | Loads a pretrained embedding model |
| `.encode(list_of_strings)` | Returns a numpy array of embeddings, one row per input string — shape `(n, 384)` for MiniLM-L6-v2 |

---

## `together.Together` (embeddings endpoint) — Reference Only

**Not executed in this sandbox** — requires a live API call to Together AI. Run directly in your lab environment where `TOGETHER_API_KEY` is already configured.

```python
from together import Together

client = Together()
response = client.embeddings.create(
    model="togethercomputer/m2-bert-80M-8k-retrieval",
    input=["some text"]
)
```

| Method | Explanation |
|---|---|
| `client.embeddings.create(model=, input=)` | Returns embedding vectors for a list of input strings via the Together AI API |
| `response.data[i].embedding` | The actual vector for the i-th input string |

---

## Status
7 fully verified entries (numpy, sklearn x3, FAISS x3) plus 2 clearly marked reference-only entries for your own environment. Use alongside the main Topic 2 doc.
