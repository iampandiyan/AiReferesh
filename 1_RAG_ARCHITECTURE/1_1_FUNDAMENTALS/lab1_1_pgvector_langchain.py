"""
lab1_1_pgvector_langchain.py
===============================
Version 2 of 2 (pgvector). Same RecursiveCharacterTextSplitter chunking,
stored and retrieved via PostgreSQL/pgvector instead of FAISS.
"""

import os
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from lab1_1_common import DOCUMENT, generate_answer, print_lab_output

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
    register_vector(conn)

    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("DROP TABLE IF EXISTS lab1_1_langchain_chunks;")
        cur.execute(f"""
            CREATE TABLE lab1_1_langchain_chunks (
                id serial PRIMARY KEY,
                chunk_text text,
                embedding vector({EMBED_DIM})
            );
        """)
    conn.commit()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=250,
        chunk_overlap=30,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(DOCUMENT)

    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    with conn.cursor() as cur:
        for text, emb in zip(chunks, embeddings):
            cur.execute(
                "INSERT INTO lab1_1_langchain_chunks (chunk_text, embedding) VALUES (%s, %s)",
                (text, emb),
            )
    conn.commit()

    question = "I just joined last month, can I work from home two days a week?"
    q_emb = embed_model.encode([question], normalize_embeddings=True)[0]
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT chunk_text, 1 - (embedding <=> %s) AS similarity
            FROM lab1_1_langchain_chunks
            ORDER BY embedding <=> %s
            LIMIT %s;
            """,
            (q_emb, q_emb, 1),
        )
        retrieved = cur.fetchall()

    answer = generate_answer(retrieved[0][0], question)

    print_lab_output(chunks, question, retrieved, answer)
    conn.close()
