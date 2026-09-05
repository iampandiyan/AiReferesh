# GenAI/AI-ML Principles — Topic 7: Fine-tuning vs Prompting vs RAG

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**

Prompting was covered in Topic 4; RAG was covered in Topic 3. This topic is the comparison and decision framework between all three approaches, plus a real demonstration of the one mechanism that's genuinely unique to fine-tuning: **actual model weights changing**. Since a real LLM fine-tune needs GPU infrastructure and model downloads not available here, the demo below uses a small `sklearn` classifier to show the exact same underlying mechanism (gradient-based weight updates) with real, verifiable numbers.

---

## 1. The Three Approaches, One Sentence Each

- **Prompting** (Topic 4): change the *input text* to guide the model's output. No weights change. Fastest and cheapest to iterate.
- **RAG** (Topic 3): retrieve relevant external information and inject it into the prompt at query time. No weights change. Solves the "model doesn't know this" problem for existing/changing knowledge.
- **Fine-tuning**: continue training the model's weights on task-specific labeled data. The model's actual parameters change permanently (until further training). Solves "the model doesn't behave/respond in the style/format I need," not primarily a knowledge-freshness problem.

---

## 2. Fine-Tuning's Real Mechanism — Demonstrated With Actual Weight Numbers

Fine-tuning is gradient-based weight updates on task-specific data. This is genuinely demonstrable without an LLM — the exact same mechanism (a model's internal parameters shifting via gradient descent when trained further on new data) happens in any gradient-based model, including a small linear classifier:

```python
import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.datasets import make_classification

np.random.seed(0)
X_general, y_general = make_classification(n_samples=200, n_features=4, n_informative=2, n_redundant=1, random_state=0)
X_narrow, y_narrow = make_classification(n_samples=30, n_features=4, n_informative=2, n_redundant=1, random_state=99)
X_narrow = X_narrow + 2.0   # shifted distribution simulating a narrow, specialized domain

model = SGDClassifier(loss='log_loss', random_state=0)
model.partial_fit(X_general, y_general, classes=[0,1])   # "pretraining" on general data

weights_before = model.coef_.copy()
print("accuracy on general data:", round(model.score(X_general, y_general), 4))
print("accuracy on narrow task (before):", round(model.score(X_narrow, y_narrow), 4))
print("weights before:", np.round(weights_before, 4))
```
Output:
```
accuracy on general data: 0.955
accuracy on narrow task (before): 0.5
weights before: [[ -4.5628  35.122  -16.6346   1.0909]]
```
The "pretrained" model does great on general data (0.955) but is at chance level (0.5 — a coin flip) on the narrow, specialized task it never saw.

**Now fine-tune — continue training ONLY on the narrow task-specific data:**
```python
for _ in range(20):
    model.partial_fit(X_narrow, y_narrow)

weights_after = model.coef_.copy()
print("accuracy on general data (after):", round(model.score(X_general, y_general), 4))
print("accuracy on narrow task (after):", round(model.score(X_narrow, y_narrow), 4))
print("weights after:", np.round(weights_after, 4))
print("weight change magnitude:", round(np.linalg.norm(weights_after - weights_before), 4))
```
Output:
```
accuracy on general data (after): 0.405
accuracy on narrow task (after): 1.0
weights after: [[ 22.8244 -12.0196  30.5428 -11.0942]]
weight change magnitude: 73.1202
```
This is a real, honest demonstration of two genuine fine-tuning phenomena at once:
1. **Specialization works:** narrow-task accuracy jumped from 0.5 (chance) to 1.0 (perfect) — the weights genuinely shifted toward the new task.
2. **Catastrophic forgetting is real:** general-data accuracy collapsed from 0.955 to 0.405 — worse than chance would even suggest — because the weights that made the model good at the *general* task got overwritten while specializing on the *narrow* task.

**This is exactly the core trade-off of fine-tuning an LLM:** it can make a model excellent at a specific format/domain/style, but naive fine-tuning risks degrading its general capabilities — which is precisely why techniques like LoRA (Section 4) and careful data mixing exist in real LLM fine-tuning pipelines.

---

## 3. Trade-off Comparison Table

| | Prompting | RAG | Fine-tuning |
|---|---|---|---|
| Changes model weights? | No | No | Yes |
| Setup cost/complexity | Very low | Medium (needs a retrieval pipeline) | High (needs training infra, labeled data) |
| Cost per query | Low (just prompt tokens) | Medium (retrieval + larger prompt) | Low per query (but high one-time training cost) |
| Best for | Format/style guidance, simple task instructions | Injecting current/private/frequently-changing knowledge | Teaching a consistent behavior, style, or output format at scale |
| Knowledge freshness | Limited to what's in the prompt | Easy — update the knowledge base, no retraining | Hard — requires retraining to update knowledge |
| Data requirement | None to a few examples | A document corpus | Hundreds to thousands of labeled examples |
| Risk of catastrophic forgetting | N/A (no weight changes) | N/A (no weight changes) | Real risk, as demonstrated above |
| Hallucination risk | Higher (relies on parametric knowledge) | Lower (grounded in retrieved text) | Depends on training data quality — doesn't inherently reduce hallucination |

---

## 4. Parameter-Efficient Fine-Tuning: LoRA/QLoRA (Reference Only)

Full fine-tuning updates ALL of a model's weights — expensive and memory-hungry for large LLMs, and the primary driver of catastrophic forgetting risk (as demonstrated above, the whole weight matrix shifted). **LoRA (Low-Rank Adaptation)** instead freezes the original weights and trains a much smaller set of additional low-rank matrices injected into the model — dramatically reducing the number of trainable parameters and memory footprint, and making forgetting less severe since the original weights never actually change.

**Reference pattern (not executed here — needs GPU + model download):**
```python
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("some-base-model")

lora_config = LoraConfig(
    r=8,                    # rank of the low-rank matrices - lower = fewer trainable params
    lora_alpha=16,          # scaling factor
    target_modules=["q_proj", "v_proj"],   # which weight matrices to adapt
    lora_dropout=0.05,
    task_type="CAUSAL_LM",
)

peft_model = get_peft_model(model, lora_config)
peft_model.print_trainable_parameters()
# typically shows something like: "trainable params: 4,194,304 || all params: 7,000,000,000 || trainable%: 0.06"
```
**QLoRA** extends this further by quantizing the frozen base model to 4-bit precision before applying LoRA, cutting memory requirements even more — this is what makes fine-tuning large models feasible on a single consumer GPU.

---

## 5. Decision Framework — Which One to Use

- **Need the model to know something new/current/private?** → RAG. Fine-tuning is a poor tool for pure knowledge injection since it's expensive to update and doesn't guarantee the model reliably recalls specific facts.
- **Need consistent output format, tone, or behavior across many queries?** → Fine-tuning (or start with prompting/few-shot, and only fine-tune if prompting proves insufficient at scale).
- **Need something working today, cheaply, with no training infrastructure?** → Prompting first, always — it's the cheapest experiment to run before reaching for RAG or fine-tuning.
- **Need to reduce hallucination on factual questions?** → RAG, not fine-tuning — fine-tuning doesn't inherently ground answers in verifiable sources the way retrieval does.
- **In practice:** these aren't mutually exclusive — many production systems combine all three (a fine-tuned model, using RAG for current knowledge, with careful prompting on top).

---

## 6. Traps & Misconceptions (MCQ-Relevant)

1. **"Fine-tuning is the best way to give a model new factual knowledge"** — FALSE. RAG is generally the better tool for this — fine-tuning is expensive to update and doesn't guarantee reliable factual recall the way retrieval-grounded generation does.
2. **"RAG and fine-tuning solve the same problem"** — FALSE. RAG addresses knowledge access; fine-tuning addresses behavior/format/style. They're complementary, not competing solutions to the same problem.
3. **"Fine-tuning always improves overall model quality"** — FALSE, as demonstrated above — narrow fine-tuning can severely degrade general performance (catastrophic forgetting) if not managed carefully.
4. **"LoRA changes the original model weights"** — FALSE. LoRA freezes the original weights entirely and trains small additional low-rank matrices alongside them — this is precisely why it reduces (though doesn't eliminate) forgetting risk.
5. **"Prompting can't achieve what fine-tuning does"** — Not universally true for smaller tasks — well-designed few-shot prompting can often match fine-tuning for simpler format/style tasks, at a fraction of the cost and complexity; fine-tuning earns its cost mainly at scale or for behaviors prompting genuinely can't reach.

---

## 7. Rapid-Fire Self-Check (MCQ Simulation)

1. Which of the three approaches actually changes a model's internal weights? *(Only fine-tuning — prompting and RAG both leave weights untouched)*
2. What real phenomenon did the weight-update demo above illustrate when general-data accuracy dropped from 0.955 to 0.405? *(Catastrophic forgetting — specializing on narrow data degraded performance on the original general task)*
3. Why is RAG generally preferred over fine-tuning for keeping a model's knowledge current? *(Updating a RAG knowledge base requires no retraining — just updating the document store — while fine-tuning requires a full retraining cycle to incorporate new information)*
4. What's the key difference between full fine-tuning and LoRA? *(Full fine-tuning updates all model weights; LoRA freezes the original weights and trains only small additional low-rank matrices, greatly reducing trainable parameters and forgetting risk)*
5. Does fine-tuning inherently reduce hallucination? *(No — it depends entirely on training data quality; it doesn't ground outputs in verifiable sources the way RAG does)*

---

## Status
The core fine-tuning mechanism (gradient-based weight updates, specialization, and catastrophic forgetting) is demonstrated with real, executed code and genuine numbers — not a description borrowed from general ML knowledge. LoRA/QLoRA are reference-only since they need GPU infrastructure and model downloads unavailable here.

Ready for the companion **Cheatsheet — Topic 7** or straight into **Topic 8: Evaluation Metrics for GenAI** whenever you want to continue.
