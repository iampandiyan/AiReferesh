import os
import re
from pathlib import Path

from dotenv import load_dotenv
from together import Together

load_dotenv(Path(__file__).resolve().with_name(".env"))
api_key = os.environ.get("TOGETHER_STUDY_API_KEY")
if not api_key:
    raise RuntimeError("TOGETHER_STUDY_API_KEY is not set in the adjacent .env file.")

client = Together(api_key=api_key)

QUERIES = [
    "Oye cuando llega el dinero?",
    "Procesa el refund porfa, es urgent",
    "Por que el KYC esta pending?",
    "El settlement no llego ni despues de T+2",
    "El order se cancelo, quiero mi dinero back",
    "El payment fallo pero me cobraron la card",
    "Quiero raise un dispute",
    "Cuando es el SSN verification?",
    "El webhook no llega",
    "En cuantos dias llega el refund?",
    "Quiero switch de bank transfer a card",
    "Necesito el sales tax invoice de un payment viejo",
    "Quiero update mi settlement account",
    "La API key se revoco, como creo una nueva?",
    "Que es este transaction id?",
    "Un customer puso complaint por wrong amount",
    "Quiero stop el recurring payment",
    "Como llega el wallet refund?",
    "Crea un payment link de 60 dolares",
    "Parece una fraudulent transaction",
]

CODEMIXED_WORDS = {
    "el", "la", "es", "que", "de", "mi", "un", "una", "por", "cuando",
    "como", "quiero", "llega", "dinero", "pero", "porfa", "urgent", "dias",
    "nueva", "esta", "necesito", "estamos", "crea",
}
LANG_RULE = "Respond in the user's language. If code-mixed, mirror code-mixed."
PADDING = (
    "Stripe processes payments for 10M+ merchants across cards and ACH, "
    "cards, bank transfer, and wallets. Settlement is T+2 by default. " * 12
)


def is_codemixed_reply(text: str) -> bool:
    tokens = re.findall(r"[a-z]+", text.lower())
    return sum(token in CODEMIXED_WORDS for token in tokens) >= 2


def build_prompt(position: str) -> str:
    sections = {
        "system": "You are a Stripe merchant-support agent.",
        "role": "You answer merchant tickets in 2-3 sentences.",
        "context": PADDING,
        "instructions": "1. Read the message.\n2. Draft a 2-3 sentence reply.",
        "examples": 'Input: "Quiero mi refund"\nOutput: "El refund llega en 5 dias."',
        "format": "Reply with 2-3 sentences only.",
    }
    if position == "top":
        sections["system"] += "\n" + LANG_RULE
    elif position == "middle":
        sections["context"] = PADDING[:600] + " " + LANG_RULE + " " + PADDING[600:]
    elif position in {"end", "end_repeated"}:
        sections["instructions"] += "\n3. " + LANG_RULE
        if position == "end_repeated":
            sections["examples"] += "\n\nReminder: " + LANG_RULE
    else:
        raise ValueError(f"Unknown instruction position: {position}")
    return (
        "[SYSTEM]\n" + sections["system"] + "\n\n[ROLE]\n" + sections["role"]
        + "\n\n[CONTEXT]\n" + sections["context"] + "\n\n[INSTRUCTIONS]\n"
        + sections["instructions"] + "\n\n[EXAMPLES]\n" + sections["examples"]
        + "\n\n[FORMAT]\n" + sections["format"]
    )


def score(position: str) -> float:
    prompt = build_prompt(position)
    hits = 0
    for query in QUERIES:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query},
            ],
        )
        if is_codemixed_reply(response.choices[0].message.content or ""):
            hits += 1
    return hits / len(QUERIES)


print(f"{'position':16s} | compliance")
print("-" * 35)
for position in ["top", "middle", "end", "end_repeated"]:
    compliance = score(position)
    print(f"{position:16s} | {compliance * 100:5.1f}%")