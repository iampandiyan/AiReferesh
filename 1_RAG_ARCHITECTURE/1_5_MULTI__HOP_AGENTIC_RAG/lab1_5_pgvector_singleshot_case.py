"""
lab1_5_pgvector_singleshot_case.py
=====================================
Version 2 of 2 (pgvector). Same single-case failure demonstration via
PostgreSQL/pgvector instead of FAISS. Same target case (Engineering
North) as lab1_5_singleshot_case.py, so the two are directly comparable.
"""
 
import os
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from lab1_5_common import build_corpus, get_chunks, generate_answer, print_lab_output
 
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
    conn.autocommit = True  # avoids leaving an open transaction that can
                             # deadlock a future run if interrupted mid-script
    register_vector(conn)
 
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("DROP TABLE IF EXISTS lab1_5_singleshot_chunks;")
        cur.execute(f"""
            CREATE TABLE lab1_5_singleshot_chunks (
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
                INSERT INTO lab1_5_singleshot_chunks (team, role, chunk_text, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (m["team"], m["role"], c, emb),  # numpy array directly, not .tolist()
            )
 
    target = next(r for r in records if r["team"] == "Engineering North")
    question = target["query"]
    q_emb = embed_model.encode([question], normalize_embeddings=True)[0]
 
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT chunk_text, 1 - (embedding <=> %s) AS similarity
            FROM lab1_5_singleshot_chunks
            ORDER BY embedding <=> %s
            LIMIT %s;
            """,
            (q_emb, q_emb, 3),
        )
        retrieved = cur.fetchall()
 
    context = "\n".join(c for c, _ in retrieved)
    answer = generate_answer(context, question)
 
    print_lab_output(chunks, question, retrieved, answer)
    print(f"\n>>> Correct answer: {target['limit']} (manager: {target['manager']})")
    print(f">>> Check whether any retrieved chunk actually belongs to {target['manager']}.")
    conn.close()
