"""
lab1_2_pgvector_hybrid.py
============================
Version 2 of 2 (pgvector). Hybrid search entirely inside PostgreSQL:
tsvector full-text search (lexical) + pgvector (semantic), fused with
RRF in a single SQL query using window functions. No external BM25
library needed on this side -- this is the standard "no extra
dependency" production pattern for Postgres-based RAG.
"""
 
import os
import re
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from lab1_2_common import get_chunks, generate_answer, print_lab_output, build_or_tsquery
 
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
        cur.execute("DROP TABLE IF EXISTS lab1_2_hybrid_chunks;")
        cur.execute(f"""
            CREATE TABLE lab1_2_hybrid_chunks (
                id serial PRIMARY KEY,
                chunk_text text,
                ts_content tsvector,
                embedding vector({EMBED_DIM})
            );
        """)
        cur.execute("""
            CREATE INDEX ON lab1_2_hybrid_chunks USING GIN (ts_content);
        """)
    conn.commit()
 
    chunks = get_chunks()
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    with conn.cursor() as cur:
        for text, emb in zip(chunks, embeddings):
            cur.execute(
                """
                INSERT INTO lab1_2_hybrid_chunks (chunk_text, ts_content, embedding)
                VALUES (%s, to_tsvector('english', %s), %s)
                """,
                (text, text, emb),
            )
    conn.commit()
 
    question = "I'm getting ERR-5012, what should I do?"
    q_emb = embed_model.encode([question], normalize_embeddings=True)[0]
 
    tsquery_str = build_or_tsquery(question)
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH bm25_ranked AS (
                SELECT id, chunk_text,
                       ROW_NUMBER() OVER (ORDER BY ts_rank_cd(ts_content, to_tsquery('english', %s)) DESC) AS rank
                FROM lab1_2_hybrid_chunks
                WHERE ts_content @@ to_tsquery('english', %s)
            ),
            vector_ranked AS (
                SELECT id, chunk_text,
                       ROW_NUMBER() OVER (ORDER BY embedding <=> %s) AS rank
                FROM lab1_2_hybrid_chunks
            )
            SELECT
                COALESCE(b.chunk_text, v.chunk_text) AS chunk_text,
                COALESCE(1.0 / (60 + b.rank), 0) + COALESCE(1.0 / (60 + v.rank), 0) AS rrf_score
            FROM bm25_ranked b
            FULL OUTER JOIN vector_ranked v ON b.id = v.id
            ORDER BY rrf_score DESC
            LIMIT %s;
            """,
            (tsquery_str, tsquery_str, q_emb, 5),
        )
        retrieved = cur.fetchall()
 
    answer = generate_answer(retrieved[0][0], question)
 
    print_lab_output(chunks, question, retrieved, answer)
    print("\n>>> This fusion happens entirely inside Postgres -- one round trip,")
    print(">>> no separate BM25 library needed on this side. Compare the RRF")
    print(">>> scores and final answer directly against the FAISS version.")
    conn.close()
