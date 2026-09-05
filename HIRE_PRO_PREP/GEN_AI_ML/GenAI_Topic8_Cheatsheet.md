# GenAI/AI-ML Cheatsheet — Topic 8 (Evaluation Metrics Libraries)

**Companion to:** GenAI_Topic8_Evaluation_Metrics.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

---

## `rouge_score.rouge_scorer.RougeScorer`

**Initialization:**
```python
from rouge_score import rouge_scorer
scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
```

**Top parameters/methods:**
| Parameter/Method | Explanation |
|---|---|
| `rouge1` / `rouge2` | Unigram / bigram overlap between candidate and reference |
| `rougeL` | Longest Common Subsequence-based overlap — rewards matching word order, not just word presence |
| `use_stemmer=True` | Reduces words to their stem first (e.g., "running" → "run") so minor inflection differences don't hurt the score |
| `.score(reference, candidate)` | Returns a dict of `Score(precision=, recall=, fmeasure=)` per ROUGE type |

**Verified example:**
```python
scorer = rouge_scorer.RougeScorer(['rouge1','rougeL'], use_stemmer=True)
print(scorer.score('the cat sat on the mat', 'the cat sat on a mat'))
```
Output: `{'rouge1': Score(precision=0.8333, recall=0.8333, fmeasure=0.8333), 'rougeL': Score(precision=0.8333, recall=0.8333, fmeasure=0.8333)}`

---

## `nltk.translate.bleu_score.sentence_bleu`

**Initialization:**
```python
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `sentence_bleu([reference_tokens], candidate_tokens)` | Reference must be a LIST of token lists (supports multiple valid references) |
| `smoothing_function=SmoothingFunction().method1` | Prevents BLEU from scoring exactly 0 when there's no 4-gram match at all — near-essential for short sentences, since raw BLEU is harsh on brevity |

**Verified example:**
```python
ref = [['the','cat','sat','on','the','mat']]
cand = ['the','cat','sat','on','a','mat']
print(sentence_bleu(ref, cand, smoothing_function=SmoothingFunction().method1))
```
Output: `0.5373`

---

## `transformers.pipeline` (NLI for faithfulness) — Reference Only

**Not executed in this sandbox** — requires downloading a model from Hugging Face.

```python
from transformers import pipeline

nli_pipeline = pipeline("text-classification", model="microsoft/deberta-large-mnli")
result = nli_pipeline(f"{context} [SEP] {answer}")
print(result)
```

| Usage | Explanation |
|---|---|
| `pipeline("text-classification", model=...)` | Loads a pretrained NLI model that classifies a (premise, hypothesis) pair as entailment/neutral/contradiction |
| High "entailment" score | Signals the context genuinely supports the answer — a stronger faithfulness signal than word overlap |

---

## `ragas.evaluate` — Reference Only

**Not executed in this sandbox** — needs a live LLM and hit a dependency error on import here (see main Topic 8 doc, Section 7).

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset

dataset = Dataset.from_dict({
    "question": [...], "answer": [...], "contexts": [[...]], "ground_truth": [...],
})
results = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision, context_recall])
print(results)
```

| Metric | Explanation |
|---|---|
| `faithfulness` | LLM-judged: is every claim in the answer supported by retrieved context? |
| `answer_relevancy` | LLM-judged: does the answer address the actual question? |
| `context_precision` / `context_recall` | LLM-judged: quality of the retrieved context set itself |

---

## Status
2 fully verified entries (`rouge_score`, `nltk` BLEU) plus 2 clearly marked reference-only entries (`transformers` NLI, `ragas`) for your own environment.
