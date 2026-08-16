"""
lab1_2_pgvector_naive.py
==========================
Version 2 of 2 (pgvector). Same corpus, same confirmed failing pair,
via PostgreSQL/pgvector instead of FAISS.
"""
 
import os
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from lab1_2_common import get_chunks, generate_answer, print_lab_output
 
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
    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = True  # avoids leaving an open transaction that can
                             # deadlock a future run if interrupted mid-script
    register_vector(conn)
 
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("DROP TABLE IF EXISTS lab1_2_chunks;")
        cur.execute(f"""
            CREATE TABLE lab1_2_chunks (
                id serial PRIMARY KEY,
                chunk_text text,
                embedding vector({EMBED_DIM})
            );
        """)
    conn.commit()
 
    chunks = get_chunks()
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    with conn.cursor() as cur:
        for text, emb in zip(chunks, embeddings):
            cur.execute(
                "INSERT INTO lab1_2_chunks (chunk_text, embedding) VALUES (%s, %s)",
                (text, emb),
            )
    conn.commit()
 
    question = "I'm getting ERR-5012, what should I do?"
    q_emb = embed_model.encode([question], normalize_embeddings=True)[0]
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT chunk_text, 1 - (embedding <=> %s) AS similarity
            FROM lab1_2_chunks
            ORDER BY embedding <=> %s
            LIMIT %s;
            """,
            (q_emb, q_emb, 2),
        )
        retrieved = cur.fetchall()
 
    answer = generate_answer(retrieved[0][0], question)
 
    print_lab_output(chunks, question, retrieved, answer)
    conn.close()
