"""
lab1_3_pgvector_parentchild.py
=================================
Version 2 of 2 (pgvector). Parent-Child retrieval using two tables:
lab1_3_pc_children (small chunks, embedded, used for matching) and
lab1_3_pc_parents (full section text, looked up by section_id after
the child match). This mirrors LangChain's ParentDocumentRetriever
pattern -- a vectorstore of children plus a docstore of parents.
"""
 
import os
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from lab1_3_common import build_sections, get_child_chunks, generate_answer, print_lab_output
 
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
    sections = build_sections(num_sections=50, seed=42)
    chunks, meta = get_child_chunks(sections)
 
    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = True
    register_vector(conn)
 
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("DROP TABLE IF EXISTS lab1_3_pc_children;")
        cur.execute("DROP TABLE IF EXISTS lab1_3_pc_parents;")
        cur.execute(f"""
            CREATE TABLE lab1_3_pc_children (
                id serial PRIMARY KEY,
                section_id text,
                role text,
                chunk_text text,
                embedding vector({EMBED_DIM})
            );
        """)
        cur.execute("""
            CREATE TABLE lab1_3_pc_parents (
                section_id text PRIMARY KEY,
                parent_text text
            );
        """)
 
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    with conn.cursor() as cur:
        for c, m, emb in zip(chunks, meta, embeddings):
            cur.execute(
                """
                INSERT INTO lab1_3_pc_children (section_id, role, chunk_text, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (m["section_id"], m["role"], c, emb),
            )
        for s in sections:
            cur.execute(
                "INSERT INTO lab1_3_pc_parents (section_id, parent_text) VALUES (%s, %s)",
                (s["id"], s["parent_text"]),
            )
 
    target = next(s for s in sections if s["id"] == "POL-1000")
    question = target["query"]
    q_emb = embed_model.encode([question], normalize_embeddings=True)[0]
 
    with conn.cursor() as cur:
        # Step 1: match at the CHILD level (same precision as naive)
        cur.execute(
            """
            SELECT section_id, chunk_text, 1 - (embedding <=> %s) AS similarity
            FROM lab1_3_pc_children
            ORDER BY embedding <=> %s
            LIMIT 1;
            """,
            (q_emb, q_emb),
        )
        matched_section_id, matched_child_text, score = cur.fetchone()
 
        # Step 2: resolve to the PARENT text before building context
        cur.execute(
            "SELECT parent_text FROM lab1_3_pc_parents WHERE section_id = %s",
            (matched_section_id,),
        )
        parent_text = cur.fetchone()[0]
 
    retrieved = [(parent_text, float(score))]
    answer = generate_answer(parent_text, question)
 
    print_lab_output(chunks, question, retrieved, answer)
    print(f"\n>>> Matched child chunk: {matched_child_text}")
    print(f">>> Resolved to parent section: {matched_section_id}")
    print(">>> Check whether the answer now correctly mentions the exception.")
    conn.close()
