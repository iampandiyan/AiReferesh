"""
lab1_5_pgvector_decomposed_case.py
=====================================
Version 2 of 2 (pgvector). Same single-case fix demonstration via
PostgreSQL/pgvector instead of FAISS. Same target case (Engineering
North) as lab1_5_decomposed_case.py.
"""
 
import os
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from lab1_5_common import build_corpus, get_chunks, extract_manager_name, generate_answer, print_lab_output
 
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
    records = build_corpus(num_teams=50, seed=42)
    chunks, meta = get_chunks(records)
 
    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = True
    register_vector(conn)
 
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("DROP TABLE IF EXISTS lab1_5_decomposed_chunks;")
        cur.execute(f"""
            CREATE TABLE lab1_5_decomposed_chunks (
                id serial PRIMARY KEY,
                team text,
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
                INSERT INTO lab1_5_decomposed_chunks (team, role, chunk_text, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (m["team"], m["role"], c, emb),
            )
 
    def retrieve(query, top_k=1):
        q_emb = embed_model.encode([query], normalize_embeddings=True)[0]
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_text, 1 - (embedding <=> %s) AS similarity
                FROM lab1_5_decomposed_chunks
                ORDER BY embedding <=> %s
                LIMIT %s;
                """,
                (q_emb, q_emb, top_k),
            )
            return cur.fetchall()
 
    target = next(r for r in records if r["team"] == "Engineering North")
    question = target["query"]
 
    # HOP 1: resolve the bridge entity
    hop1_results = retrieve(f"Who manages the {target['team']} team?", top_k=1)
    manager_name = extract_manager_name(hop1_results[0][0])
 
    # HOP 2: retrieve using the RESOLVED name
    hop2_results = retrieve(f"What is {manager_name}'s approval limit?", top_k=1)
 
    retrieved = hop1_results + hop2_results
    context = "\n".join(c for c, _ in retrieved)
    answer = generate_answer(context, question)
 
    print_lab_output(chunks, question, retrieved, answer)
    print(f"\n>>> Hop 1 resolved manager: {manager_name}")
    print(f">>> Hop 2 retrieved that SAME manager's own chunk.")
    print(f">>> Correct answer: {target['limit']} -- check whether the answer matches.")
    conn.close()
