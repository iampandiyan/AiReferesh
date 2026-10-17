"""Exercise 4: generate a GitHub Actions RAG-gate workflow.

Run with `python exercise_04_github_actions.py` to print the standalone workflow.
Pass `--write` to save it as `rag-ci.yml` under the current working directory.
Run `python exercise_04_github_actions.py --check` to execute its deterministic
gate example. No other exercise file is imported or required.

Behavior: the workflow runs on pull requests, captures the gate output, comments
on a failing PR, and marks the check failed. Its scores are a clearly labelled
fixture; replace them with the result of the project's real RAG evaluation.

Lesson: CI should fail on threshold breaches and make those breaches visible in
the PR. A fixture validates the workflow plumbing, not the quality of a live RAG.
"""

import argparse
import json
import os
from pathlib import Path


THRESHOLDS = {
    "faithfulness": 0.85,
    "answer_relevancy": 0.85,
    "context_precision": 0.80,
    "context_recall": 0.80,
}
EXAMPLE_SCORES = {
    "faithfulness": 0.91,
    "answer_relevancy": 0.90,
    "context_precision": 0.86,
    "context_recall": 0.84,
}
WORKFLOW = """name: rag-ci
on:
  pull_request:
permissions:
  contents: read
  issues: write
jobs:
  ragas-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Run the standalone gate fixture
        id: gate
        continue-on-error: true
        env:
          RAGAS_SCORES_JSON: ${{ vars.RAGAS_SCORES_JSON }}
        run: |
          set -o pipefail
          python FDE/2_RAG_ARCHITECTURE/6_RAGAS/exercise_04_github_actions.py --check 2>&1 | tee gate.txt
      - name: Comment with breached metrics
        if: steps.gate.outcome == 'failure'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const log = fs.readFileSync('gate.txt', 'utf8').slice(-1500);
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: '## RAG CI gate failed\\n```\\n' + log + '\\n```',
            });
            core.setFailed('RAG gate breached - see PR comment.');
"""


def gate_report(scores, thresholds=THRESHOLDS):
    missing = sorted(set(thresholds) - set(scores))
    if missing:
        raise ValueError("Missing metric scores: " + ", ".join(missing))
    breaches = [
        f"{metric}={scores[metric]:.2f} < {threshold:.2f}"
        for metric, threshold in thresholds.items()
        if scores[metric] < threshold
    ]
    return "PASS" if not breaches else "FAIL: " + "; ".join(breaches)


def run_check():
    raw_scores = os.environ.get("RAGAS_SCORES_JSON")
    scores = json.loads(raw_scores) if raw_scores else EXAMPLE_SCORES
    report = gate_report(scores)
    print("scores:", json.dumps(scores, sort_keys=True))
    print("RAG CI gate:", report)
    if report != "PASS":
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="run the deterministic gate fixture")
    mode.add_argument("--write", action="store_true", help="write rag-ci.yml in the current directory")
    args = parser.parse_args()

    if args.check:
        run_check()
    elif args.write:
        path = Path.cwd() / "rag-ci.yml"
        path.write_text(WORKFLOW, encoding="utf-8")
        print(f"Workflow written to {path}")
    else:
        print(WORKFLOW, end="")


if __name__ == "__main__":
    main()
