"""Exercise 3: choose chunk boundaries based on content type.

Run with Python 3. PDF text extraction requires `python -m pip install pypdf`; no API key
or embedding model is needed. Fixture files are in the adjacent `examples/` directory.
The PDF strategy is a paragraph-boundary approximation, not semantic embedding chunking.

Lesson: PDFs, Markdown, CSV tables, code, and chat logs have different structure. CSV
row chunks must repeat their header; chat chunks should preserve speaker turns; empty and
header-only inputs are valid edge cases.
"""

import re
from pathlib import Path
from typing import Callable


def semantic_paragraphs(text: str, target_chars: int = 300) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    chunks = []
    buffer = ""
    for paragraph in paragraphs:
        candidate = f"{buffer}\n\n{paragraph}".strip()
        if buffer and len(candidate) > target_chars:
            chunks.append(buffer)
            buffer = paragraph
        else:
            buffer = candidate
    if buffer:
        chunks.append(buffer)
    return chunks


def markdown_sections(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?=^##\s)", text, flags=re.MULTILINE) if part.strip()]


def csv_rows(text: str) -> list[str]:
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) <= 1:
        return []
    header = lines[0]
    return [f"{header}\n{row}" for row in lines[1:]]


def code_boundaries(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?=^(?:def|class)\s)", text, flags=re.MULTILINE) if part.strip()]


def chat_turns(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?=^(?:User|Agent|Customer|Assistant):\s)", text, flags=re.MULTILINE) if part.strip()]


def chunker_for(content_type: str) -> Callable[[str], list[str]]:
    strategies = {
        "pdf": semantic_paragraphs,
        "markdown": markdown_sections,
        "csv": csv_rows,
        "code": code_boundaries,
        "chat": chat_turns,
    }
    try:
        return strategies[content_type]
    except KeyError as error:
        raise ValueError(f"Unsupported content_type={content_type!r}") from error


def extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError("Read the PDF fixture by installing pypdf: python -m pip install pypdf") from error
    reader = PdfReader(str(path))
    text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if not text:
        raise ValueError(f"No extractable text found in PDF: {path}")
    return text


def main() -> None:
    examples_dir = Path(__file__).resolve().parent / "examples"
    samples = {
        "pdf": ("sample_policy.pdf", extract_pdf_text(examples_dir / "sample_policy.pdf")),
        "markdown": ("sample_policy.md", (examples_dir / "sample_policy.md").read_text(encoding="utf-8")),
        "csv": ("sample_rates.csv", (examples_dir / "sample_rates.csv").read_text(encoding="utf-8")),
        "code": ("sample_policy_code.py", (examples_dir / "sample_policy_code.py").read_text(encoding="utf-8")),
        "chat": "User: Where is my order?\nAgent: It is on the way.\nUser: Thanks",
    }
    for kind, sample in samples.items():
        if isinstance(sample, tuple):
            filename, text = sample
        else:
            filename, text = "inline demonstration", sample
        chunks = chunker_for(kind)(text)
        print(f"\n{kind.upper()} from {filename}: {len(chunks)} chunks")
        for index, chunk in enumerate(chunks, 1):
            print(f"  [{index}] {chunk[:240]!r}")
    print("Edge cases:")
    print("empty text:", chunker_for("pdf")(""))
    print("header-only CSV:", chunker_for("csv")("Tier,Rate"))
    print("code without functions:", chunker_for("code")("x = 1\ny = 2"))
    assert chunker_for("csv")("a,b\n1,2\n3,4") == ["a,b\n1,2", "a,b\n3,4"]
    print("Lesson: preserve each format's meaningful boundaries and required context.")


if __name__ == "__main__":
    main()

"""

PDF from sample_policy.pdf: 1 chunks
  [1] 'Synthetic Lending Policy - PDF Chunking Example\nThis fixture is fictional teaching content, not legal or financial advice.\nSection 1 - Payment review\nA captured payment may be reviewed when the request is within the configured window.\nConfi'

MARKDOWN from sample_policy.md: 4 chunks
  [1] '# Synthetic Lending Operations Guide\n\nTeaching fixture for Markdown section chunking. This is fictional policy text, not legal or financial advice.'
  [2] '## Refund eligibility\n\nA payment may be reviewed for a refund when the payment status is captured and the request is within the configured review window. A support agent should confirm the transaction reference before discussing next steps.'
  [3] '## Identity verification\n\nVerification status is checked using a synthetic customer reference such as `cust_TEST_001`. Never put government-issued identifiers into an example document or a log.'
  [4] '## Escalation\n\nEscalate a request when its status is unknown, evidence conflicts, or a specialist review is required. Do not claim that a refund has been issued until a payment system confirms it.'

CSV from sample_rates.csv: 3 chunks
  [1] 'Tier,AnnualRate,EffectiveDate,SourceReference\nTier 1,6.50%,2026-10-01,RATE_TEST_001'
  [2] 'Tier,AnnualRate,EffectiveDate,SourceReference\nTier 2,7.25%,2026-10-01,RATE_TEST_001'
  [3] 'Tier,AnnualRate,EffectiveDate,SourceReference\nTier 3,8.10%,2026-10-01,RATE_TEST_001'

CODE from sample_policy_code.py: 4 chunks
  [1] '"""Synthetic example module for function-boundary chunking."""'
  [2] 'def estimate_monthly_payment(principal: float, annual_rate: float, months: int) -> float:\n    """Return a fixed-payment estimate using a nominal annual interest rate."""\n    if principal < 0 or months <= 0:\n        raise ValueError("princip'
  [3] 'def classify_review_window(age_days: int, configured_limit_days: int = 30) -> str:\n    """Classify an example payment age without contacting a payment service."""\n    if age_days < 0:\n        raise ValueError("age_days cannot be negative")\n'
  [4] 'class SyntheticPaymentRecord:\n    """A tiny fixture object; IDs here are fake and are not real payment credentials."""\n\n    def __init__(self, payment_id: str, amount_usd: int, status: str):\n        self.payment_id = payment_id\n        self'

CHAT from inline demonstration: 3 chunks
  [1] 'User: Where is my order?'
  [2] 'Agent: It is on the way.'
  [3] 'User: Thanks'
Edge cases:
empty text: []
header-only CSV: []
code without functions: ['x = 1\ny = 2']
Lesson: preserve each format's meaningful boundaries and required context.
"""