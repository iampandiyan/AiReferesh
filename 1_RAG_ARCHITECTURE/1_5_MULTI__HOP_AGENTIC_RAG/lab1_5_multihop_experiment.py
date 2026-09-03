"""
lab1_5_multihop_experiment.py
================================
Version 1 of 2 (FAISS). Measures how often single-shot top-k retrieval
actually recovers BOTH facts needed for a bridge-entity multi-hop
question. Prints the full chunk list once, then query/retrieved/answer
for EVERY case.
"""
 
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from lab1_5_common import build_corpus, get_chunks, generate_answer, print_section
 
if __name__ == "__main__":
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
 
    records = build_corpus(num_teams=50, seed=42)
    chunks, meta = get_chunks(records)
 
    print_section("ALL CHUNKS CREATED")
    for i, c in enumerate(chunks):
        print(f"[{i}] {c}")
 
    embeddings = model.encode(chunks, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
 
    bridge_found = 0
    target_found = 0
    both_found = 0
    correct_answer_count = 0
    TOP_K = 3
 
    for idx, r in enumerate(records):
        print(f"\n{'=' * 70}\nTEAM {r['team']} ({idx + 1}/{len(records)})\n{'=' * 70}")
        print_section("QUERY")
        print(r["query"])
 
        q_emb = model.encode([r["query"]], normalize_embeddings=True)
        scores, indices = index.search(np.array(q_emb, dtype="float32"), TOP_K)
        retrieved_meta = [meta[i] for i in indices[0]]
        retrieved_texts = [chunks[i] for i in indices[0]]
        retrieved_scores = [float(s) for s in scores[0]]
 
        print_section("RETRIEVED CHUNK(S)")
        for text, score in zip(retrieved_texts, retrieved_scores):
            print(f"[score={score:.4f}] {text}")
 
        has_bridge = any(m["team"] == r["team"] and m["role"] == "bridge_manager" for m in retrieved_meta)
        has_target = any(m["team"] == r["team"] and m["role"] == "target_limit" for m in retrieved_meta)
        bridge_found += int(has_bridge)
        target_found += int(has_target)
        both_found += int(has_bridge and has_target)
 
        context = "\n".join(retrieved_texts)
        answer = generate_answer(context, r["query"])
        is_correct = str(r["limit"]) in answer
        correct_answer_count += int(is_correct)
 
        print_section("LLM ANSWER")
        print(answer)
        print(f"Verdict: {'CORRECT' if is_correct else 'WRONG'} (expected {r['limit']}, manager: {r['manager']})")
        print(f"Bridge fact retrieved: {has_bridge} | Target fact retrieved: {has_target}")
 
    n = len(records)
    print(f"\n\n{'=' * 70}\nAGGREGATE RESULTS (single-shot top-{TOP_K} retrieval)\n{'=' * 70}")
    print(f"Total multi-hop questions tested: {n}")
    print(f"Bridge fact (team->manager) retrieved: {bridge_found} ({100*bridge_found/n:.1f}%)")
    print(f"Target fact (correct manager's limit) retrieved: {target_found} ({100*target_found/n:.1f}%)")
    print(f"BOTH facts retrieved together: {both_found} ({100*both_found/n:.1f}%)")
    print(f"Final answer contained the CORRECT limit number: {correct_answer_count} ({100*correct_answer_count/n:.1f}%)")
