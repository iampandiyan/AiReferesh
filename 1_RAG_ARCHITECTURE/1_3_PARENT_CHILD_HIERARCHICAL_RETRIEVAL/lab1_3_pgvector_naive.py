"""
lab1_3_pgvector_naive.py
==========================
Version 2 of 2 (pgvector). Same child-only retrieval, same confirmed
POL-1000 failure, via PostgreSQL/pgvector instead of FAISS.
"""
 
import os
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from lab1_3_common import build_sections, get_child_chunks, generate_answer, print_lab_output
 
load_dotenv()
 
PG_CONFIG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": os.environ.get("PG_PORT", "5432"),
    "dbname": os.environ.get("PG_DB", "rag_labs"),
    "user": os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD"),
}
EMBED_DIM = 384
 
if __name__ == "__main__":
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    sections = build_sections(num_sections=50, seed=42)
    chunks, meta = get_child_chunks(sections)
 
    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = True  # avoids leaving an open transaction that can
                             # deadlock a future run if interrupted mid-script
    register_vector(conn)
 
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("DROP TABLE IF EXISTS lab1_3_naive_chunks;")
        cur.execute(f"""
            CREATE TABLE lab1_3_naive_chunks (
                id serial PRIMARY KEY,
                section_id text,
                role text,
                chunk_text text,
                embedding vector({EMBED_DIM})
            );
        """)
 
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    with conn.cursor() as cur:
        for c, m, emb in zip(chunks, meta, embeddings):
            cur.execute(
                """
                INSERT INTO lab1_3_naive_chunks (section_id, role, chunk_text, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (m["section_id"], m["role"], c, emb),  # numpy array directly, not .tolist()
            )
 
    target = next(s for s in sections if s["id"] == "POL-1000")
    question = target["query"]
    q_emb = embed_model.encode([question], normalize_embeddings=True)[0]
 
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT chunk_text, 1 - (embedding <=> %s) AS similarity
            FROM lab1_3_naive_chunks
            ORDER BY embedding <=> %s
            LIMIT %s;
            """,
            (q_emb, q_emb, 2),
        )
        retrieved = cur.fetchall()
 
    answer = generate_answer(retrieved[0][0], question)
 
    print_lab_output(chunks, question, retrieved, answer)
    print(f"\n>>> The correct qualifier is: {target['qualifier_text']}")
    print(">>> Check whether the LLM answer above mentions this exception at all.")
    conn.close()
