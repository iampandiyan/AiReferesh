"""
lab1_5_common.py
==================
Fully standalone shared module for Lab 1.5.
"""
 
import os
import re
import random
from dotenv import load_dotenv
from together import Together
 
load_dotenv()
client = Together(api_key=os.environ.get("TOGETHER_STUDY_API_KEY"))
MODEL = "openai/gpt-oss-20b"
 
DOMAINS = [
    "engineering", "sales", "marketing", "operations", "finance",
    "support", "hr", "legal", "product", "design",
]
REGIONS = ["North", "South", "East", "West", "Central"]
 
FIRST_NAMES = ["Alice", "Bilal", "Chen", "Diana", "Emeka", "Fiona", "Gabriel",
               "Hana", "Ivan", "Jasmine", "Kenji", "Lucia", "Malik", "Nadia",
               "Omar", "Priya", "Quinn", "Rosa", "Sanjay", "Tara"]
LAST_NAMES = ["Reyes", "Nkomo", "Petrov", "Sato", "Okafor", "Lindqvist",
              "Mehta", "Fontaine", "Yilmaz", "Choudhury", "Novak", "Diallo"]
 
UNITS = ["expense requests", "purchase orders", "contract approvals", "leave requests"]
PERIODS = ["month", "quarter"]
 
 
def build_corpus(num_teams=50, seed=42):
    """Each team has a manager (Chunk A: the BRIDGE fact) and that manager
    has an approval limit (Chunk B: the TARGET fact). Chunk B's all share
    near-identical wording except name/number -- nothing in a single-shot
    query can discriminate the CORRECT manager's Chunk B from any other,
    since the manager's name never appears in the question at all. It is
    only reachable by first resolving the bridge in Chunk A."""
    random.seed(seed)
    teams = [f"{d.capitalize()} {r}" for d in DOMAINS for r in REGIONS][:num_teams]
 
    names = [f"{f} {l}" for f in FIRST_NAMES for l in LAST_NAMES]
    random.shuffle(names)
    managers = names[:num_teams]
 
    records = []
    for team, manager in zip(teams, managers):
        limit = random.randint(5, 50)
        unit = random.choice(UNITS)
        period = random.choice(PERIODS)
        chunk_a = f"The {team} team is managed by {manager}."
        chunk_b = f"{manager} has an approval limit of {limit} {unit} per {period}."
        records.append({
            "team": team, "manager": manager, "limit": limit,
            "unit": unit, "period": period,
            "chunk_a": chunk_a, "chunk_b": chunk_b,
            "query": f"What is the approval limit for the manager of the {team} team?",
        })
    return records
 
 
def get_chunks(records):
    chunks, meta = [], []
    for r in records:
        chunks.append(r["chunk_a"]); meta.append({"team": r["team"], "role": "bridge_manager"})
        chunks.append(r["chunk_b"]); meta.append({"team": r["team"], "role": "target_limit"})
    return chunks, meta
 
 
def extract_manager_name(chunk_a_text):
    """Chunk A's format is fixed, so the bridge entity can be parsed
    deterministically -- no LLM call needed for this hop."""
    match = re.search(r"managed by (.+)\.", chunk_a_text)
    return match.group(1) if match else None
 
 
def generate_answer(context, question):
    prompt = f"""Answer the question using ONLY the context below.
If the context does not contain the answer, say exactly: "Not found in the provided context."
 
CONTEXT:
{context}
 
QUESTION: {question}
 
ANSWER:"""
    response = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0,
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
