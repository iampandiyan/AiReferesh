# GenAI/AI-ML Cheatsheet — Topic 1 (Core ML Concepts Libraries)

**Companion to:** GenAI_Topic1_Core_ML_Concepts.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

All examples below were executed for real — outputs shown are actual, not invented.

---

## `sklearn.model_selection.train_test_split`

**Initialization:**
```python
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
```

**Top parameters (this is a function, not a class with methods):**
| Parameter | Explanation |
|---|---|
| `test_size` | Fraction (or count) of data reserved for testing |
| `random_state` | Seed for reproducibility — same split every run |
| `stratify=y` | Preserve class proportions between train and test sets |
| `shuffle` (default `True`) | Whether to shuffle before splitting — usually leave as default |

**Verified example:**
```python
print("shapes:", X_train.shape, X_test.shape, y_train.shape, y_test.shape)
# shapes: (120, 4) (30, 4) (120,) (30,)
```

---

## `sklearn.linear_model.LogisticRegression`

**Initialization:**
```python
from sklearn.linear_model import LogisticRegression
clf = LogisticRegression(max_iter=200)
```

**Top methods:**
| Method | Explanation |
|---|---|
| `.fit(X, y)` | Train the model on labeled data |
| `.predict(X)` | Predict class labels for new data |
| `.predict_proba(X)` | Predict class probabilities instead of hard labels |
| `.score(X, y)` | Convenience method — fits accuracy in one call |

**Verified example:**
```python
clf.fit(X_train, y_train)
print(clf.predict(X_test[:5]))          # [1 0 2 1 1]
print(clf.predict_proba(X_test[:1]))    # [[0.0038 0.8277 0.1685]]
print(clf.score(X_test, y_test))        # 1.0
```

---

## `sklearn.linear_model.LinearRegression`

**Initialization:**
```python
from sklearn.linear_model import LinearRegression
lr = LinearRegression()
```

**Top methods/attributes:**
| Method/Attribute | Explanation |
|---|---|
| `.fit(X, y)` | Fit the regression line |
| `.coef_` | Learned slope(s) — one per feature |
| `.intercept_` | Learned intercept (bias term) |
| `.predict(X)` | Predict continuous values for new data |

**Verified example:**
```python
Xr = [[1],[2],[3],[4]]
yr = [2,4,6,8]
lr.fit(Xr, yr)
print(lr.coef_, lr.intercept_)   # [2.] 0.0
print(lr.predict([[5]]))         # [10.]
```

---

## `sklearn.cluster.KMeans`

**Initialization:**
```python
from sklearn.cluster import KMeans
km = KMeans(n_clusters=3, random_state=42, n_init=10)
```

**Top methods/attributes:**
| Method/Attribute | Explanation |
|---|---|
| `.fit(X)` | Find clusters — note: no `y` argument, unsupervised |
| `.labels_` | Cluster assignment for each training point |
| `.cluster_centers_` | Coordinates of the learned cluster centers |
| `.inertia_` | Sum of squared distances to nearest cluster center — lower is "tighter" clusters |
| `.predict(X_new)` | Assign new points to the nearest existing cluster |

**Verified example:**
```python
km.fit(X)
print(km.cluster_centers_.shape)   # (3, 4)
print(round(km.inertia_, 2))       # 78.85
print(km.predict([X[0]]))          # [1]
```

---

## `sklearn.datasets`

**Initialization:**
```python
from sklearn.datasets import load_iris, make_classification
```

**Top functions:**
| Function | Explanation |
|---|---|
| `load_iris(return_X_y=True)` | Classic built-in labeled dataset for quick classification demos |
| `make_classification(n_samples=, n_features=)` | Generate a synthetic classification dataset on demand — useful when you need controllable, disposable data |

**Verified example:**
```python
Xc, yc = make_classification(n_samples=100, n_features=4, random_state=42)
print(Xc.shape, yc.shape)          # (100, 4) (100,)

X, y = load_iris(return_X_y=True)
print(X.shape, set(y))             # (150, 4) {0, 1, 2}
```

---

## `sklearn.preprocessing.PolynomialFeatures`

**Initialization:**
```python
from sklearn.preprocessing import PolynomialFeatures
poly = PolynomialFeatures(degree=2)
```

**Top methods:**
| Method | Explanation |
|---|---|
| `.fit_transform(X)` | Generate polynomial/interaction features up to the given degree |
| `.get_feature_names_out(input_names)` | Human-readable names for the generated features — useful for debugging what got created |

**Verified example:**
```python
transformed = poly.fit_transform([[2,3]])
print(transformed)   # [[1. 2. 3. 4. 6. 9.]]  -> [1, a, b, a^2, ab, b^2]
print(poly.get_feature_names_out(['a','b']))   # ['1' 'a' 'b' 'a^2' 'a b' 'b^2']
```

---

## `sklearn.preprocessing.StandardScaler`

**Initialization:**
```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
```

**Top methods:**
| Method | Explanation |
|---|---|
| `.fit_transform(X)` | Standardize features to mean=0, std=1 — fit on train, only `.transform()` on test to avoid leakage |
| `.transform(X)` | Apply a previously-fit scaler to new data (no re-fitting) |

**Verified example:**
```python
scaled = scaler.fit_transform(X_train)
print(scaled.mean(axis=0).round(4))   # [ 0. -0. -0. -0.]  (essentially zero)
print(scaled.std(axis=0).round(4))    # [1. 1. 1. 1.]
```

---

## `sklearn.pipeline.make_pipeline`

**Initialization:**
```python
from sklearn.pipeline import make_pipeline
pipe = make_pipeline(PolynomialFeatures(2), LinearRegression())
```

**Top methods:**
| Method | Explanation |
|---|---|
| `.fit(X, y)` | Runs every step's `.fit_transform()` in sequence, then fits the final estimator |
| `.predict(X)` | Runs data through every transform step, then predicts with the final estimator |
| Why it matters | Prevents a very common bug: forgetting to apply the same preprocessing to test data as was applied to training data |

**Verified example:**
```python
pipe.fit(Xr, yr)
print(pipe.predict([[5]]))   # [10.]
```

---

## `sklearn.metrics`

**Initialization:**
```python
from sklearn.metrics import (
    accuracy_score, mean_squared_error, confusion_matrix,
    classification_report, precision_score, recall_score, f1_score
)
```

**Top functions:**
| Function | Explanation |
|---|---|
| `accuracy_score(y_true, y_pred)` | Fraction of correct predictions — classification |
| `mean_squared_error(y_true, y_pred)` | Average squared error — regression |
| `confusion_matrix(y_true, y_pred)` | Grid of true vs predicted classes — shows exactly what's being confused with what |
| `precision_score` / `recall_score` / `f1_score` | Per-class or averaged classification quality metrics beyond raw accuracy |
| `classification_report(y_true, y_pred)` | One-call summary of precision/recall/f1/support per class |

**Verified example:**
```python
preds = clf.predict(X_test)
print(accuracy_score(y_test, preds))                 # 1.0
print(mean_squared_error([1,2,3],[1,2,4]))           # 0.333...

print(confusion_matrix(y_test, preds))
# [[10  0  0]
#  [ 0  9  0]
#  [ 0  0 11]]

print(round(precision_score(y_test, preds, average='macro'), 4))  # 1.0
print(round(recall_score(y_test, preds, average='macro'), 4))     # 1.0
print(round(f1_score(y_test, preds, average='macro'), 4))         # 1.0
```

---

## `sklearn.model_selection.cross_val_score`

**Initialization:**
```python
from sklearn.model_selection import cross_val_score
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `cross_val_score(model, X, y, cv=5)` | Train/evaluate the model on 5 different train/test splits (folds), return all 5 scores — more robust than a single train/test split |
| `.mean()` on the result | The typical single number reported — average performance across all folds |

**Verified example:**
```python
scores = cross_val_score(LogisticRegression(max_iter=200), X, y, cv=5)
print(scores.round(4))        # [0.9667 1. 0.9333 0.9667 1.]
print(round(scores.mean(), 4)) # 0.9733
```

---

## `numpy` — ML Data Generation Utilities

**Top functions:**
| Function | Explanation |
|---|---|
| `np.random.seed(n)` | Fix the random seed for reproducible experiments |
| `np.random.rand(n)` | n uniform random floats in [0, 1) |
| `np.random.randn(n)` | n random floats from a standard normal distribution |
| `np.bincount(arr)` | Count occurrences of each non-negative integer — useful for checking class balance |

**Verified example:**
```python
np.random.seed(0)
print(np.random.rand(3).round(4))    # [0.5488 0.7152 0.6028]
print(np.random.randn(3).round(4))   # [-2.2683  1.3335 -0.8427]
print(np.bincount([0,0,1,2,2,2]))    # [2 1 3]
```

---

## Status
All 11 entries verified with real executed output. Use alongside the main GenAI Topic 1 doc for quick lookup during practice.
