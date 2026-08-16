"""
lab1_2_faiss_naive.py
=======================
Version 1 of 2 (FAISS). Pure vector search over the real 82-article
corpus, targeting the confirmed failing pair from the collision
experiment: ERR-5012 (correct) vs. ERR-5013 (wrong, opposite instruction).
"""
 
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from lab1_2_common import get_chunks, generate_answer, print_lab_output
 
if __name__ == "__main__":
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    chunks = get_chunks()
 
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
 
    question = "I'm getting ERR-5012, what should I do?"
    q_emb = embed_model.encode([question], normalize_embeddings=True)
    scores, indices = index.search(np.array(q_emb, dtype="float32"), 2)
    retrieved = [(chunks[i], float(scores[0][j])) for j, i in enumerate(indices[0])]
 
    answer = generate_answer(retrieved[0][0], question)
 
    print_lab_output(chunks, question, retrieved, answer)
    print("\n>>> This pair was confirmed failing in the collision experiment.")
    print(">>> If ERR-5013 outranks ERR-5012 here, the LLM will confidently")
    print(">>> tell the user to do the OPPOSITE of what ERR-5012 actually requires.")
