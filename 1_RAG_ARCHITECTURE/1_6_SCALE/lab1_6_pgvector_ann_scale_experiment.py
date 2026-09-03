"""
lab1_6_pgvector_ann_scale_experiment.py
==========================================
Version 2 of 2 (pgvector). Same exact-vs-approximate comparison as
lab1_6_ann_scale_experiment.py, via PostgreSQL/pgvector: a table with
NO index (forces exact sequential scan) vs. a table with a native
pgvector HNSW index (approximate).
"""

import os
import time
import numpy as np
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from lab1_6_common import build_scale_corpus

load_dotenv()

PG_CONFIG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": os.environ.get("PG_PORT", "5432"),
    "dbname": os.environ.get("PG_DB", "rag_labs"),
    "user": os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD"),
}
EMBED_DIM = 384
CORPUS_SIZES = [1000, 5000, 15000]
NUM_TEST_QUERIES = 30
TOP_K = 10

if __name__ == "__main__":
    print("Loading embedding model...")
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")

    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = True
    register_vector(conn)

    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    print(f"\n{'Size':>8} | {'ExactBuild':>10} | {'HNSWBuild':>10} | {'ExactQry(ms)':>13} | {'HNSWQry(ms)':>12} | {'Recall@10':>10}")
    print("-" * 80)

    for size in CORPUS_SIZES:
        chunks = build_scale_corpus(num_chunks=size, seed=42)
        embeddings = embed_model.encode(chunks, normalize_embeddings=True, show_progress_bar=False)

        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS lab1_6_exact;")
            cur.execute("DROP TABLE IF EXISTS lab1_6_hnsw;")
            cur.execute(f"CREATE TABLE lab1_6_exact (id serial PRIMARY KEY, chunk_text text, embedding vector({EMBED_DIM}));")
            cur.execute(f"CREATE TABLE lab1_6_hnsw (id serial PRIMARY KEY, chunk_text text, embedding vector({EMBED_DIM}));")

        with conn.cursor() as cur:
            for c, emb in zip(chunks, embeddings):
                cur.execute("INSERT INTO lab1_6_exact (chunk_text, embedding) VALUES (%s, %s)", (c, emb))
                cur.execute("INSERT INTO lab1_6_hnsw (chunk_text, embedding) VALUES (%s, %s)", (c, emb))

        # Exact table gets NO index -- forces a sequential scan (true exact search)
        exact_build_time = 0.0  # no index to build

        # HNSW table gets a real pgvector HNSW index
        t0 = time.perf_counter()
        with conn.cursor() as cur:
            cur.execute("CREATE INDEX ON lab1_6_hnsw USING hnsw (embedding vector_cosine_ops);")
        hnsw_build_time = time.perf_counter() - t0

        rng = np.random.RandomState(7)
        query_indices = rng.choice(size, size=min(NUM_TEST_QUERIES, size), replace=False)
        query_embeddings = [embeddings[i] for i in query_indices]

        exact_times, hnsw_times, recalls = [], [], []
        for q_emb in query_embeddings:
            t0 = time.perf_counter()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM lab1_6_exact ORDER BY embedding <=> %s LIMIT %s;",
                    (q_emb, TOP_K),
                )
                exact_ids = set(row[0] for row in cur.fetchall())
            exact_times.append(time.perf_counter() - t0)

            t0 = time.perf_counter()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM lab1_6_hnsw ORDER BY embedding <=> %s LIMIT %s;",
                    (q_emb, TOP_K),
                )
                hnsw_ids = set(row[0] for row in cur.fetchall())
            hnsw_times.append(time.perf_counter() - t0)

            recalls.append(len(exact_ids & hnsw_ids) / TOP_K)

        exact_query_time_ms = sum(exact_times) / len(exact_times) * 1000
        hnsw_query_time_ms = sum(hnsw_times) / len(hnsw_times) * 1000
        avg_recall = sum(recalls) / len(recalls)

        print(f"{size:>8} | {exact_build_time:>9.3f}s | {hnsw_build_time:>9.3f}s | "
              f"{exact_query_time_ms:>12.3f} | {hnsw_query_time_ms:>11.3f} | {avg_recall:>9.3f}")

    conn.close()