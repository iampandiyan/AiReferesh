"""Exercise 6: generate a versioned, tagged, A/B-ready prompt migration.

Run independently with `python -m pip install openai pyyaml` and Git installed/on PATH.
Set TOGETHER_STUDY_API_KEY to make the optional smoke call. Generated files and the
Git repository are confined to exercise_6_output/ beside this script.

Lesson: prompt changes need provenance (metadata + golden hash), immutable promotion
points (tags), deterministic cohorts, observable source/version data, compliance sign-off,
and a rollback procedure. This is a demo; a real rollout also needs reviewed eval results.
"""

import hashlib
import os
import subprocess
from collections import Counter
from pathlib import Path

import yaml
from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
OUTPUT = Path(__file__).resolve().parent / "exercise_6_output"
PROMPT_DIR = OUTPUT / "prompts" / "lending-advisor"
GOLDEN_CASES = [
    "credit score 690, $6,000 business loan eligible?",
    "monthly payment for $2,400, 18%, 24 months?",
    "mi credit score es 690, elegible para business loan?",
    "What documents are needed for a small-business loan?",
    "Do not echo CUST_TEST_0001.",
    "How do I check repayment terms?",
    "Can a seasonal business apply for credit?",
    "Necesito informacion de un prestamo personal.",
    "What is the difference between fixed and variable rates?",
    "Can I update my business address?",
    "My application status is unclear.",
    "How long does underwriting take?",
    "Tengo ingresos variables, que documentos necesito?",
    "Can I make an early repayment?",
    "What does APR mean?",
    "Please explain the synthetic policy in simple terms.",
    "Is collateral required for every loan?",
    "Can I speak to a human about an appeal?",
    "When is my next payment due?",
    "Mask identifiers before responding.",
]
GOLDEN_HASH = hashlib.sha256("\n".join(GOLDEN_CASES).encode("utf-8")).hexdigest()[:16]
VERSION_BODIES = {
    "v1": (
        "You are an AcmeCorp lending advisor for small businesses. Follow the supplied "
        "synthetic lending policy. Declare a purpose before any sensitive-data access. "
        "Respond in the user's language and do not invent facts."
    ),
    "v2": (
        "You are an AcmeCorp lending advisor for small businesses. Follow the supplied "
        "synthetic lending policy. Declare a purpose before any sensitive-data access. "
        "Respond in the user's language, including code-mixed Spanish and English. "
        "Do not invent facts or repeat personal identifiers."
    ),
    "v3": (
        "You are an AcmeCorp lending advisor for small businesses. Follow the supplied "
        "synthetic lending policy. Declare a purpose before any sensitive-data access. "
        "Respond in the user's language, including code-mixed Spanish and English. "
        "Never quote a loan amount unless asked. Do not invent facts or repeat identifiers."
    ),
}
VERSIONS = {
    "v1": ("2026-10-10T09:00:00Z", "initial migration from inline prompt"),
    "v2": ("2026-10-10T10:00:00Z", "clarify code-mixed language and identifier handling"),
    "v3": ("2026-10-10T11:00:00Z", "compliance review: prevent unrequested amount disclosure"),
}


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def ensure_repo() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not (OUTPUT / ".git").exists():
        git(OUTPUT, "init", "-q")
        git(OUTPUT, "config", "user.name", os.environ.get("GIT_AUTHOR_NAME", "Prompt Lab"))
        git(OUTPUT, "config", "user.email", os.environ.get("GIT_AUTHOR_EMAIL", "prompt-lab@example.invalid"))


def write_version(version: str) -> Path:
    created_at, _reason = VERSIONS[version]
    spec = {
        "name": "lending-advisor",
        "version": version,
        "model": MODEL,
        "author": os.environ.get("PROMPT_AUTHOR", "local-developer"),
        "created_at": created_at,
        "golden_hash": GOLDEN_HASH,
        "body": VERSION_BODIES[version],
    }
    path = PROMPT_DIR / f"{version}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def commit_tagged_version(version: str, path: Path) -> None:
    relative = path.relative_to(OUTPUT).as_posix()
    git(OUTPUT, "add", relative)
    if git(OUTPUT, "status", "--porcelain"):
        git(OUTPUT, "commit", "-q", "-m", f"prompt: lending-advisor {version}")
    tag = f"prompt-lending-advisor-{version}"
    tags = git(OUTPUT, "tag", "-l", tag).splitlines()
    if not tags:
        git(OUTPUT, "tag", tag)


def pick_version(request_id: str, cohorts: list[tuple[str, int]]) -> str:
    if not cohorts or any(weight < 0 for _, weight in cohorts) or sum(weight for _, weight in cohorts) != 100:
        raise ValueError("Cohort percentages must be non-negative and sum to 100.")
    bucket = int(hashlib.sha256(request_id.encode("utf-8")).hexdigest(), 16) % 100
    cutoff = 0
    for version, weight in cohorts:
        cutoff += weight
        if bucket < cutoff:
            return version
    raise RuntimeError("No prompt cohort selected.")


def write_supporting_docs() -> None:
    (PROMPT_DIR / "CURRENT").write_text("v2\n", encoding="utf-8")
    changelog_lines = []
    for version, (created_at, reason) in VERSIONS.items():
        changelog_lines.append(
            f"- {created_at} | lending-advisor@{version} | operator={os.environ.get('PROMPT_AUTHOR', 'local-developer')} "
            f"| model={MODEL} | golden_hash={GOLDEN_HASH} | {reason}"
        )
    (PROMPT_DIR / "CHANGELOG.md").write_text("\n".join(changelog_lines) + "\n", encoding="utf-8")
    (OUTPUT / "prompt_ops.md").write_text(
        f"""# Prompt Operations: Compliance and DPO Review

The lending-advisor prompt is managed as a versioned control. Each YAML file records its name, version, model (`{MODEL}`), author, creation time, frozen evaluation-set hash (`{GOLDEN_HASH}`), and complete prompt body. The hash ties a prompt release to the exact synthetic cases used during review; it is not evidence of regulatory approval by itself.

Changes move through Git commits and immutable `prompt-lending-advisor-v1`, `v2`, and `v3` tags. `CURRENT` is the stable deployment pointer and is set to v2 in this demonstration. The CHANGELOG records operator, timestamp, pinned model, evaluation hash, and reason for every version. A reviewer must confirm data-minimization wording, language behavior, identifier masking, and evaluation results before promotion.

The A/B schedule assigns 10% of stable request IDs to v3 and 90% to v2 using a SHA-256 bucket. Repeated requests remain in the same cohort. The dashboard should show refusal/appeal rate, latency, cost, prompt version, and loader source by tenant; the canary is paused if approved quality or compliance thresholds regress. The included deterministic sample validates routing arithmetic only, not loan-advice quality.

Promotion requires documented product, compliance, and DPO sign-off, a reviewed golden set, and a named rollback owner. Keep synthetic or minimized test data, restrict prompt-store access, record purpose where personal data is accessed, and avoid logging raw customer identifiers. Consult `runbook.md` for rollback and watch `gen_ai.prompt.version` and loader-source dimensions in the dashboard. This demo does not provide legal advice or establish production approval.
""", encoding="utf-8")
    (OUTPUT / "runbook.md").write_text(
        """# Prompt Rollback Runbook

1. Pause the canary and confirm the affected `gen_ai.prompt.version` and loader source in the dashboard.
2. Set `prompts/lending-advisor/CURRENT` to the last-known-good version, such as `v2`, and verify the file is committed.
3. Restart/reload the service and send a synthetic canary request; confirm the selected version and response quality.
4. Verify latency, error/refusal rate, and cache/loader metrics recover; notify compliance and page on-call if they do not.
""", encoding="utf-8")
    (OUTPUT / "ab_router.py").write_text(
        '''import hashlib\n\ndef pick_version(request_id: str, cohorts=(('v3', 10), ('v2', 90))) -> str:\n    if sum(percent for _, percent in cohorts) != 100:\n        raise ValueError("cohorts must sum to 100")\n    bucket = int(hashlib.sha256(request_id.encode()).hexdigest(), 16) % 100\n    edge = 0\n    for version, percent in cohorts:\n        edge += percent\n        if bucket < edge:\n            return version\n    raise RuntimeError("no version selected")\n''', encoding="utf-8")
    (OUTPUT / "hybrid_loader.py").write_text(
        '''from dataclasses import dataclass\nfrom pathlib import Path\nimport yaml\n\n@dataclass\nclass PromptHit:\n    spec: dict\n    source: str\n\ndef load_disk(root: Path, name: str, version: str) -> PromptHit:\n    path = root / name / f"{version}.yaml"\n    with path.open(encoding="utf-8") as stream:\n        return PromptHit(yaml.safe_load(stream), "disk")\n''', encoding="utf-8")


def main() -> None:
    ensure_repo()
    for version in ("v1", "v2", "v3"):
        commit_tagged_version(version, write_version(version))
    write_supporting_docs()
    git(OUTPUT, "add", "prompts/lending-advisor/CURRENT", "prompts/lending-advisor/CHANGELOG.md",
        "prompt_ops.md", "runbook.md", "ab_router.py", "hybrid_loader.py")
    if git(OUTPUT, "status", "--porcelain"):
        git(OUTPUT, "commit", "-q", "-m", "docs: prompt operations and deployment controls")

    cohorts = [("v3", 10), ("v2", 90)]
    sample = Counter(pick_version(f"synthetic-request-{index}", cohorts) for index in range(1000))
    assert abs(sample["v3"] / 1000 - 0.10) <= 0.03
    print("Generated prompt versions v1/v2/v3 with golden hash:", GOLDEN_HASH)
    print("A/B distribution over 1000 deterministic IDs:", dict(sample))
    print("Git tags:", git(OUTPUT, "tag", "-l", "prompt-lending-advisor-v*"))
    print("Generated artifacts in:", OUTPUT)

    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        print("Together smoke call skipped; set TOGETHER_STUDY_API_KEY to try v2.")
        return
    spec_path = PROMPT_DIR / "v2.yaml"
    with spec_path.open(encoding="utf-8") as stream:
        spec = yaml.safe_load(stream)
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    response = client.chat.completions.create(
        model=spec["model"],
        messages=[
            {"role": "system", "content": spec["body"]},
            {"role": "user", "content": "Explain how an applicant can prepare for a loan review."},
        ],
        max_tokens=160,
    )
    print("v2 Together smoke response:", response.choices[0].message.content or "")


if __name__ == "__main__":
    main()