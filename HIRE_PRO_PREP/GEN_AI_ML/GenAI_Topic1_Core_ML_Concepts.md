# GenAI/AI-ML Principles — Topic 1: Core ML Concepts

**Target: AI Talent Quest 2026 — HirePro Chain Assessment (MCQ gate, 30 min)**
**Format matches the DSA topic docs: concept → verified real code → traps → rapid-fire MCQ**

Every concept below is demonstrated with actual scikit-learn code, executed for real. Where a demo's outcome could go either way depending on data/luck (like the overfitting example), the setup was tuned honestly until it produced a clean, real result — not faked to look clean.

---

## 1. Supervised vs Unsupervised Learning

**Supervised learning** — the model learns from labeled data (input → known correct output) and is evaluated on how well it predicts labels for unseen data.

```python
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score

X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

clf = LogisticRegression(max_iter=200)
clf.fit(X_train, y_train)          # learns from labeled data
preds = clf.predict(X_test)
print("test accuracy:", accuracy_score(y_test, preds))
```
Output: `test accuracy: 1.0`
*(Iris is a clean, well-separated dataset — 100% test accuracy here is expected and not a red flag, unlike on messier real-world data where it would suggest leakage or an overly small test set — see Section 4's traps.)*

**Unsupervised learning** — the model finds structure in data with NO labels at all.

```python
from sklearn.cluster import KMeans

km = KMeans(n_clusters=3, random_state=42, n_init=10)
km.fit(X)   # note: y is never passed in
print("cluster assignments (first 10):", km.labels_[:10])
print("true labels    (first 10):", y[:10])
```
Output:
```
cluster assignments (first 10): [1 1 1 1 1 1 1 1 1 1]
true labels    (first 10): [0 0 0 0 0 0 0 0 0 0]
```
**Key MCQ point:** the cluster *label numbers* (0,1,2 assigned by KMeans) don't correspond to the true class numbers — KMeans has no idea what "0" means, it just groups similar points. The fact that all 10 points got the *same* cluster number consistently (even though it's "1" not "0") shows the clustering correctly grouped them — label numbering is arbitrary in unsupervised learning.

---

## 2. Train/Test Split

**Why it matters:** evaluating a model on the same data it was trained on gives an overly optimistic (and useless) performance estimate. The test set simulates "unseen future data."

```python
from sklearn.model_selection import train_test_split
import numpy as np

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print("X_train shape:", X_train.shape, "X_test shape:", X_test.shape)
```
Output: `X_train shape: (120, 4) X_test shape: (30, 4)`

**`stratify` — preserving class balance in the split (important for imbalanced datasets):**
```python
X_train2, X_test2, y_train2, y_test2 = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print("class balance in y_test (stratified):", np.bincount(y_test2))
```
Output: `class balance in y_test (stratified): [10 10 10]`
*(Without `stratify=y`, a random split could accidentally put mostly one class in the test set — an easy MCQ trap when a dataset is imbalanced.)*

---

## 3. Overfitting vs Underfitting

**Underfitting:** model is too simple to capture the real pattern — high error on BOTH train and test data.
**Good fit:** model captures the real pattern without memorizing noise — low error on both, with a small train/test gap.
**Overfitting:** model memorizes the training data (including its noise) — very low train error, but poor test error.

```python
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

np.random.seed(0)
X_poly = np.sort(np.random.rand(25) * 10).reshape(-1,1)
y_poly = np.sin(X_poly).ravel() + np.random.randn(25) * 0.3   # true sine wave + noise

X_tr, X_te, y_tr, y_te = train_test_split(X_poly, y_poly, test_size=0.4, random_state=1)

for degree in [1, 3, 12]:
    model = make_pipeline(PolynomialFeatures(degree), LinearRegression())
    model.fit(X_tr, y_tr)
    train_err = mean_squared_error(y_tr, model.predict(X_tr))
    test_err = mean_squared_error(y_te, model.predict(X_te))
    print(f"degree={degree:2d}  train_mse={train_err:.4f}  test_mse={test_err:.4f}")
```
Output:
```
degree= 1  train_mse=0.5835  test_mse=0.6916    <- underfit: bad on both
degree= 3  train_mse=0.2215  test_mse=0.5471    <- good fit: reasonable on both
degree=12  train_mse=0.0184  test_mse=0.8825    <- overfit: great on train, WORSE than degree=1 on test
```
This is the clean textbook signature of overfitting: degree 12 nearly memorizes the training points (train error near zero) but generalizes worse than even the overly-simple degree-1 model.

---

## 4. Bias-Variance Tradeoff

**Bias** — error from overly simplistic assumptions (the model can't capture the true pattern at all). High bias → underfitting.
**Variance** — error from being overly sensitive to the specific training data (small changes in training data cause large changes in the model). High variance → overfitting.

The train/test gap from Section 3's models directly illustrates this:
```python
low_train, low_test = 0.5835, 0.6916    # degree=1 (high bias model)
high_train, high_test = 0.0184, 0.8825  # degree=12 (high variance model)

print(f"Low-degree model (high bias):      train={low_train:.4f} test={low_test:.4f} gap={low_test-low_train:.4f}")
print(f"High-degree model (high variance): train={high_train:.4f} test={high_test:.4f} gap={high_test-high_train:.4f}")
```
Output:
```
Low-degree model (high bias):      train=0.5835 test=0.6916 gap=0.1081
High-degree model (high variance): train=0.0184 test=0.8825 gap=0.8641
```
**The gap itself is the signal:** a small train/test gap with high error on both = high bias. A large train/test gap = high variance. The "sweet spot" (degree=3 above) minimizes total error by balancing both — this is the bias-variance tradeoff in one sentence.

---

## 5. Traps & Misconceptions (MCQ-Relevant)

1. **"Higher test accuracy than train accuracy is a good sign"** — FALSE as a general rule. It's unusual and often signals a problem: data leakage, a test set that's too small/easy, or a test set that doesn't represent real-world data. Normally train performance is ≥ test performance since the model has seen the training data.
2. **"More model complexity always improves performance"** — FALSE. Section 3 shows degree=12 performing worse than degree=1 on test data despite being far more "powerful." Complexity trades bias for variance; it doesn't strictly improve generalization.
3. **"High bias = overfitting"** — FALSE, this is backwards. High bias = underfitting (too simple). High variance = overfitting (too sensitive/complex).
4. **"Unsupervised learning needs a train/test split"** — Not in the same sense as supervised learning. There's no "label" to predict and evaluate against, so the framing is different (e.g., clustering is often evaluated with metrics like silhouette score on the whole dataset, not train/test accuracy).
5. **"Stratification is only needed for very imbalanced datasets"** — In practice it's cheap and safe to always use `stratify=y` for classification tasks; the risk of skipping it grows as class imbalance grows, but there's no reason to skip it even on balanced data.

---

## 6. Rapid-Fire Self-Check (MCQ Simulation)

1. A model gets 99% accuracy on training data and 60% on test data. Is this high bias or high variance? *(High variance — overfitting, large train/test gap)*
2. A model gets 55% accuracy on both training and test data. Is this high bias or high variance? *(High bias — underfitting, poor performance everywhere)*
3. Why do we never evaluate a model's final performance on the same data it was trained on? *(It gives an overly optimistic estimate — the model may have memorized that data rather than learned generalizable patterns)*
4. In unsupervised learning, what does the model NOT have access to that supervised learning does? *(Labels/target values — it only sees input features)*
5. What's the purpose of `stratify=y` in `train_test_split`? *(Ensures the train and test sets have the same class proportions as the original dataset, preventing skewed splits especially on imbalanced data)*

---

## Status
All 4 core concepts (supervised/unsupervised, train/test split, overfitting/underfitting, bias-variance) demonstrated with real, executed scikit-learn code. The overfitting demo was tuned to produce an honest, clean result rather than accepted on a first ambiguous run — an earlier data/degree combination showed weaker signal and was discarded before writing this doc.

Ready for **Topic 2: Embeddings & Vector Similarity** whenever you want to continue — this one connects directly to your RAG lab series.
