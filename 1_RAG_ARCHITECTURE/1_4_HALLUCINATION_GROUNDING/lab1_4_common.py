"""
lab1_4_common.py
==================
Fully standalone shared module for Lab 1.4.
"""
 
import os
import random
import itertools
from dotenv import load_dotenv
from together import Together
 
load_dotenv()
client = Together(api_key=os.environ.get("TOGETHER_STUDY_API_KEY"))
MODEL = "openai/gpt-oss-20b"
 
ACTIONS = [
    "work from home", "expense client dinners", "borrow a company laptop",
    "access the finance shared drive", "take unpaid leave",
    "claim mileage reimbursement", "use a company car", "work flexible hours",
    "carry over unused vacation days", "receive a signing bonus advance",
]
DOMAINS = [
    "engineering", "sales", "marketing", "operations", "finance",
    "support", "hr", "legal", "product", "design",
]
UNITS = ["days", "times", "hours", "occasions"]
PERIODS = ["week", "month", "quarter", "year"]
 
 
def build_sections(num_sections=50, seed=42):
    """Same generator family as Lab 1.3, one rule sentence per section --
    no qualifier needed, since this lab tests generation-layer grounding
    rather than retrieval-layer chunk boundaries."""
    random.seed(seed)
    combos = list(itertools.product(ACTIONS, DOMAINS))
    random.shuffle(combos)
    chosen = combos[:num_sections]
 
    sections = []
    for i, (action, domain) in enumerate(chosen):
        code = f"POL-{2000 + i}"
        limit = random.randint(1, 5)
        unit = random.choice(UNITS)
        period = random.choice(PERIODS)
        rule_text = (
            f"Policy {code}: {domain.capitalize()} team members may {action} "
            f"up to {limit} {unit} per {period}."
        )
        sections.append({
            "id": code, "action": action, "domain": domain,
            "limit": limit, "unit": unit, "period": period,
            "rule_text": rule_text,
            "query": f"How many {unit} per {period} may {domain} team members {action}?",
        })
    return sections
 
 
def generate_answer(context, question):
    """STRICT grounding prompt -- explicitly instructs the model on
    exactly what to say when context is insufficient."""
    prompt = f"""Answer the employee's question using ONLY the context below.
If the context does not contain the answer, say exactly: "Not found in the provided context."
Do not guess or use outside knowledge.
 
CONTEXT:
{context}
 
QUESTION: {question}
 
ANSWER:"""
    response = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0,
    )
    return response.choices[0].message.content
 
 
def generate_answer_naive(context, question):
    """NAIVE prompt -- the kind many RAG tutorials ship with by default,
    no explicit instruction about what to do when context is insufficient.
    This is the CONTROL for isolating whether strict grounding instructions
    actually cause the difference in hallucination rate, or whether the
    model would behave the same either way."""
    prompt = f"""Answer the following question based on the context provided.
 
Context: {context}
 
Question: {question}
 
Answer:"""
    response = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0,
    )
    return response.choices[0].message.content
 
 
def contains_number(text):
    import re
    return bool(re.search(r"\d+", text))
 
 
def print_section(title):
    print(f"\n{'=' * 40}\n{title}\n{'=' * 40}")
 
 
def print_lab_output(all_chunks, query, retrieved, answer):
    print_section("ALL CHUNKS CREATED")
    for i, c in enumerate(all_chunks):
        print(f"[{i}] {c}")
    print_section("QUERY")
    print(query)
    print_section("RETRIEVED CHUNK(S)")
    for chunk_text, score in retrieved:
        print(f"[score={score:.4f}] {chunk_text}")
    print_section("LLM ANSWER")
    print(answer)
