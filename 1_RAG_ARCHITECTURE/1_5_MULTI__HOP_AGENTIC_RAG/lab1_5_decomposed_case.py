"""
lab1_5_decomposed_case.py
============================
Version 1 of 2 (FAISS). Single-case demonstration of the confirmed fix,
using the standard print_lab_output format. Same target case
(Engineering North) as lab1_5_singleshot_case.py.
"""
 
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from lab1_5_common import build_corpus, get_chunks, extract_manager_name, generate_answer, print_lab_output
 
if __name__ == "__main__":
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    records = build_corpus(num_teams=50, seed=42)
    chunks, meta = get_chunks(records)
 
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
 
    def retrieve(query, top_k=1):
        q_emb = embed_model.encode([query], normalize_embeddings=True)
        scores, indices = index.search(np.array(q_emb, dtype="float32"), top_k)
        return [(chunks[i], float(scores[0][j])) for j, i in enumerate(indices[0])]
 
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
