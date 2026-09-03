"""
lab1_5_decomposed_multihop.py
================================
Version 1 of 2 (FAISS). Aggregate validation: runs the SAME decomposed
2-hop strategy from lab1_5_decomposed_case.py across all 50 teams.
Prints the full chunk list once, then query/retrieved/answer for
EVERY case.
"""
 
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from lab1_5_common import build_corpus, get_chunks, extract_manager_name, generate_answer, print_section
 
if __name__ == "__main__":
    model = SentenceTransformer("all-MiniLM-L6-v2")
    records = build_corpus(num_teams=50, seed=42)
    chunks, meta = get_chunks(records)
 
    print_section("ALL CHUNKS CREATED")
    for i, c in enumerate(chunks):
        print(f"[{i}] {c}")
 
    embeddings = model.encode(chunks, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
 
    def retrieve(query, top_k=1):
        q_emb = model.encode([query], normalize_embeddings=True)
        scores, indices = index.search(np.array(q_emb, dtype="float32"), top_k)
        return [(chunks[i], float(scores[0][j])) for j, i in enumerate(indices[0])]
 
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
 
    print(f"\n\n{'=' * 70}\nAGGREGATE RESULT (decomposed 2-hop retrieval)\n{'=' * 70}")
    print(f"Total questions: {n}")
    print(f"Correct final answer: {correct_count} ({100*correct_count/n:.1f}%)")
