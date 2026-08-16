"""
lab1_2_faiss_hybrid.py
========================
Version 1 of 2 (FAISS). BM25 (rank_bm25) + FAISS vector search,
fused with Reciprocal Rank Fusion, over the confirmed failing pair.
"""
 
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from lab1_2_common import get_chunks, tokenize, rrf_fuse, generate_answer, print_lab_output
 
TOP_N = 5  # only keep/show the top 5 fused results, not all 82 chunks
 
if __name__ == "__main__":
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    chunks = get_chunks()
    question = "I'm getting ERR-5012, what should I do?"
 
    # --- Lexical side: BM25 ---
    tokenized_chunks = [tokenize(c) for c in chunks]
    bm25 = BM25Okapi(tokenized_chunks)
    bm25_scores = bm25.get_scores(tokenize(question))
    bm25_ranked_ids = list(np.argsort(bm25_scores)[::-1])  # best first
 
    # --- Semantic side: FAISS vector search ---
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
    q_emb = embed_model.encode([question], normalize_embeddings=True)
    _, indices = index.search(np.array(q_emb, dtype="float32"), len(chunks))
    vector_ranked_ids = list(indices[0])
 
    # --- Fuse by RANK, not raw score -- then cap to TOP_N ---
    fused_scores = rrf_fuse([bm25_ranked_ids, vector_ranked_ids], k=60)
    fused_order = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:TOP_N]
    retrieved = [(chunks[i], score) for i, score in fused_order]
 
    answer = generate_answer(retrieved[0][0], question)
 
    print_lab_output(chunks, question, retrieved, answer)
    print("\n>>> RRF scores here are small (around 0.03) because the formula is")
    print(">>> 1/(k+rank) summed across lists with k=60 -- a rank-1 finish only")
    print(">>> contributes ~0.0164 per list. These scores are ONLY meaningful")
    print(">>> relative to each other, never as an absolute confidence percentage")
    print(">>> the way cosine similarity is. Check the RELATIVE order: ERR-5012")
    print(">>> should now outrank ERR-5013, even though pure vector search alone")
    print(">>> (Part 4) ranked it below ERR-5013.")
