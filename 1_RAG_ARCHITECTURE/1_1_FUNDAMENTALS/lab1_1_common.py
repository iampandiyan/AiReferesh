"""
lab1_1_common.py
==================
Shared code used by all FAISS/pgvector lab variants: the document,
both chunking strategies, the LLM call, and the standardized console
output format every lab script in this series uses.
"""
 
import os
import re
from dotenv import load_dotenv
from together import Together
 
load_dotenv()
client = Together(api_key=os.environ.get("TOGETHER_STUDY_API_KEY"))
MODEL = "openai/gpt-oss-20b"
 
# ---------------------------------------------------------------------------
# The document we're building RAG over. Small and readable on purpose --
# you should be able to read the whole thing and know the "correct" answer
# to any question before the LLM tells you, so you can judge it honestly.
# ---------------------------------------------------------------------------
DOCUMENT = """
Leave Policy Section 3: Annual Leave Entitlement. Employees are entitled to 18 days
of annual leave per calendar year, accrued monthly at 1.5 days per month. Unused
leave can be carried forward up to a maximum of 10 days into the next calendar year.
Any leave beyond the 10-day carry-forward cap is forfeited and will not be paid out.
 
Leave Policy Section 4: Sick Leave. Employees are entitled to 12 days of sick leave
per year. Sick leave does not carry forward and lapses at the end of the calendar year.
A medical certificate is required for sick leave exceeding 2 consecutive days.
 
Leave Policy Section 5: Work From Home. Employees may work from home up to 2 days
per week, subject to manager approval. Employees in probation period are NOT eligible
for work from home and must work from office for the first 6 months of employment.
 
Leave Policy Section 6: Notice Period. The standard notice period for resignation is
60 days for employees above 2 years of tenure, and 30 days for employees below 2 years
of tenure. The company reserves the right to waive the notice period at its discretion.
"""
 
 
# ---------------------------------------------------------------------------
# BROKEN chunker: splits by raw character count, no sentence awareness.
# Used in Part 3 to reproduce the failure.
# ---------------------------------------------------------------------------
def naive_chunk(text, chunk_size=120):
    text = text.strip().replace("\n", " ")
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
 
 
# ---------------------------------------------------------------------------
# FIXED chunker: groups whole sentences up to a size limit, never
# splitting mid-clause. Used in Part 4 to fix the failure.
# ---------------------------------------------------------------------------
def sentence_aware_chunk(text, max_chars=250):
    text = text.strip().replace("\n", " ")
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""
    for sent in sentences:
        if len(current) + len(sent) <= max_chars:
            current += (" " + sent if current else sent)
        else:
            if current:
                chunks.append(current.strip())
            current = sent
    if current:
        chunks.append(current.strip())
    return chunks
 
 
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
    """Standard console output format for every lab script in this series:
    all chunks -> query -> retrieved chunk(s) -> LLM answer."""
    print_section("ALL CHUNKS CREATED")
    for i, c in enumerate(all_chunks):
        print(f"[{i}] {c}")
 
    print_section("QUERY")
    print(query)
 
    print_section("RETRIEVED CHUNK(S)")
    for chunk_text, score in retrieved:
        print(f"[similarity={score:.4f}] {chunk_text}")
 
    print_section("LLM ANSWER")
    print(answer)
