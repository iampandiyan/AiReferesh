"""
lab1_1_pgvector_naive.py
==========================
Version 2 of 2 (pgvector). Naive fixed-size chunking + PostgreSQL/pgvector.
Reproduces the SAME negation-splitting bug as the FAISS version, proving
the bug is upstream in chunking, not the vector store.
"""
 
import os
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from lab1_1_common import DOCUMENT, naive_chunk, generate_answer, print_lab_output
 
load_dotenv()
 
PG_CONFIG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": os.environ.get("PG_PORT", "5432"),
    "dbname": os.environ.get("PG_DB", "rag_labs"),
    "user": os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD"),
}
EMBED_DIM = 384  # all-MiniLM-L6-v2 output dimension
 
if __name__ == "__main__":
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    conn = psycopg2.connect(**PG_CONFIG)
    register_vector(conn)
 
    # Drop and recreate each run so the lab is repeatable with no leftovers.
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("DROP TABLE IF EXISTS lab1_1_naive_chunks;")
        cur.execute(f"""
            CREATE TABLE lab1_1_naive_chunks (
                id serial PRIMARY KEY,
                chunk_text text,
                embedding vector({EMBED_DIM})
            );
        """)
    conn.commit()
 
    chunks = naive_chunk(DOCUMENT, chunk_size=120)
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    with conn.cursor() as cur:
        for text, emb in zip(chunks, embeddings):
            cur.execute(
                "INSERT INTO lab1_1_naive_chunks (chunk_text, embedding) VALUES (%s, %s)",
                (text, emb),  # pass the numpy array directly -- NOT emb.tolist()
            )
    conn.commit()
 
    question = "I just joined last month, can I work from home two days a week?"
    q_emb = embed_model.encode([question], normalize_embeddings=True)[0]
    with conn.cursor() as cur:
        # <=> is pgvector's cosine DISTANCE operator (0 = identical).
        # Converting to (1 - distance) makes it read the same as FAISS's score.
        cur.execute(
            """
            SELECT chunk_text, 1 - (embedding <=> %s) AS similarity
            FROM lab1_1_naive_chunks
            ORDER BY embedding <=> %s
            LIMIT %s;
            """,
            (q_emb, q_emb, 1),
        )
        retrieved = cur.fetchall()
 
    answer = generate_answer(retrieved[0][0], question)
 
    print_lab_output(chunks, question, retrieved, answer)
    conn.close()
