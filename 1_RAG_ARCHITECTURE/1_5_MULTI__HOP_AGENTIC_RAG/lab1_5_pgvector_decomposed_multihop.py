"""
lab1_5_pgvector_decomposed_multihop.py
=========================================
Version 2 of 2 (pgvector). Same aggregate decomposed 2-hop validation
via PostgreSQL/pgvector instead of FAISS.
"""
 
import os
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from lab1_5_common import build_corpus, get_chunks, extract_manager_name, generate_answer, print_section
 
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
 
    print_section("ALL CHUNKS CREATED")
    for i, c in enumerate(chunks):
        print(f"[{i}] {c}")
 
    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = True
    register_vector(conn)
 
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("DROP TABLE IF EXISTS lab1_5_pc_decomposed_chunks;")
        cur.execute(f"""
            CREATE TABLE lab1_5_pc_decomposed_chunks (
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
                INSERT INTO lab1_5_pc_decomposed_chunks (team, role, chunk_text, embedding)
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
                FROM lab1_5_pc_decomposed_chunks
                ORDER BY embedding <=> %s
                LIMIT %s;
                """,
                (q_emb, q_emb, top_k),
            )
            return cur.fetchall()
 
    correct_count = 0
    n = len(records)
 
    for idx, r in enumerate(records):
        print(f"\n{'=' * 70}\nTEAM {r['team']} ({idx + 1}/{n})\n{'=' * 70}")
        print_section("QUERY")
        print(r["query"])
 
        hop1_query = f"Who manages the {r['team']} team?"
        hop1_results = retrieve(hop1_query, top_k=1)
        chunk_a_text, score_a = hop1_results[0]
        manager_name = extract_manager_name(chunk_a_text)
 
        if not manager_name:
            print("Could not resolve manager name -- skipping.")
            continue
 
        hop2_query = f"What is {manager_name}'s approval limit?"
        hop2_results = retrieve(hop2_query, top_k=1)
        chunk_b_text, score_b = hop2_results[0]
 
        print_section("RETRIEVED CHUNK(S)")
        print(f"[HOP 1: {hop1_query}]")
        print(f"  [score={score_a:.4f}] {chunk_a_text}")
        print(f"[HOP 2: {hop2_query}]")
        print(f"  [score={score_b:.4f}] {chunk_b_text}")
 
        combined_context = chunk_a_text + " " + chunk_b_text
        answer = generate_answer(combined_context, r["query"])
        is_correct = str(r["limit"]) in answer
        correct_count += int(is_correct)
 
        print_section("LLM ANSWER")
        print(answer)
        print(f"Verdict: {'CORRECT' if is_correct else 'WRONG'} (expected {r['limit']})")
 
    print(f"\n\n{'=' * 70}\nAGGREGATE RESULT (pgvector decomposed 2-hop retrieval)\n{'=' * 70}")
    print(f"Total questions: {n}")
    print(f"Correct final answer: {correct_count} ({100*correct_count/n:.1f}%)")
    conn.close()
