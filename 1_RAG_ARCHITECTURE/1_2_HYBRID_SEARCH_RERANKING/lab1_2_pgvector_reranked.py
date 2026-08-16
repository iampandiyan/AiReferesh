"""
lab1_2_pgvector_reranked.py
==============================
Version 2 of 2 (pgvector). Same reranking layer, on top of the
pgvector hybrid shortlist from Part 5.
"""
 
import os
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer, CrossEncoder
from dotenv import load_dotenv
from lab1_2_common import get_chunks, build_or_tsquery, generate_answer, print_lab_output
 
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
    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")
    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = True
    register_vector(conn)
 
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("DROP TABLE IF EXISTS lab1_2_reranked_chunks;")
        cur.execute(f"""
            CREATE TABLE lab1_2_reranked_chunks (
                id serial PRIMARY KEY,
                chunk_text text,
                ts_content tsvector,
                embedding vector({EMBED_DIM})
            );
        """)
        cur.execute("CREATE INDEX ON lab1_2_reranked_chunks USING GIN (ts_content);")
 
    chunks = get_chunks()
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    with conn.cursor() as cur:
        for text, emb in zip(chunks, embeddings):
            cur.execute(
                """
                INSERT INTO lab1_2_reranked_chunks (chunk_text, ts_content, embedding)
                VALUES (%s, to_tsvector('english', %s), %s)
                """,
                (text, text, emb),
            )
 
    question = "I'm getting ERR-5012, what should I do?"
    q_emb = embed_model.encode([question], normalize_embeddings=True)[0]
    tsquery_str = build_or_tsquery(question)
 
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH bm25_ranked AS (
                SELECT id, chunk_text,
                       ROW_NUMBER() OVER (ORDER BY ts_rank_cd(ts_content, to_tsquery('english', %s)) DESC) AS rank
                FROM lab1_2_reranked_chunks
                WHERE ts_content @@ to_tsquery('english', %s)
            ),
            vector_ranked AS (
                SELECT id, chunk_text,
                       ROW_NUMBER() OVER (ORDER BY embedding <=> %s) AS rank
                FROM lab1_2_reranked_chunks
            )
            SELECT
                COALESCE(b.chunk_text, v.chunk_text) AS chunk_text,
                COALESCE(1.0 / (60 + b.rank), 0) + COALESCE(1.0 / (60 + v.rank), 0) AS rrf_score
            FROM bm25_ranked b
            FULL OUTER JOIN vector_ranked v ON b.id = v.id
            ORDER BY rrf_score DESC
            LIMIT %s;
            """,
            (tsquery_str, tsquery_str, q_emb, 10),  # broader shortlist (10) before reranking narrows to fewer
        )
        shortlist = cur.fetchall()  # [(chunk_text, rrf_score), ...]
 
    # --- Rerank the shortlist with a cross-encoder ---
    pairs = [(question, chunk_text) for chunk_text, _ in shortlist]
    rerank_scores = reranker.predict(pairs)
    reranked = sorted(zip([c for c, _ in shortlist], rerank_scores), key=lambda x: x[1], reverse=True)[:5]
    retrieved = [(chunk_text, float(score)) for chunk_text, score in reranked]
 
    answer = generate_answer(retrieved[0][0], question)
 
    print_lab_output(chunks, question, retrieved, answer)
    conn.close()
