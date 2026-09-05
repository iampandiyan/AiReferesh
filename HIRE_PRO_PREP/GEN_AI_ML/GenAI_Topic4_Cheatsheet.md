# GenAI/AI-ML Cheatsheet — Topic 4 (LLM Fundamentals Libraries)

**Companion to:** GenAI_Topic4_LLM_Fundamentals.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

The `re` module used for the tokenization approximation is already covered in the Topic 2 cheatsheet — not repeated here. All examples below were executed for real.

---

## `numpy` — Softmax & Nucleus Sampling Math

**Top functions (the specific ones behind temperature/top-k/top-p, beyond what's in earlier cheatsheets):**

| Function | Explanation |
|---|---|
| `np.exp(x)` | Element-wise exponential — the core of the softmax formula |
| `np.max(x)` | Used to subtract the max before exponentiating, for numerical stability (prevents overflow on large logits) |
| `np.cumsum(x)` | Running cumulative sum — the basis of nucleus (top-p) sampling's "keep adding until threshold reached" logic |
| `np.searchsorted(sorted_arr, value)` | Binary search — finds the insertion index where `value` would fit into a sorted array; used here to find the smallest prefix whose cumulative sum reaches `p` |

**Verified example — the full softmax-with-temperature formula:**
```python
import numpy as np

def softmax_with_temperature(logits, temperature=1.0):
    logits = np.array(logits) / temperature
    exp_logits = np.exp(logits - np.max(logits))
    return exp_logits / np.sum(exp_logits)

print(softmax_with_temperature([2.0, 1.0, 0.5, 0.1], temperature=1.0))
# [0.5745 0.2114 0.1282 0.0859]
```

**Verified example — `cumsum` + `searchsorted` for top-p cutoff:**
```python
sorted_probs = np.array([0.5745, 0.2114, 0.1282, 0.0859])
cum = np.cumsum(sorted_probs)
print("cumulative:", cum)                     # [0.5745 0.7859 0.9141 1.    ]
print("searchsorted(0.9):", np.searchsorted(cum, 0.9))   # 2 -> need indices 0,1,2 (3 tokens) to reach 0.9
print("searchsorted(0.5):", np.searchsorted(cum, 0.5))   # 0 -> first token alone (0.5745) already exceeds 0.5
```

---

## `tiktoken` — Reference Only

**Not executed in this sandbox** — `tiktoken.get_encoding()` downloads its BPE merge file from `openaipublic.blob.core.windows.net` on first use, which this sandbox's network allowlist doesn't include. Confirmed with a real 403 error when attempted (see Topic 4, Section 1). Run this directly in your own environment:

```python
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")   # encoding used by GPT-3.5/4-era models
tokens = enc.encode("hello world")
print(tokens)                 # list of integer token IDs
print(enc.decode(tokens))     # back to original text
print(len(tokens))            # actual token count - what really counts against context limits
```

| Method | Explanation |
|---|---|
| `tiktoken.get_encoding(name)` | Load a specific named encoding (e.g., `cl100k_base` for GPT-4-era models, `o200k_base` for newer models) |
| `tiktoken.encoding_for_model(model_name)` | Convenience method — picks the right encoding automatically for a given model name |
| `.encode(text)` | Text → list of integer token IDs |
| `.decode(token_ids)` | Token IDs → back to text |
| `len(enc.encode(text))` | The standard way to get an accurate token count for budgeting against a context window |

---

## Status
2 fully verified numpy entries plus 1 clearly marked reference-only entry (`tiktoken`) with the actual error this sandbox produced, not a guessed one. Use alongside the main Topic 4 doc.
