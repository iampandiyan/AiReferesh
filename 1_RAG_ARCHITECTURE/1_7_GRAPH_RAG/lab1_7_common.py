"""
lab1_7_common.py
==================
Fully standalone shared module for Lab 1.7.
"""

import os
from dotenv import load_dotenv
from together import Together
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import numpy as np

load_dotenv()
client = Together(api_key=os.environ.get("TOGETHER_STUDY_API_KEY"))
MODEL = "openai/gpt-oss-20b"

NEO4J_URI = os.environ.get("NEO4J_URI")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")


def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


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

def build_policy_variants():
    """Multiple short documents describing the SAME underlying entities
    (work-from-home policy, manager approval, probation period) using
    DIFFERENT surface phrasing -- simulating realistic variation across
    a real document set. Each extraction call is independent, so nothing
    forces the model to normalize these to the same node id across calls."""
    return [
        {"id": "DOC-01", "canonical_action": "work_from_home",
         "text": "Employees may work from home up to 2 days per week, subject to manager approval."},
        {"id": "DOC-02", "canonical_action": "work_from_home",
         "text": "Remote work is permitted for a maximum of 2 days weekly, pending supervisor sign-off."},
        {"id": "DOC-03", "canonical_action": "work_from_home",
         "text": "Staff may telecommute up to two days each week if their team lead approves."},
        {"id": "DOC-04", "canonical_action": "work_from_home",
         "text": "WFH arrangements are capped at 2 days per week and require manager authorization."},
        {"id": "DOC-05", "canonical_action": "probation",
         "text": "New hires in their probation period are not eligible for remote work."},
        {"id": "DOC-06", "canonical_action": "probation",
         "text": "Employees still in their probationary period cannot work from home."},
        {"id": "DOC-07", "canonical_action": "probation",
         "text": "Staff completing an initial trial period are excluded from telecommuting privileges."},
        {"id": "DOC-08", "canonical_action": "probation",
         "text": "During the new-hire evaluation window, WFH is not permitted."},
    ]

CANONICAL_REGISTRY = {
    "work_from_home": "WorkFromHome",
    "probation": "ProbationPeriod",
}
CANONICAL_DESCRIPTIONS = {
    "work_from_home": "working remotely from home instead of the office",
    "probation": "a new employee's initial probationary trial period",
}

def canonicalize_node_id(node_id, embed_model, canonical_embeddings, threshold=0.45):
    """Compares a newly extracted node id's embedding against a small
    registry of known canonical entities. If similar enough, rewrites
    it to the canonical id before it ever reaches Neo4j -- entity
    resolution via embedding similarity, a real production technique,
    not a hand-wavy string match."""
    node_embedding = embed_model.encode([node_id], normalize_embeddings=True)[0]
    best_match, best_score = None, threshold
    for canonical_key, canonical_emb in canonical_embeddings.items():
        score = float(np.dot(node_embedding, canonical_emb))
        if score > best_score:
            best_match, best_score = canonical_key, score
    if best_match:
        return CANONICAL_REGISTRY[best_match], best_score
    return node_id, None