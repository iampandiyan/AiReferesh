"""Generate a tiny PDF fixture using only Python's standard library."""

from pathlib import Path


LINES = [
    "Synthetic Lending Policy - PDF Chunking Example",
    "This fixture is fictional teaching content, not legal or financial advice.",
    "",
    "Section 1 - Payment review",
    "A captured payment may be reviewed when the request is within the configured window.",
    "Confirm the synthetic payment reference before discussing next steps.",
    "",
    "Section 2 - Evidence",
    "Record the synthetic payment ID, requested amount, and short reason.",
    "Example reference: pay_TEST_4421. Never use real customer or bank identifiers.",
    "",
    "Section 3 - Escalation",
    "Escalate unknown or conflicting states to a human reviewer.",
    "Do not state that a refund was processed until a system confirms it.",
]


def pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_pdf(destination: Path) -> None:
    commands = ["BT", "/F1 11 Tf", "50 790 Td", "14 TL"]
    for index, line in enumerate(LINES):
        if index:
            commands.append("T*")
        if line:
            commands.append(f"({pdf_escape(line)}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("ascii")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for obj_number, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{obj_number} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    destination.write_bytes(pdf)


if __name__ == "__main__":
    output = Path(__file__).with_name("sample_policy.pdf")
    write_pdf(output)
    print(f"Created {output}")
