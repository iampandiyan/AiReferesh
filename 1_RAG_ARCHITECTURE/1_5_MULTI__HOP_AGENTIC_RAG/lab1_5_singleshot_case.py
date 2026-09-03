"""
lab1_5_singleshot_case.py
============================
Version 1 of 2 (FAISS). Single-case demonstration of the confirmed
multi-hop failure, using the standard print_lab_output format.
"""
 
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from lab1_5_common import build_corpus, get_chunks, generate_answer, print_lab_output
 
if __name__ == "__main__":
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    records = build_corpus(num_teams=50, seed=42)
    chunks, meta = get_chunks(records)
 
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
 
    target = next(r for r in records if r["team"] == "Engineering North")
    question = target["query"]
 
    q_emb = embed_model.encode([question], normalize_embeddings=True)
    scores, indices = index.search(np.array(q_emb, dtype="float32"), 3)
    retrieved = [(chunks[i], float(scores[0][j])) for j, i in enumerate(indices[0])]
 
    # Single-shot: use ALL top-3 retrieved chunks as context
    context = "\n".join(c for c, _ in retrieved)
    answer = generate_answer(context, question)
 
    print_lab_output(chunks, question, retrieved, answer)
    print(f"\n>>> Correct answer: {target['limit']} (manager: {target['manager']})")
    print(f">>> Check whether any retrieved chunk actually belongs to {target['manager']}.")
