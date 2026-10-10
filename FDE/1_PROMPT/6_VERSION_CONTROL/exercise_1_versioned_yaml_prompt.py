"""Exercise 1: lift a system prompt into a versioned YAML file.

Run independently with `python -m pip install openai pyyaml` and
TOGETHER_STUDY_API_KEY set. It creates prompts/lending-advisor/v1.yaml next to this
script, hashes its embedded synthetic golden cases, loads the prompt, and smoke-tests it.

Lesson: prompts are deployable assets. Store metadata and content together, bind a
version to the evaluation set hash, and load prompt text instead of duplicating literals.
"""

import hashlib
import os
from pathlib import Path

import yaml
from openai import OpenAI


MODEL = "openai/gpt-oss-120b"
ROOT = Path(__file__).resolve().parent
PROMPT_PATH = ROOT / "prompts" / "lending-advisor" / "v1.yaml"
GOLDEN_CASES = [
    "credit score 690, $6,000 business loan eligible?",
    "monthly payment for $2,400, 18%, 24 months?",
    "mi credit score es 690, elegible para un business loan?",
    "What documents are needed for a small-business loan?",
    "Do not repeat the synthetic ID CUST_TEST_001 in your answer.",
]
PROMPT_BODY = """You are an AcmeCorp small-business lending advisor.
Explain assumptions and distinguish annual rates from monthly rates.
Respond in the language used by the customer. Never invent missing facts.
Do not echo personal identifiers. Use only the synthetic policy context in the request.
"""


def load_prompt(name: str, version: str) -> dict:
    path = ROOT / "prompts" / name / f"{version}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt {name}@{version} not found at {path}")
    with path.open(encoding="utf-8") as stream:
        spec = yaml.safe_load(stream)
    required = {"name", "version", "model", "author", "created_at", "golden_hash", "body"}
    missing = required - set(spec or {})
    if missing:
        raise ValueError(f"Prompt metadata missing keys: {sorted(missing)}")
    return spec


def main() -> None:
    golden_hash = hashlib.sha256("\n".join(GOLDEN_CASES).encode("utf-8")).hexdigest()[:16]
    spec = {
        "name": "lending-advisor",
        "version": "v1",
        "model": MODEL,
        "author": os.environ.get("PROMPT_AUTHOR", "local-developer"),
        "created_at": "2026-10-10T00:00:00Z",
        "golden_hash": golden_hash,
        "body": PROMPT_BODY,
    }
    PROMPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROMPT_PATH.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True), encoding="utf-8")
    loaded = load_prompt("lending-advisor", "v1")
    print(f"Wrote {PROMPT_PATH}; golden_hash={golden_hash}")

    api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
    if not api_key:
        print("Smoke test skipped; set TOGETHER_STUDY_API_KEY to make the Together call.")
        return
    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
    response = client.chat.completions.create(
        model=loaded["model"],
        messages=[
            {"role": "system", "content": loaded["body"]},
            {"role": "user", "content": "Mi credit score es 690, elegible para un business loan?"},
        ],
        max_tokens=180,
    )
    print("Loaded version:", loaded["version"])
    print("Reply:", response.choices[0].message.content or "")


if __name__ == "__main__":
    main()