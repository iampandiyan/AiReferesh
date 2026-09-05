# GenAI/AI-ML Cheatsheet — Topic 11 (Transformer Building Blocks)

**Companion to:** GenAI_Topic11_Transformers.md
**Format:** This topic is from-scratch numpy code rather than a third-party library, so this cheatsheet covers the reusable core functions instead of package APIs — Purpose → Signature → One verified runnable example per entry.

---

## `softmax(x, axis=-1)`

**Purpose:** Converts raw scores (logits) into a probability distribution that sums to 1 — used both for attention weights and final output probabilities.

```python
def softmax(x, axis=-1):
    x = x - np.max(x, axis=axis, keepdims=True)   # numerical stability - prevents overflow
    e = np.exp(x)
    return e / np.sum(e, axis=axis, keepdims=True)
```

**Verified example:**
```python
x = np.array([[1.0, 2.0, 3.0], [10.0, 1.0, 1.0]])
print(softmax(x))
# [[0.09   0.2447 0.6652]
#  [0.9998 0.0001 0.0001]]
```
Notice the second row: a large gap between 10.0 and 1.0 produces an almost one-hot distribution — this is exactly the effect the `/sqrt(d_k)` scaling in attention (Topic 11, Section 2) is designed to prevent from happening too aggressively.

---

## `layer_norm(x, eps=1e-5)`

**Purpose:** Normalizes each individual example's features to zero mean, unit variance — stabilizes training in deep networks, applied after each residual connection in a transformer block.

```python
def layer_norm(x, eps=1e-5):
    mean = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    return (x - mean) / np.sqrt(var + eps)
```

**Verified example:**
```python
x = np.array([[1.0, 2.0, 3.0], [10.0, 1.0, 1.0]])
print(layer_norm(x))
# [[-1.2247  0.      1.2247]
#  [ 1.4142 -0.7071 -0.7071]]
```
Each ROW is independently normalized (mean≈0, unit variance) — this is the key distinction from batch norm, which would normalize down COLUMNS across the batch instead.

---

## `relu(x)`

**Purpose:** The standard non-linear activation in a transformer's feedforward sub-layer — zeroes out negative values, passes positive values unchanged.

```python
def relu(x):
    return np.maximum(0, x)
```

**Verified example:**
```python
print(relu(np.array([-2, -1, 0, 1, 2])))   # [0 0 0 1 2]
```

---

## `positional_encoding(seq_len, d_model)`

**Purpose:** Generates a unique sinusoidal pattern per sequence position, added to token embeddings to inject order information (see Topic 11, Section 3 for full output and rationale).

```python
def positional_encoding(seq_len, d_model):
    pe = np.zeros((seq_len, d_model))
    position = np.arange(seq_len)[:, None]
    div_term = np.exp(np.arange(0, d_model, 2) * -(np.log(10000.0) / d_model))
    pe[:, 0::2] = np.sin(position * div_term)
    pe[:, 1::2] = np.cos(position * div_term)
    return pe
```

---

## Scaled Dot-Product Attention (the core pattern)

**Purpose:** The central mechanism — compute a weighted average of values, weighted by query-key similarity.

```python
def attention(Q, K, V, d_k):
    scores = Q @ K.T / np.sqrt(d_k)
    weights = softmax(scores, axis=-1)
    return weights @ V, weights
```

**Verified example (from Topic 11, Section 2):**
```python
Q = np.array([[1.0, 0.0], [0.0, 1.0]])
K = np.array([[1.0, 0.0], [0.0, 1.0]])
V = np.array([[10.0, 0.0], [0.0, 20.0]])
output, weights = attention(Q, K, V, d_k=2)
print(weights)   # [[0.6698 0.3302] [0.3302 0.6698]]
print(output)    # [[ 6.6976  6.6048] [ 3.3024 13.3952]]
```

---

## Status
5 core reusable functions verified with real output — these are the exact building blocks used to construct and train the full mini-transformer in the main Topic 11 document.
