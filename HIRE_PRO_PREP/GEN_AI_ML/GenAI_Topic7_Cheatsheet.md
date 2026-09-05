# GenAI/AI-ML Cheatsheet — Topic 7 (Fine-tuning Mechanics Libraries)

**Companion to:** GenAI_Topic7_Finetuning_vs_Prompting_vs_RAG.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

`make_classification` is already covered in the Topic 1 cheatsheet — not repeated here.

---

## `sklearn.linear_model.SGDClassifier`

**Initialization:**
```python
from sklearn.linear_model import SGDClassifier
model = SGDClassifier(loss='log_loss', random_state=0)
```

**Top methods/attributes:**
| Method/Attribute | Explanation |
|---|---|
| `.partial_fit(X, y, classes=[...])` | Incremental training — the `classes` argument is REQUIRED on the very first call (so the model knows all possible labels upfront), but omitted on subsequent calls. This incremental nature is exactly what makes it a useful stand-in for demonstrating "continued training" / fine-tuning behavior |
| `.coef_` | The learned weight vector — inspecting this before/after further training is how you directly observe weight updates |
| `.intercept_` | The learned bias term |
| `.predict(X)` | Predict class labels |
| `.score(X, y)` | Accuracy on given data |

**Verified example:**
```python
from sklearn.datasets import make_classification
import numpy as np

X, y = make_classification(n_samples=100, n_features=4, n_informative=2, n_redundant=1, random_state=0)
model = SGDClassifier(loss='log_loss', random_state=0)
model.partial_fit(X, y, classes=[0,1])          # first call - classes required
print(np.round(model.coef_, 4))                  # [[ 29.4924 -14.2764  19.4646  13.1167]]
print(round(model.score(X, y), 4))               # 0.91

model.partial_fit(X[:10], y[:10])                # continued training - no classes= needed now
print(np.round(model.coef_, 4))                  # weights shifted slightly: [[ 29.4499 -13.5196 ...]]
```

---

## `peft.LoraConfig` / `get_peft_model` — Reference Only

**Not executed in this sandbox** — requires a GPU and a downloaded base model. Full reference pattern for your own environment:

```python
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("some-base-model")

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    task_type="CAUSAL_LM",
)

peft_model = get_peft_model(model, lora_config)
peft_model.print_trainable_parameters()
```

| Parameter/Method | Explanation |
|---|---|
| `r` | Rank of the low-rank adaptation matrices — lower = fewer trainable parameters, less expressive |
| `lora_alpha` | Scaling factor applied to the LoRA update |
| `target_modules` | Which of the base model's weight matrices get a LoRA adapter attached (commonly attention projection layers) |
| `.print_trainable_parameters()` | Shows the trainable-vs-total parameter count — typically well under 1% of total parameters |

---

## Status
1 fully verified entry (`SGDClassifier`) plus 1 clearly marked reference-only entry (`peft`/LoRA) for your own environment.
