# GenAI/AI-ML Principles — Topic 8: Evaluation Metrics for GenAI

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Retrieval metrics (Precision@k, Recall@k, MRR, NDCG) and text-similarity metrics (ROUGE, BLEU) are pure math/string comparison — genuinely computed here with real numbers. RAGAS's LLM-judged metrics (faithfulness, answer relevancy, context precision/recall) fundamentally require a live LLM to score outputs, so that section gives complete, copy-ready code for your environment, with the actual dependency error this sandbox hit shown honestly rather than hidden.

---

## 1. Why GenAI Evaluation Is Different From Traditional ML Evaluation

Classification metrics (precision/recall/F1 — Topic 1) work when there's a single correct label. GenAI systems produce open-ended text and rank retrieved documents, so evaluation needs metrics for: **ranking quality** (did retrieval surface the right documents, in a good order?), **text similarity** (does the generated answer resemble a reference answer?), and **faithfulness** (is the generated answer actually supported by what was retrieved, or did the model hallucinate?).

---

## 2. Precision@k and Recall@k — Retrieval Ranking Quality

```python
def precision_at_k(retrieved, relevant, k):
    retrieved_k = retrieved[:k]
    hits = len(set(retrieved_k) & set(relevant))
    return hits / k

def recall_at_k(retrieved, relevant, k):
    retrieved_k = retrieved[:k]
    hits = len(set(retrieved_k) & set(relevant))
    return hits / len(relevant) if relevant else 0.0

retrieved_docs = ["doc1", "doc5", "doc3", "doc7", "doc2"]
relevant_docs = {"doc1", "doc2", "doc3"}   # ground truth relevant docs for this query

for k in [1, 3, 5]:
    p = precision_at_k(retrieved_docs, relevant_docs, k)
    r = recall_at_k(retrieved_docs, relevant_docs, k)
    print(f"k={k}: precision@{k}={p:.4f}  recall@{k}={r:.4f}")
```
Output:
```
k=1: precision@1=1.0000  recall@1=0.3333
k=3: precision@3=0.6667  recall@3=0.6667
k=5: precision@5=0.6000  recall@5=1.0000
```
**MCQ-relevant pattern:** precision tends to decrease and recall tends to increase as k grows — this is the standard precision/recall trade-off, now applied to retrieval rather than classification. At k=5 you've retrieved every relevant doc (recall=1.0) but diluted with irrelevant ones (precision drops to 0.6).

---

## 3. Mean Reciprocal Rank (MRR) — How Quickly Was the First Relevant Result Found?

```python
def reciprocal_rank(retrieved, relevant):
    for i, doc in enumerate(retrieved):
        if doc in relevant:
            return 1 / (i + 1)
    return 0.0

queries_results = [
    (["doc1", "doc2", "doc3"], {"doc2"}),          # first relevant hit at rank 2
    (["doc5", "doc1", "doc2"], {"doc1", "doc2"}),  # first relevant hit at rank 2
    (["doc9", "doc8", "doc7"], {"doc1"}),          # no relevant hit at all
]
rrs = [reciprocal_rank(r, rel) for r, rel in queries_results]
print("individual reciprocal ranks:", rrs)
print("MRR:", round(sum(rrs)/len(rrs), 4))
```
Output:
```
individual reciprocal ranks: [0.5, 0.5, 0.0]
MRR: 0.3333
```
MRR only cares about the position of the FIRST relevant result — useful for tasks like "find the one right answer" (e.g., a chatbot's top suggestion) rather than tasks needing many relevant documents.

---

## 4. NDCG (Normalized Discounted Cumulative Gain) — Graded Relevance + Position

Unlike precision/recall (binary relevant/not-relevant), NDCG handles **graded relevance** (e.g., a 0-3 scale) and penalizes relevant results appearing later in the ranking.

```python
import numpy as np

def dcg(relevance_scores):
    return sum(rel / np.log2(idx + 2) for idx, rel in enumerate(relevance_scores))

def ndcg(retrieved_relevance, ideal_relevance):
    actual_dcg = dcg(retrieved_relevance)
    ideal_dcg = dcg(sorted(ideal_relevance, reverse=True))
    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0

retrieved_relevance = [3, 0, 1, 2, 0]   # relevance scores in the order actually retrieved
ideal_relevance = [3, 0, 1, 2, 0]       # same documents, used to compute the best-possible ordering

print("DCG:", round(dcg(retrieved_relevance), 4))
print("NDCG:", round(ndcg(retrieved_relevance, ideal_relevance), 4))

worse_order = [0, 0, 1, 2, 3]   # same docs, but most relevant one buried last
print("NDCG (worse ordering, same docs):", round(ndcg(worse_order, ideal_relevance), 4))
```
Output:
```
DCG: 4.3614
NDCG: 0.9159
NDCG (worse ordering, same docs): 0.5296
```
Same set of documents, dramatically different NDCG (0.9159 vs 0.5296) purely from re-ordering — this is exactly why NDCG is preferred over simple precision/recall when ranking QUALITY (not just presence) matters, such as evaluating a re-ranker (Topic 3, Section 6).

---

## 5. ROUGE and BLEU — Text Similarity Metrics (Real Libraries, No Network Needed)

These compare generated text against a reference answer via n-gram overlap — genuinely computable without any LLM.

```python
from rouge_score import rouge_scorer

scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
reference = "RAG reduces hallucination by grounding answers in retrieved documents"
candidate_good = "RAG reduces hallucination by grounding responses in retrieved documents"
candidate_bad = "The weather today is sunny with a chance of rain"

print("good candidate ROUGE-1:", scorer.score(reference, candidate_good)['rouge1'])
print("bad candidate ROUGE-1:", scorer.score(reference, candidate_bad)['rouge1'])
```
Output:
```
good candidate ROUGE-1: Score(precision=0.8889, recall=0.8889, fmeasure=0.8889)
bad candidate ROUGE-1: Score(precision=0.0, recall=0.0, fmeasure=0.0)
```

```python
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

reference_tokens = [reference.split()]
smoothie = SmoothingFunction().method1
bleu_good = sentence_bleu(reference_tokens, candidate_good.split(), smoothing_function=smoothie)
bleu_bad = sentence_bleu(reference_tokens, candidate_bad.split(), smoothing_function=smoothie)
print("good candidate BLEU:", round(bleu_good, 4))
print("bad candidate BLEU:", round(bleu_bad, 4))
```
Output:
```
good candidate BLEU: 0.5969
bad candidate BLEU: 0
```
**MCQ-relevant caveat:** ROUGE/BLEU measure surface-level word overlap, not actual meaning. A paraphrased answer that's semantically identical but uses different words scores poorly on both — this is precisely why these traditional NLG metrics are increasingly supplemented (not replaced) by embedding-based or LLM-judged metrics for modern GenAI evaluation.

---

## 6. Hallucination Detection — Heuristic Demo + Real Production Approach

**Simple heuristic (real, computed here) — word-overlap between answer and retrieved context:**
```python
def simple_faithfulness_check(answer, context, threshold=0.5):
    answer_words = set(answer.lower().split())
    context_words = set(context.lower().split())
    overlap = len(answer_words & context_words) / len(answer_words) if answer_words else 0
    return overlap >= threshold, round(overlap, 4)

context = "RAG reduces hallucination by grounding answers in retrieved documents from a knowledge base."
grounded_answer = "RAG reduces hallucination by grounding answers in retrieved documents."
hallucinated_answer = "RAG was invented in 1823 and uses quantum computing to eliminate all errors."

print(simple_faithfulness_check(grounded_answer, context))
print(simple_faithfulness_check(hallucinated_answer, context))
```
Output:
```
(True, 0.8889)
(False, 0.1538)
```
**Honest limitation of this heuristic:** it's just word overlap — it would incorrectly flag a well-paraphrased, fully faithful answer as unfaithful (same weakness as ROUGE/BLEU above), and could be fooled by an answer that reuses context words in a logically wrong way. This is why production systems use one of:

**a) NLI (Natural Language Inference) models** — check whether the context "entails" the answer:
```python
# Full pattern for your environment - not executed here (needs model download)
from transformers import pipeline

nli_pipeline = pipeline("text-classification", model="microsoft/deberta-large-mnli")
result = nli_pipeline(f"{context} [SEP] {grounded_answer}")
print(result)   # expect a high "ENTAILMENT" score for a faithful answer
```

**b) RAGAS's LLM-judged faithfulness metric** — an LLM itself checks whether each claim in the answer is supported by the retrieved context.

---

## 7. RAGAS — Full Reference Code (Not Executed Here)

RAGAS's core metrics (`faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`) all use an LLM as a judge to score outputs — this fundamentally requires a live LLM call, which isn't available in this sandbox. Attempting to even import the library here surfaced a real dependency issue worth disclosing honestly:

```
ModuleNotFoundError: No module named 'langchain_community.chat_models.vertexai'
```
This is a separate problem from the network restriction — it's a missing optional dependency in `ragas`'s own import chain in this environment. In your lab environment (which likely already has compatible LangChain versions installed for your RAG work), this may not occur at all — worth checking your own `pip list` for version conflicts before assuming this specific error will reproduce.

**Full reference code for your environment:**
```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset

data = {
    "question": ["What does RAG do to reduce hallucination?"],
    "answer": ["RAG grounds answers in retrieved documents from a knowledge base."],
    "contexts": [["RAG reduces hallucination by grounding answers in retrieved documents."]],
    "ground_truth": ["RAG reduces hallucination through retrieval-grounded generation."],
}
dataset = Dataset.from_dict(data)

results = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
)
print(results)
# Expect a dict-like result with scores per metric, e.g.:
# {'faithfulness': 0.92, 'answer_relevancy': 0.88, 'context_precision': 0.95, 'context_recall': 0.90}
```

| Metric | What it measures |
|---|---|
| `faithfulness` | Is every claim in the answer actually supported by the retrieved context? (the direct, LLM-judged version of Section 6's heuristic) |
| `answer_relevancy` | Does the answer actually address the question asked, rather than being faithful-but-off-topic? |
| `context_precision` | Of the retrieved contexts, how many were actually relevant/useful? |
| `context_recall` | Did retrieval surface all the context needed to fully answer the question? |

---

## 8. Traps & Misconceptions (MCQ-Relevant)

1. **"High ROUGE/BLEU score means the answer is factually correct"** — FALSE. These measure surface word overlap with a reference text, not factual accuracy or faithfulness to retrieved context — a fluent hallucination can score reasonably on these if it happens to reuse similar phrasing.
2. **"Precision@k and Recall@k always move in the same direction"** — FALSE, as Section 2 shows — they trade off against each other as k increases.
3. **"NDCG and Recall@k measure the same thing"** — FALSE. Recall@k only cares whether relevant docs are present in the top k; NDCG additionally cares about their exact position and graded relevance level.
4. **"RAGAS metrics are pure math, no LLM needed"** — FALSE. RAGAS's core metrics are LLM-judged — the metric computation itself makes calls to an LLM to assess faithfulness/relevancy, unlike ROUGE/BLEU/precision/recall which are pure computation.
5. **"A faithfulness heuristic based on word overlap is production-ready"** — Not for anything high-stakes — as shown in Section 6, word-overlap heuristics can't distinguish a faithful paraphrase from an unfaithful answer that happens to reuse context vocabulary.

---

## 9. Rapid-Fire Self-Check (MCQ Simulation)

1. As k increases in Precision@k/Recall@k, which one typically increases and which typically decreases? *(Recall typically increases toward 1.0 as more documents are retrieved; precision typically decreases as more irrelevant documents get included)*
2. What does MRR specifically measure that Precision@k does not? *(The position/rank of the FIRST relevant result, not the overall proportion of relevant results in the top k)*
3. Why might NDCG be preferred over Recall@k when evaluating a re-ranker? *(NDCG accounts for the ORDER and graded relevance of results, not just their presence in the top k — exactly what a re-ranker is trying to improve)*
4. Name one reason ROUGE/BLEU scores can be misleading for evaluating LLM-generated answers. *(They measure surface word overlap, not semantic correctness or faithfulness — a well-paraphrased correct answer can score low, and a fluent hallucination can score deceptively high)*
5. What's the fundamental difference between RAGAS's metrics and Precision@k/ROUGE/BLEU? *(RAGAS metrics are LLM-judged — they require an actual LLM call to assess qualities like faithfulness and relevancy — while precision/recall/ROUGE/BLEU are pure computation with no LLM involved)*

---

## Status
Precision@k, Recall@k, MRR, NDCG, ROUGE, and BLEU are all genuinely computed with real numbers above. The word-overlap hallucination-detection heuristic is real and computed, with its limitations disclosed honestly. RAGAS and NLI-model-based faithfulness checking are given as complete, copy-ready reference code for your environment, including the actual import error this sandbox hit when attempting to even load the library — a real, disclosed limitation rather than a silently-skipped section.

Ready for the companion **Cheatsheet — Topic 8** or straight into **Topic 9: Common ML Algorithms Overview** whenever you want to continue.
