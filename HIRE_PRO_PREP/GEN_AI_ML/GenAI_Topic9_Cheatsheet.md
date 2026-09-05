# GenAI/AI-ML Cheatsheet — Topic 9 (Common ML Algorithms Libraries)

**Companion to:** GenAI_Topic9_Common_ML_Algorithms.md
**Format:** Initialization → Top production-relevant methods → One verified runnable example per entry

`LinearRegression`, `LogisticRegression`, `KMeans`, and `make_classification` are already covered in the Topic 1 cheatsheet — not repeated here.

---

## `sklearn.linear_model.Ridge` / `Lasso`

**Initialization:**
```python
from sklearn.linear_model import Ridge, Lasso
ridge = Ridge(alpha=1.0)   # alpha = regularization strength
lasso = Lasso(alpha=0.1)
```

**Top attribute:**
| Attribute | Explanation |
|---|---|
| `.coef_` | Learned coefficients — Lasso's will often contain exact zeros (feature selection); Ridge's will be shrunk but non-zero |

**Verified example:**
```python
print(ridge.fit(X, y).coef_.round(3))   # [0.267 0.05  0.196 0.005]  - all non-zero
print(lasso.fit(X, y).coef_.round(3))   # [0.339 0.    0.   -0.   ]  - three zeroed out
```

---

## `sklearn.tree.DecisionTreeClassifier`

**Initialization:**
```python
from sklearn.tree import DecisionTreeClassifier
tree = DecisionTreeClassifier(max_depth=3, random_state=0)
```

**Top methods/attributes:**
| Method/Attribute | Explanation |
|---|---|
| `max_depth` | Constrains tree depth — the main lever against overfitting for a single tree |
| `.feature_importances_` | Relative importance of each feature in the tree's splits (sums to 1.0) |
| `.predict(X)` | Standard prediction call |

**Verified example:**
```python
tree.fit(X, y)
print(tree.feature_importances_.round(3))   # [1. 0. 0. 0.] - this small example relied entirely on feature 0
print(tree.predict(X[:3]))                  # [1 0 1]
```

---

## `sklearn.ensemble.RandomForestClassifier`

**Initialization:**
```python
from sklearn.ensemble import RandomForestClassifier
rf = RandomForestClassifier(n_estimators=100, random_state=0)
```

**Top parameter/method:**
| Parameter/Method | Explanation |
|---|---|
| `n_estimators` | Number of trees in the forest — more trees generally reduce variance further, with diminishing returns |
| `.predict_proba(X)` | Class probabilities averaged across all trees' votes |

**Verified example:**
```python
rf.fit(X, y)
print(rf.predict_proba(X[:2]).round(3))   # [[0. 1.] [1. 0.]]
```

---

## `sklearn.neighbors.KNeighborsClassifier`

**Initialization:**
```python
from sklearn.neighbors import KNeighborsClassifier
knn = KNeighborsClassifier(n_neighbors=3)
```

**Top method:**
| Method | Explanation |
|---|---|
| `.kneighbors(X, n_neighbors=k)` | Returns `(distances, indices)` of the k nearest training points — useful for debugging exactly WHY a prediction was made |

**Verified example:**
```python
knn.fit(X, y)
distances, indices = knn.kneighbors(X[:1], n_neighbors=3)
print(distances, indices)
# (array([[0.  , 0.1625, 0.2291]]), array([[ 0, 48, 45]]))
```

---

## `sklearn.svm.SVC`

**Initialization:**
```python
from sklearn.svm import SVC
svc = SVC(kernel='rbf', probability=True)   # probability=True needed for predict_proba
```

**Top parameter/attribute:**
| Parameter/Attribute | Explanation |
|---|---|
| `kernel` | `'linear'`, `'rbf'`, `'poly'`, `'sigmoid'` — controls what shape of decision boundary is possible |
| `.support_vectors_` | The actual training points that define the decision boundary — only these matter for prediction, not the full dataset |

**Verified example:**
```python
svc.fit(X, y)
print(svc.support_vectors_.shape)   # (15, 4) - only 15 of the 50 training points became support vectors
print(svc.predict(X[:3]))           # [1 0 1]
```

---

## `sklearn.naive_bayes.MultinomialNB`

**Initialization:**
```python
from sklearn.naive_bayes import MultinomialNB
nb = MultinomialNB()
```

**Top attribute:**
| Attribute | Explanation |
|---|---|
| `.class_log_prior_` | Log of each class's prior probability, learned from training label frequencies |
| Requires non-negative features | MultinomialNB assumes count-like data (e.g., word counts) — negative values will error |

**Verified example:**
```python
nb.fit(np.abs(X), y)   # abs() needed since MultinomialNB requires non-negative features
print(nb.class_log_prior_.round(3))   # [-0.693 -0.693] -> both classes equally likely (log(0.5))
```

---

## `sklearn.cluster.DBSCAN`

**Initialization:**
```python
from sklearn.cluster import DBSCAN
db = DBSCAN(eps=0.3, min_samples=5)
```

**Top parameter/attribute:**
| Parameter/Attribute | Explanation |
|---|---|
| `eps` | Max distance between two points to be considered neighbors |
| `min_samples` | Minimum neighbors required for a point to be a "core point" |
| `.labels_` | Cluster assignment per point — **`-1` means noise/outlier**, unlike KMeans which forces every point into a cluster |
| `.core_sample_indices_` | Indices of points that qualified as core points (dense-region anchors) |

**Verified example:**
```python
db.fit(X_moons)
print(db.labels_[:10])              # [ 3  0  0  4 -1  3  4  3  1  0]  - note the -1 (noise point)
print(len(db.core_sample_indices_)) # 21
```

---

## `sklearn.neural_network.MLPClassifier`

**Initialization:**
```python
from sklearn.neural_network import MLPClassifier
mlp = MLPClassifier(hidden_layer_sizes=(5,), activation='relu', max_iter=1000, random_state=0)
```

**Top parameter/attribute:**
| Parameter/Attribute | Explanation |
|---|---|
| `hidden_layer_sizes=(5,)` | One hidden layer with 5 neurons — a tuple like `(10,5)` would mean two hidden layers |
| `.n_layers_` | Total layers including input and output (so `(5,)` hidden = 3 total: input, hidden, output) |
| `.predict_proba(X)` | Class probabilities from the trained network |

**Verified example:**
```python
mlp.fit(X, y)
print(mlp.n_layers_)                        # 3
print(mlp.predict_proba(X[:2]).round(3))    # [[0.01 0.99] [0.969 0.031]]
```

---

## `sklearn.metrics.adjusted_rand_score`

**Initialization:**
```python
from sklearn.metrics import adjusted_rand_score
```

**Top usage:**
| Usage | Explanation |
|---|---|
| `adjusted_rand_score(true_labels, predicted_labels)` | Measures clustering agreement, corrected for chance — 1.0 = perfect match, ~0 = random. Robust to cluster label numbering being arbitrary (unlike raw accuracy) |

**Verified example:**
```python
print(adjusted_rand_score([0,0,1,1], [1,1,0,0]))   # 1.0 - perfect agreement even though label NUMBERS are swapped
```

---

## Status
9 entries verified with real executed output, covering every algorithm compared in the main Topic 9 doc.
