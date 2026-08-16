"""
lab1_3_faiss_naive.py
=======================
Version 1 of 2 (FAISS). Child-only retrieval -- reproduces the confirmed
98% qualifier-loss failure using POL-1000, the first crowded-out example
from the experiment.
"""
 
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from lab1_3_common import build_sections, get_child_chunks, generate_answer, print_lab_output
 
if __name__ == "__main__":
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    sections = build_sections(num_sections=50, seed=42)
    chunks, meta = get_child_chunks(sections)
 
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
 
    target = next(s for s in sections if s["id"] == "POL-1000")
    question = target["query"]
 
    q_emb = embed_model.encode([question], normalize_embeddings=True)
    scores, indices = index.search(np.array(q_emb, dtype="float32"), 2)
    retrieved = [(chunks[i], float(scores[0][j])) for j, i in enumerate(indices[0])]
 
    # Context = ONLY the top-1 retrieved child chunk -- the naive approach
    answer = generate_answer(retrieved[0][0], question)
 
    print_lab_output(chunks, question, retrieved, answer)
    print(f"\n>>> The correct qualifier is: {target['qualifier_text']}")
    print(">>> Check whether the LLM answer above mentions this exception at all.")
