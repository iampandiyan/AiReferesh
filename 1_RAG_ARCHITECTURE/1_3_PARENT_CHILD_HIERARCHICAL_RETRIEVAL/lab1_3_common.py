"""
lab1_3_common.py
==================
Fully standalone shared module for Lab 1.3.
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
CONDITIONS = [
    "on probation", "under an active performance improvement plan",
    "classified as contractors", "part-time employees",
    "new hires in their first 90 days", "on an unpaid leave of absence",
    "based outside the country", "in a temporary role",
]
ALTERNATIVES = [
    "submit a written request to their manager",
    "wait until their status changes",
    "escalate to HR for case-by-case approval",
    "use the standard reimbursement process instead",
    "consult the exceptions handbook",
]
UNITS = ["days", "times", "hours", "occasions"]
PERIODS = ["week", "month", "quarter", "year"]
 
 
def build_sections(num_sections=50, seed=42):
    """Generates num_sections policy sections, each with a RULE sentence
    and a QUALIFIER sentence stating an exception. Each section's
    (action, domain) pair is unique (sampled without replacement)."""
    random.seed(seed)
    combos = list(itertools.product(ACTIONS, DOMAINS))
    random.shuffle(combos)
    chosen = combos[:num_sections]
 
    sections = []
    for i, (action, domain) in enumerate(chosen):
        code = f"POL-{1000 + i}"
        limit = random.randint(1, 5)
        unit = random.choice(UNITS)
        period = random.choice(PERIODS)
        condition = random.choice(CONDITIONS)
        alternative = random.choice(ALTERNATIVES)
 
        rule_text = (
            f"Policy {code}: {domain.capitalize()} team members may {action} "
            f"up to {limit} {unit} per {period}."
        )
        qualifier_text = (
            f"However, {domain.capitalize()} team members who are {condition} "
            f"are not eligible for this and must instead {alternative}."
        )
        sections.append({
            "id": code,
            "action": action,
            "domain": domain,
            "rule_text": rule_text,
            "qualifier_text": qualifier_text,
            "parent_text": rule_text + " " + qualifier_text,
            "query": f"Can {domain} team members {action}?",
        })
    return sections
 
 
def get_child_chunks(sections):
    """Flattens every section into its two child chunks (rule, qualifier),
    each tagged with which section and role it belongs to."""
    chunks, meta = [], []
    for s in sections:
        chunks.append(s["rule_text"])
        meta.append({"section_id": s["id"], "role": "rule"})
        chunks.append(s["qualifier_text"])
        meta.append({"section_id": s["id"], "role": "qualifier"})
    return chunks, meta
 
 
def generate_answer(context, question):
    prompt = f"""Answer the employee's question using ONLY the context below.
If the context doesn't fully answer the question, say what it says and nothing more.
 
CONTEXT:
{context}
 
QUESTION: {question}
 
ANSWER:"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content
 
 
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
