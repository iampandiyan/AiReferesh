"""
lab1_6_common.py
==================
Fully standalone shared module for Lab 1.6.
"""

import os
import random
from dotenv import load_dotenv
from together import Together

load_dotenv()
client = Together(api_key=os.environ.get("TOGETHER_STUDY_API_KEY"))
MODEL = "openai/gpt-oss-20b"

TOPICS = ["billing", "authentication", "deployment", "networking", "storage",
          "permissions", "notifications", "search", "reporting", "integrations",
          "backups", "scheduling", "monitoring", "encryption", "caching"]
VERBS = ["reset", "configure", "troubleshoot", "enable", "disable", "audit", "migrate"]
OBJECTS = ["account", "pipeline", "cluster", "endpoint", "credential", "dashboard", "workspace"]


def build_scale_corpus(num_chunks=5000, seed=42):
    """Generates an arbitrary number of unique, realistic-length knowledge-base
    articles for testing retrieval at scale. Uniqueness comes from the
    incrementing article ID, not just the combinatorial word space, so this
    scales cleanly to any size."""
    random.seed(seed)
    chunks = []
    for i in range(num_chunks):
        topic = random.choice(TOPICS)
        verb = random.choice(VERBS)
        obj = random.choice(OBJECTS)
        minutes = random.randint(1, 999)
        text = (
            f"Article KB-{i:06d}: To {verb} the {obj} related to {topic}, "
            f"follow the standard procedure and allow up to {minutes} minutes "
            f"for the change to take effect."
        )
        chunks.append(text)
    return chunks


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
    print_section("ALL CHUNKS CREATED (sample, first 20 of possibly many)")
    for i, c in enumerate(all_chunks[:20]):
        print(f"[{i}] {c}")
    if len(all_chunks) > 20:
        print(f"... ({len(all_chunks) - 20} more chunks not shown)")
    print_section("QUERY")
    print(query)
    print_section("RETRIEVED CHUNK(S)")
    for chunk_text, score in retrieved:
        print(f"[score={score:.4f}] {chunk_text}")
    print_section("LLM ANSWER")
    print(answer)