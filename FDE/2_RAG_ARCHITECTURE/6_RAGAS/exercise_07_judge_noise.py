"""Exercise 7: measure judge noise and compare absolute vs paired gates.

Run with `python exercise_07_judge_noise.py`. Uses only the Python standard
library; all scores are inline, so no API call or API key is required.

Behavior: reports per-run means, population standard deviation, and a seeded
bootstrap confidence interval; then evaluates absolute and paired gates.

Lesson: repeated LLM-as-judge scores can cross an absolute threshold on unchanged
code. Comparing a candidate to a contemporaneous main run can cancel shared noise.
"""

import random
import statistics


MAIN_RUNS = [
    [1.0] * 14 + [0.5, 0.5, 0.5, 0.5, 0.3, 0.3],
    [1.0] * 15 + [0.5, 0.5, 0.5, 0.5, 0.4],
    [1.0] * 15 + [0.5, 0.5, 0.5, 0.25, 0.25],
    [1.0] * 15 + [0.5, 0.5, 0.5, 0.5, 0.2],
    [1.0] * 14 + [0.5, 0.5, 0.5, 0.5, 0.5, 0.3],
]
CANDIDATE_RUNS = [
    [1.0] * 14 + [0.5, 0.5, 0.5, 0.5, 0.3, 0.4],
    [1.0] * 15 + [0.5, 0.5, 0.5, 0.5, 0.44],
    [1.0] * 15 + [0.46, 0.5, 0.5, 0.25, 0.25],
    [1.0] * 15 + [0.5, 0.5, 0.5, 0.5, 0.3],
    [1.0] * 14 + [0.5, 0.5, 0.5, 0.5, 0.5, 0.34],
]
ABSOLUTE_GATE = 0.85
PAIRED_TOLERANCE = -0.03


def bootstrap_ci(run, samples=10_000, seed=42):
    rng = random.Random(seed)
    means = sorted(
        statistics.mean(rng.choices(run, k=len(run)))
        for _ in range(samples)
    )
    def percentile(fraction):
        position = (len(means) - 1) * fraction
        lower = int(position)
        upper = min(lower + 1, len(means) - 1)
        return means[lower] + (means[upper] - means[lower]) * (position - lower)
    return percentile(0.025), percentile(0.975)


def main():
    print(f'{"run":>3} {"main":>6} {"cand":>6} {"c_std":>6} {"ci_lo":>6} {"ci_hi":>6}')
    for index, (main_run, candidate_run) in enumerate(zip(MAIN_RUNS, CANDIDATE_RUNS), start=1):
        mean_main = statistics.mean(main_run)
        mean_candidate = statistics.mean(candidate_run)
        low, high = bootstrap_ci(candidate_run, seed=41 + index)
        print(
            f"{index:>3} {mean_main:>6.3f} {mean_candidate:>6.3f} "
            f"{statistics.pstdev(candidate_run):>6.3f} {low:>6.3f} {high:>6.3f}"
        )

    absolute = [
        "PASS" if statistics.mean(run) >= ABSOLUTE_GATE else "FAIL"
        for run in CANDIDATE_RUNS
    ]
    print(f"\nabsolute gate (candidate mean >= {ABSOLUTE_GATE:.2f}): {absolute}")
    if len(set(absolute)) == 1:
        raise AssertionError("Expected judge noise to demonstrate an absolute-gate flip.")

    print(f"paired delta gate (vs main, tolerance {PAIRED_TOLERANCE:+.2f}):")
    for index, (main_run, candidate_run) in enumerate(zip(MAIN_RUNS, CANDIDATE_RUNS), start=1):
        delta = statistics.mean(candidate_run) - statistics.mean(main_run)
        verdict = "PASS" if delta >= PAIRED_TOLERANCE else "FAIL"
        print(f"  run {index}: delta={delta:+.3f} -> {verdict}")
        if verdict != "PASS":
            raise AssertionError(f"Expected paired run {index} to pass.")
    print("Paired comparisons keep all five identical-code candidate runs within tolerance.")


if __name__ == "__main__":
    main()
