"""Exercise 8: calibrate a judge threshold against SME labels.

Run with `python exercise_08_judge_calibration.py`. Uses only the Python
standard library; all sample labels and scores are inline.

Behavior: calculates Pearson correlation, sweeps candidate cutoffs, and reports
Cohen's kappa plus TP/FP/FN/TN at the conventional and best-scoring thresholds.

Lesson: chance-corrected agreement with SME labels can produce a better threshold
than choosing a familiar number. Recalibrate when the evaluation population changes.
"""

import math


GOLDEN = [
    (0.41, 0), (0.53, 0), (0.57, 0), (0.60, 0), (0.64, 0), (0.67, 0),
    (0.69, 0), (0.72, 0), (0.74, 0), (0.77, 0), (0.79, 0), (0.81, 0),
    (0.88, 0),
    (0.825, 1), (0.845, 1), (0.85, 1), (0.86, 1), (0.87, 1), (0.89, 1),
    (0.90, 1), (0.91, 1), (0.92, 1), (0.93, 1), (0.94, 1), (0.95, 1),
    (0.96, 1), (0.97, 1), (0.98, 1), (0.99, 1), (1.00, 1),
]


def cohen_kappa(predictions, labels):
    observed = sum(
        prediction == label for prediction, label in zip(predictions, labels)
    ) / len(labels)
    expected = sum(
        (sum(value == category for value in predictions) / len(predictions))
        * (sum(value == category for value in labels) / len(labels))
        for category in (0, 1)
    )
    if expected == 1:
        raise ValueError("Cohen's kappa is undefined when expected agreement is 1.")
    return (observed - expected) / (1 - expected)


def confusion(predictions, labels):
    true_positive = sum(prediction == 1 and label == 1 for prediction, label in zip(predictions, labels))
    false_positive = sum(prediction == 1 and label == 0 for prediction, label in zip(predictions, labels))
    false_negative = sum(prediction == 0 and label == 1 for prediction, label in zip(predictions, labels))
    true_negative = sum(prediction == 0 and label == 0 for prediction, label in zip(predictions, labels))
    return true_positive, false_positive, false_negative, true_negative


def main():
    scores = [score for score, _ in GOLDEN]
    labels = [label for _, label in GOLDEN]
    mean_score = sum(scores) / len(scores)
    mean_label = sum(labels) / len(labels)
    covariance = sum(
        (score - mean_score) * (label - mean_label)
        for score, label in zip(scores, labels)
    ) / len(scores)
    score_sd = math.sqrt(sum((score - mean_score) ** 2 for score in scores) / len(scores))
    label_sd = math.sqrt(sum((label - mean_label) ** 2 for label in labels) / len(labels))
    correlation = covariance / (score_sd * label_sd)
    print(f"Pearson r (judge score vs SME label): {correlation:.2f}")

    candidates = [round(0.70 + index * 0.01, 2) for index in range(31)]
    best_threshold, best_kappa = max(
        (
            (
                threshold,
                cohen_kappa(
                    [int(score >= threshold) for score in scores],
                    labels,
                ),
            )
            for threshold in candidates
        ),
        key=lambda item: item[1],
    )
    for threshold, tag in ((0.85, "naive"), (best_threshold, "calibrated")):
        predictions = [int(score >= threshold) for score in scores]
        tp, fp, fn, tn = confusion(predictions, labels)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        print(
            f"{tag:10s} t={threshold:.2f}: "
            f"kappa={cohen_kappa(predictions, labels):.2f} "
            f"TP={tp} FP={fp} FN={fn} TN={tn} "
            f"precision={precision:.2f} recall={recall:.2f}"
        )
    print(
        f"\nCalibrated gate = argmax kappa = {best_threshold:.2f} "
        f"(kappa={best_kappa:.2f}), derived from this SME-labelled sample."
    )


if __name__ == "__main__":
    main()
