"""
lab1_1_pgvector_rag.py
========================
Same naive RAG pipeline as lab1_1_naive_rag.py, but using PostgreSQL +
pgvector as the vector store instead of FAISS. Same document, same
chunking, same embedding model, same LLM -- only the vector store changes.
This lets you compare retrieval behavior between an in-memory library
(FAISS) and a production-style database (pgvector) directly.
"""

import os
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from lab1_1_naive_rag import DOCUMENT, naive_chunk, generate_answer

load_dotenv()

PG_CONFIG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": os.environ.get("PG_PORT", "5432"),
    "dbname": os.environ.get("PG_DB", "rag_labs"),
    "user": os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD"),
}

EMBED_DIM = 384  # all-MiniLM-L6-v2 output dimension


def get_connection():
    conn = psycopg2.connect(**PG_CONFIG)
    register_vector(conn)
    return conn


def setup_table(conn):
    """Drops and recreates the table each run so the lab is repeatable
    without leftover rows from previous runs piling up."""
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("DROP TABLE IF EXISTS lab1_chunks;")
        cur.execute(f"""
            CREATE TABLE lab1_chunks (
                id serial PRIMARY KEY,
                chunk_text text,
                embedding vector({EMBED_DIM})
            );
        """)
    conn.commit()


def insert_chunks(conn, chunks, model):
    embeddings = model.encode(chunks, normalize_embeddings=True)
    with conn.cursor() as cur:
        for text, emb in zip(chunks, embeddings):
            cur.execute(
                "INSERT INTO lab1_chunks (chunk_text, embedding) VALUES (%s, %s)",
                (text, emb),  # <-- pass numpy array directly, not emb.tolist()
            )
    conn.commit()


def retrieve(conn, query, model, top_k=1):
    q_emb = model.encode([query], normalize_embeddings=True)[0]
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT chunk_text, 1 - (embedding <=> %s) AS similarity
            FROM lab1_chunks
            ORDER BY embedding <=> %s
            LIMIT %s;
            """,
            (q_emb, q_emb, top_k),  # <-- pass numpy array directly, not q_emb.tolist()
        )
        results = cur.fetchall()
    print(f"\nQUERY: {query}")
    for chunk_text, score in results:
        print(f"  [similarity={score:.4f}] {chunk_text}")
    return results


if __name__ == "__main__":
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    conn = get_connection()

    setup_table(conn)

    chunks = naive_chunk(DOCUMENT, chunk_size=120)
    print(f"Inserting {len(chunks)} naive chunks into Postgres...")
    insert_chunks(conn, chunks, embed_model)

    # Same paraphrased query that broke FAISS retrieval in Lab 1.1 Part 3
    question = "I just joined last month, can I work from home two days a week?"
    results = retrieve(conn, question, embed_model, top_k=1)
    top_chunk, score = results[0]

    answer = generate_answer(top_chunk, question)
    print(f"\nLLM ANSWER:\n{answer}")

    print(f"\n>>> Compare this retrieved chunk and answer to the FAISS version")
    print(f">>> in Lab 1.1 Part 3. Same document, same chunking, same bug --")
    print(f">>> pgvector doesn't fix a chunking problem any more than FAISS")
    print(f">>> does, because retrieval quality is bottlenecked by chunking,")
    print(f">>> not by which vector store holds the vectors.")

    conn.close()