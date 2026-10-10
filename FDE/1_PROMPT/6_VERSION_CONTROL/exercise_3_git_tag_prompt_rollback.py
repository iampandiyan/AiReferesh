"""Exercise 3: load a prompt from immutable Git tags and rehearse rollback.

Run independently with `python -m pip install pyyaml` and Git installed/on PATH.
All Git work happens in a new temporary repository, never in the current workspace repo.

Lesson: a Git tag identifies the committed prompt content, not the possibly modified
worktree file. Numeric version sorting is needed because lexical sorting puts v10 before v2.
"""

import re
import subprocess
import tempfile
from pathlib import Path

import yaml


TAG_RE = re.compile(r"^prompt-lending-advisor-v(\d+)$")


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def save_prompt(repo: Path, version: str, body: str) -> None:
    prompt_dir = repo / "prompts" / "lending-advisor"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    spec = {
        "name": "lending-advisor",
        "version": version,
        "model": "openai/gpt-oss-120b",
        "author": "local-developer",
        "created_at": "2026-10-10T00:00:00Z",
        "golden_hash": "synthetic-demo-hash",
        "body": body,
    }
    (prompt_dir / f"{version}.yaml").write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")


def list_versions(repo: Path) -> list[str]:
    tags = run_git(repo, "tag", "-l", "prompt-lending-advisor-v*").splitlines()
    numbers = [int(match.group(1)) for tag in tags if (match := TAG_RE.fullmatch(tag))]
    return [f"v{number}" for number in sorted(numbers)]


def load_at_tag(repo: Path, version: str) -> dict:
    relative_path = f"prompts/lending-advisor/{version}.yaml"
    raw = run_git(repo, "show", f"prompt-lending-advisor-{version}:{relative_path}")
    return yaml.safe_load(raw)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="fde_prompt_git_demo_") as temp_dir:
        repo = Path(temp_dir)
        run_git(repo, "init", "-q")
        run_git(repo, "config", "user.name", "Prompt Lab")
        run_git(repo, "config", "user.email", "prompt-lab@example.invalid")

        versions = [
            ("v1", "Lending advisor v1: explain the available options."),
            ("v2", "Lending advisor v2: match the user's language and state assumptions."),
            ("v10", "Lending advisor v10: mask identifiers and do not invent facts."),
        ]
        for version, body in versions:
            save_prompt(repo, version, body)
            run_git(repo, "add", "prompts")
            run_git(repo, "commit", "-q", "-m", f"prompt: lending-advisor {version}")
            run_git(repo, "tag", f"prompt-lending-advisor-{version}")

        available = list_versions(repo)
        assert available == ["v1", "v2", "v10"], available
        v1_before = load_at_tag(repo, "v1")
        worktree_v1 = repo / "prompts" / "lending-advisor" / "v1.yaml"
        worktree_v1.write_text("body: TAMPERED\n", encoding="utf-8")
        v1_after = load_at_tag(repo, "v1")
        assert v1_after["body"] == v1_before["body"]

        changelog = repo / "prompts" / "lending-advisor" / "CHANGELOG.md"
        changelog.write_text(
            "- 2026-10-10T00:00:00Z | rollback v2 -> v1 | operator=local-developer "
            "| reason=demonstrate reverting to immutable last-known-good tag\n",
            encoding="utf-8",
        )
        print("Versions sorted numerically:", available)
        print("Tagged v1 body after worktree tampering:", v1_after["body"])
        print("Rollback log:", changelog.read_text(encoding="utf-8").strip())
        print("All demo commits and tags are isolated in a temporary repository.")


if __name__ == "__main__":
    main()