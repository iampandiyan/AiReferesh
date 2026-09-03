"""
lab1_5_pgvector_multihop_experiment.py
=========================================
Version 2 of 2 (pgvector). Same aggregate single-shot experiment via
PostgreSQL/pgvector instead of FAISS.
"""
 
import os
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from lab1_5_common import build_corpus, get_chunks, generate_answer, print_section
 
load_dotenv()
 
PG_CONFIG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": os.environ.get("PG_PORT", "5432"),
    "dbname": os.environ.get("PG_DB", "rag_labs"),
    "user": os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD"),
}
EMBED_DIM = 384
TOP_K = 3
 
if __name__ == "__main__":
    print("Loading embedding model...")
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
        cur.execute("DROP TABLE IF EXISTS lab1_5_experiment_chunks;")
        cur.execute(f"""
            CREATE TABLE lab1_5_experiment_chunks (
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
                INSERT INTO lab1_5_experiment_chunks (team, role, chunk_text, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (m["team"], m["role"], c, emb),
            )
 
    bridge_found = 0
    target_found = 0
    both_found = 0
    correct_answer_count = 0
    n = len(records)
 
    for idx, r in enumerate(records):
        print(f"\n{'=' * 70}\nTEAM {r['team']} ({idx + 1}/{n})\n{'=' * 70}")
        print_section("QUERY")
        print(r["query"])
 
        q_emb = embed_model.encode([r["query"]], normalize_embeddings=True)[0]
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT team, role, chunk_text, 1 - (embedding <=> %s) AS similarity
                FROM lab1_5_experiment_chunks
                ORDER BY embedding <=> %s
                LIMIT %s;
                """,
                (q_emb, q_emb, TOP_K),
            )
            rows = cur.fetchall()
 
        retrieved = [(row[2], row[3]) for row in rows]
 
        print_section("RETRIEVED CHUNK(S)")
        for text, score in retrieved:
            print(f"[score={score:.4f}] {text}")
 
        has_bridge = any(row[0] == r["team"] and row[1] == "bridge_manager" for row in rows)
        has_target = any(row[0] == r["team"] and row[1] == "target_limit" for row in rows)
        bridge_found += int(has_bridge)
        target_found += int(has_target)
        both_found += int(has_bridge and has_target)
 
        context = "\n".join(text for text, _ in retrieved)
        answer = generate_answer(context, r["query"])
        is_correct = str(r["limit"]) in answer
        correct_answer_count += int(is_correct)
 
        print_section("LLM ANSWER")
        print(answer)
        print(f"Verdict: {'CORRECT' if is_correct else 'WRONG'} (expected {r['limit']}, manager: {r['manager']})")
        print(f"Bridge fact retrieved: {has_bridge} | Target fact retrieved: {has_target}")
 
    print(f"\n\n{'=' * 70}\nAGGREGATE RESULTS (pgvector single-shot top-{TOP_K} retrieval)\n{'=' * 70}")
    print(f"Total multi-hop questions tested: {n}")
    print(f"Bridge fact (team->manager) retrieved: {bridge_found} ({100*bridge_found/n:.1f}%)")
    print(f"Target fact (correct manager's limit) retrieved: {target_found} ({100*target_found/n:.1f}%)")
    print(f"BOTH facts retrieved together: {both_found} ({100*both_found/n:.1f}%)")
    print(f"Final answer contained the CORRECT limit number: {correct_answer_count} ({100*correct_answer_count/n:.1f}%)")
    conn.close()
