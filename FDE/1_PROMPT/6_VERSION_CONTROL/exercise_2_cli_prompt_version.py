"""Exercise 2: resolve prompt version from CLI, environment, then CURRENT.

Run independently with `python -m pip install openai pyyaml` and
TOGETHER_STUDY_API_KEY set for a live response. Example:
`python exercise_2_cli_prompt_version.py --query "monthly payment for $2400" --prompt-version v1`
The script creates isolated demo v1/v2 prompt files beside itself when first run.

Lesson: make precedence explicit: CLI override > PROMPT_VERSION > CURRENT. Print the
resolved prompt version so operators can identify exactly what a request loaded.
"""

import argparse
import os
from pathlib import Path

import yaml
from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
ROOT = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "prompts" / "lending-advisor"


def ensure_demo_prompts() -> None:
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    for version, suffix in (("v1", "Explain assumptions and avoid inventing facts."),
                            ("v2", "Explain assumptions, avoid inventing facts, and be concise.")):
        path = PROMPT_DIR / f"{version}.yaml"
        if not path.exists():
            spec = {"name": "lending-advisor", "version": version, "model": MODEL,
                    "author": "local-developer", "created_at": "2026-10-10T00:00:00Z",
                    "golden_hash": "demo-only", "body": "You are a lending advisor. " + suffix}
            path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    current = PROMPT_DIR / "CURRENT"
    if not current.exists():
        current.write_text("v1\n", encoding="utf-8")


def resolve_version(name: str, cli_arg: str | None) -> str:
    if cli_arg:
        return cli_arg
    env_version = os.environ.get("PROMPT_VERSION")
    if env_version:
        return env_version.strip()
    current_path = ROOT / "prompts" / name / "CURRENT"
    if current_path.is_file():
        version = current_path.read_text(encoding="utf-8").strip()
        if version:
            return version
    raise RuntimeError(f"No version for {name}; pass --prompt-version, set PROMPT_VERSION, or provide CURRENT.")


def load_prompt(name: str, version: str) -> dict:
    path = ROOT / "prompts" / name / f"{version}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt {name}@{version} is missing: {path}")
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a selected prompt version")
    parser.add_argument("--prompt-version", help="Override PROMPT_VERSION and CURRENT")
    parser.add_argument("--query", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    ensure_demo_prompts()
    version = resolve_version("lending-advisor", args.prompt_version)
    try:
        spec = load_prompt("lending-advisor", version)
    except FileNotFoundError as error:
        raise SystemExit(str(error)) from error
    print(f"[loaded] lending-advisor@{version} (model={spec['model']})")

    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        print("Model call skipped; version resolution succeeded. Set TOGETHER_STUDY_API_KEY for a live response.")
        return
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    response = client.chat.completions.create(
        model=spec["model"],
        messages=[{"role": "system", "content": spec["body"]}, {"role": "user", "content": args.query}],
        max_tokens=180,
    )
    print(response.choices[0].message.content or "")


if __name__ == "__main__":
    main()