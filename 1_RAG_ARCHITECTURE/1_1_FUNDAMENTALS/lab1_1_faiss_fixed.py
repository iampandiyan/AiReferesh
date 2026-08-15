"""
lab1_1_faiss_fixed.py
=======================
Version 1 of 2 (FAISS). Sentence-aware chunking + FAISS vector search.
Fixes the negation-splitting bug from lab1_1_faiss_naive.py.
"""
 
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from lab1_1_common import DOCUMENT, sentence_aware_chunk, generate_answer, print_lab_output
 
if __name__ == "__main__":
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
 
    chunks = sentence_aware_chunk(DOCUMENT, max_chars=250)
 
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
 
    question = "I just joined last month, can I work from home two days a week?"
    q_emb = embed_model.encode([question], normalize_embeddings=True)
    scores, indices = index.search(np.array(q_emb, dtype="float32"), 1)
    retrieved = [(chunks[i], float(scores[0][j])) for j, i in enumerate(indices[0])]
 
    answer = generate_answer(retrieved[0][0], question)
 
    print_lab_output(chunks, question, retrieved, answer)
