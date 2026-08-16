"""
lab1_2_faiss_reranked.py
==========================
Version 1 of 2 (FAISS). Takes the hybrid FAISS shortlist from Part 5's
approach and adds a cross-encoder reranking pass on top.
"""
 
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
from lab1_2_common import get_chunks, tokenize, rrf_fuse, generate_answer, print_lab_output
 
SHORTLIST_N = 10  # the reranker only ever sees a shortlist, never the full 82-chunk corpus
 
if __name__ == "__main__":
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")
    chunks = get_chunks()
    question = "I'm getting ERR-5012, what should I do?"
 
    # --- Hybrid shortlist (same as Part 5) ---
    tokenized_chunks = [tokenize(c) for c in chunks]
    bm25 = BM25Okapi(tokenized_chunks)
    bm25_ranked_ids = list(np.argsort(bm25.get_scores(tokenize(question)))[::-1])
 
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
    q_emb = embed_model.encode([question], normalize_embeddings=True)
    _, indices = index.search(np.array(q_emb, dtype="float32"), len(chunks))
    vector_ranked_ids = list(indices[0])
 
    fused_scores = rrf_fuse([bm25_ranked_ids, vector_ranked_ids], k=60)
    shortlist_ids = [i for i, _ in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:SHORTLIST_N]]
 
    # --- Rerank ONLY the shortlist with a cross-encoder ---
    pairs = [(question, chunks[i]) for i in shortlist_ids]
    rerank_scores = reranker.predict(pairs)
    reranked = sorted(zip(shortlist_ids, rerank_scores), key=lambda x: x[1], reverse=True)[:5]
    retrieved = [(chunks[i], float(score)) for i, score in reranked]
 
    answer = generate_answer(retrieved[0][0], question)
 
    print_lab_output(chunks, question, retrieved, answer)
    print("\n>>> Compare this order against Part 5's RRF order. The reranker")
    print(">>> reads actual text, so check whether it separates ERR-5012 from")
    print(">>> ERR-5013 more decisively than RRF's rank-based fusion did.")
