# GenAI/AI-ML Principles — Topic 4: LLM Fundamentals

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Tokenization's real library (`tiktoken`) needs a network host this sandbox can't reach — that failure is shown honestly below, with full reference code for your own environment. Temperature, top-k, and top-p, however, are pure math — genuinely computed here with numpy, not simulated or described from memory.

---

## 1. Tokenization

An LLM doesn't process raw characters or whole words — it processes **tokens**, which are typically sub-word pieces learned from a large corpus (Byte-Pair Encoding, or BPE). A common word might be one token; a rare or long word might be split into several.

**Attempting the real tokenizer — honest failure due to this sandbox's network restrictions:**
```python
import tiktoken
enc = tiktoken.get_encoding('cl100k_base')
print(enc.encode('hello world'))
```
Actual error when run here:
```
requests.exceptions.HTTPError: 403 Client Error: Forbidden for url:
https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken
```
This is a genuine network restriction (this sandbox only allows a fixed list of domains — PyPI, GitHub, npm, etc. — and OpenAI's encoding-file host isn't on it), not a code bug. The code above is correct and will work in your own environment.

**Simplified approximation used instead (to show the word-vs-token distinction with something actually runnable):**
```python
import re

def simple_tokenize_approx(text):
    # crude approximation - splits on word boundaries and punctuation only.
    # Real BPE tokenizers would further split long/rare words into sub-pieces
    # like "tokenization" -> ["token", "ization"] - this version can't do that.
    return re.findall(r"\w+|[^\w\s]", text)

text = "Tokenization isn't the same as word-splitting!"
tokens = simple_tokenize_approx(text)
print("word count:", len(text.split()))
print("approx token count:", len(tokens))
print("tokens:", tokens)
```
Output:
```
word count: 6
approx token count: 11
tokens: ['Tokenization', 'isn', "'", 't', 'the', 'same', 'as', 'word', '-', 'splitting', '!']
```
Even this crude approximation shows tokens ≠ words — contractions and punctuation become separate tokens. **What this approximation genuinely cannot show** (an honest limitation, not glossed over): real BPE would also split long/rare words like "antidisestablishmentarianism" into multiple sub-word tokens, and non-Latin scripts often tokenize far less efficiently per character than English — both are real, MCQ-relevant facts about tokenization that this simplified demo can't visually prove without the real library.

---

## 2. Context Window

The context window is the maximum number of **tokens** (input + output combined) a model can process in a single call. Exceeding it requires truncation or chunking (connecting directly to Topic 3's chunking strategies).

```python
def fits_in_context(token_count, max_context=4096, reserved_for_output=512):
    available = max_context - reserved_for_output
    return token_count <= available, available

doc_tokens = 3500
fits, available = fits_in_context(doc_tokens)
print(f"document tokens={doc_tokens}, available budget={available}, fits={fits}")

doc_tokens2 = 4000
fits2, _ = fits_in_context(doc_tokens2)
print(f"document tokens={doc_tokens2}, fits={fits2}")
```
Output:
```
document tokens=3500, available budget=3584, fits=True
document tokens=4000, fits=False
```
**MCQ-relevant point:** the context window is shared between input AND output — reserving budget for the expected response length (as `reserved_for_output` does above) is a real, common production pattern, not just a theoretical concern.

---

## 3. Temperature — The Real Math Behind It

Temperature controls how "confident vs random" a model's next-token choice is, by reshaping the probability distribution over candidate tokens before sampling. This is genuinely computable without any LLM — it's just the softmax function with a scaling parameter:

```python
import numpy as np

def softmax_with_temperature(logits, temperature=1.0):
    logits = np.array(logits) / temperature
    exp_logits = np.exp(logits - np.max(logits))  # subtract max for numerical stability
    return exp_logits / np.sum(exp_logits)

logits = [2.0, 1.0, 0.5, 0.1]   # raw model scores for 4 candidate next-tokens
labels = ["the", "a", "an", "this"]

for temp in [0.1, 1.0, 2.0]:
    probs = softmax_with_temperature(logits, temp)
    print(f"temperature={temp}: " + ", ".join(f"{l}={p:.4f}" for l, p in zip(labels, probs)))
```
Output:
```
temperature=0.1: the=1.0000, a=0.0000, an=0.0000, this=0.0000
temperature=1.0: the=0.5745, a=0.2114, an=0.1282, this=0.0859
temperature=2.0: the=0.4056, a=0.2460, an=0.1916, this=0.1569
```
This is the real mechanism, not an analogy: **low temperature (0.1) makes the distribution sharply peaked** — "the" is picked almost deterministically. **High temperature (2.0) flattens the distribution** — the gap between "the" and "this" shrinks dramatically, making less-likely tokens meaningfully more probable. This is exactly why temperature=0 is often used for factual/deterministic tasks and higher temperatures for creative tasks.

---

## 4. Decoding Strategies: Top-k and Top-p (Nucleus) Sampling

These are filters applied to the probability distribution before sampling, to avoid ever picking a very-low-probability (often nonsensical) token.

**Top-k — keep only the k highest-probability candidates, renormalize:**
```python
def top_k_filter(probs, labels, k=2):
    idx = np.argsort(probs)[::-1][:k]
    filtered_probs = probs[idx]
    filtered_probs = filtered_probs / filtered_probs.sum()   # renormalize so it sums to 1 again
    return [(labels[i], round(p, 4)) for i, p in zip(idx, filtered_probs)]

probs = softmax_with_temperature(logits, temperature=1.0)
print("full distribution:", dict(zip(labels, np.round(probs,4))))
print("top-2 filtered:", top_k_filter(probs, labels, k=2))
```
Output:
```
full distribution: {'the': 0.5745, 'a': 0.2114, 'an': 0.1282, 'this': 0.0859}
top-2 filtered: [('the', 0.7311), ('a', 0.2689)]
```
Notice "an" and "this" are entirely excluded, and the remaining two probabilities are rescaled to sum to 1.

**Top-p (nucleus sampling) — keep the smallest set of tokens whose cumulative probability reaches p:**
```python
def top_p_filter(probs, labels, p=0.9):
    idx = np.argsort(probs)[::-1]
    sorted_probs = probs[idx]
    cumulative = np.cumsum(sorted_probs)
    cutoff = np.searchsorted(cumulative, p) + 1
    chosen_idx = idx[:cutoff]
    chosen_probs = probs[chosen_idx]
    chosen_probs = chosen_probs / chosen_probs.sum()
    return [(labels[i], round(pr, 4)) for i, pr in zip(chosen_idx, chosen_probs)]

print("top-p=0.9:", top_p_filter(probs, labels, p=0.9))
print("top-p=0.5:", top_p_filter(probs, labels, p=0.5))
```
Output:
```
top-p=0.9: [('the', 0.6285), ('a', 0.2312), ('an', 0.1402)]
top-p=0.5: [('the', 1.0)]
```
**Key MCQ distinction from top-k:** top-p's cutoff size adapts to the shape of the distribution — with `p=0.5` here, "the" alone already exceeds that cumulative threshold, so only one token survives. Top-k always keeps a fixed count regardless of how the probability mass is actually distributed; top-p adapts dynamically.

---

## 5. Prompt Engineering Patterns

**Zero-shot — no examples given, just the task:**
```python
def zero_shot_prompt(task):
    return f"Classify the sentiment of this review as positive or negative:\n\n{task}"

print(zero_shot_prompt("The food was okay, nothing special."))
```
Output:
```
Classify the sentiment of this review as positive or negative:

The food was okay, nothing special.
```

**Few-shot — examples included to demonstrate the expected pattern:**
```python
def few_shot_prompt(task, examples):
    prompt = "Classify the sentiment of each review as positive or negative.\n\n"
    for ex_text, ex_label in examples:
        prompt += f"Review: {ex_text}\nSentiment: {ex_label}\n\n"
    prompt += f"Review: {task}\nSentiment:"
    return prompt

examples = [("This product is amazing!", "positive"), ("Terrible experience, avoid.", "negative")]
print(few_shot_prompt("The food was okay, nothing special.", examples))
```
Output:
```
Classify the sentiment of each review as positive or negative.

Review: This product is amazing!
Sentiment: positive

Review: Terrible experience, avoid.
Sentiment: negative

Review: The food was okay, nothing special.
Sentiment:
```

**Chat message format (system/user/assistant roles) — the structure behind every modern chat-based LLM API call:**
```python
def build_chat_messages(system_prompt, user_message, history=None):
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages

messages = build_chat_messages(
    "You are a helpful assistant that answers concisely.",
    "What is chunking in RAG?",
)
for m in messages:
    print(m)
```
Output:
```
{'role': 'system', 'content': 'You are a helpful assistant that answers concisely.'}
{'role': 'user', 'content': 'What is chunking in RAG?'}
```

**Chain-of-thought (CoT) — prompting the model to reason step by step before answering:**
```python
cot_prompt = """Question: If a train travels 60 km in 1.5 hours, what is its average speed?
Let's think step by step.
"""
print(cot_prompt)
```
The phrase `"Let's think step by step"` is the classic CoT trigger — it encourages the model to externalize intermediate reasoning before committing to a final answer, which measurably improves accuracy on multi-step reasoning tasks compared to asking for the answer directly.

---

## 6. Traps & Misconceptions (MCQ-Relevant)

1. **"Token count equals word count"** — FALSE, as shown in Section 1. Punctuation, contractions, rare words, and non-Latin scripts all commonly produce more tokens than words.
2. **"Temperature=0 means fully random output"** — FALSE, backwards. Temperature=0 (or very low) means near-deterministic, most-likely-token-every-time output. Higher temperature increases randomness.
3. **"Context window only limits the input prompt"** — FALSE. It's a shared budget across input AND output tokens combined (Section 2).
4. **"Top-k and top-p do the same thing"** — FALSE. Top-k always keeps a fixed number of candidates; top-p keeps a variable number based on cumulative probability mass, adapting to how confident/uncertain the distribution is (Section 4).
5. **"Few-shot prompting always outperforms zero-shot"** — Not universally true. Few-shot helps most when the task format is ambiguous or unusual; for simple, well-understood tasks it mainly adds token cost without meaningfully improving accuracy.

---

## 7. Rapid-Fire Self-Check (MCQ Simulation)

1. Does a lower temperature make output more or less deterministic? *(More deterministic — the probability distribution becomes sharply peaked around the most likely token)*
2. What does the context window budget limit — input only, output only, or both combined? *(Both combined)*
3. What's the key structural difference between top-k and top-p sampling? *(Top-k keeps a fixed count of candidates; top-p keeps a variable count based on cumulative probability threshold)*
4. What's the classic trigger phrase for chain-of-thought prompting? *("Let's think step by step" or equivalent instruction to reason before answering)*
5. In a chat-based LLM API call, what are the three standard message roles? *(system, user, assistant)*

---

## Status
Tokenization's real library failure is shown honestly with the actual error, not hidden. Temperature, top-k, and top-p are demonstrated with genuine computed math (softmax, cumulative sums) — not descriptions, actual numbers you can verify by re-running the code. Prompt engineering patterns are real, executable string-construction code.

Ready for the companion **Cheatsheet — Topic 4** or straight into **Topic 5: Vector Databases** whenever you want to continue.
