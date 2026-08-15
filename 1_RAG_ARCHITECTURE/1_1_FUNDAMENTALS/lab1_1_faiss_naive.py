"""
lab1_1_faiss_naive.py
=======================
Version 1 of 2 (FAISS). Naive fixed-size chunking + FAISS vector search.
Reproduces the negation-splitting bug.
"""
 
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from lab1_1_common import DOCUMENT, naive_chunk, generate_answer, print_lab_output
 
if __name__ == "__main__":
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
 
    chunks = naive_chunk(DOCUMENT, chunk_size=120)
 
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
 
    # A realistic paraphrase that does NOT use the word "probation" --
    # exactly how a real employee would actually ask this.
    question = "I just joined last month, can I work from home two days a week?"
    q_emb = embed_model.encode([question], normalize_embeddings=True)
    scores, indices = index.search(np.array(q_emb, dtype="float32"), 1)
    retrieved = [(chunks[i], float(scores[0][j])) for j, i in enumerate(indices[0])]
 
    answer = generate_answer(retrieved[0][0], question)
 
    print_lab_output(chunks, question, retrieved, answer)
