"""
lab1_6_ann_scale_experiment.py
================================
Measures REAL latency and recall trade-offs between exact search
(IndexFlatIP, used in every lab so far) and approximate search
(IndexHNSWFlat) as corpus size grows. Run this to find the actual
crossover point where exact search gets slow enough to matter.
"""

import time
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from lab1_6_common import build_scale_corpus

CORPUS_SIZES = [1000, 5000, 15000]
NUM_TEST_QUERIES = 30
TOP_K = 10

if __name__ == "__main__":
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"\n{'Size':>8} | {'ExactBuild':>10} | {'HNSWBuild':>10} | {'ExactQry(ms)':>13} | {'HNSWQry(ms)':>12} | {'Recall@10':>10}")
    print("-" * 80)

    for size in CORPUS_SIZES:
        chunks = build_scale_corpus(num_chunks=size, seed=42)
        embeddings = model.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
        embeddings = np.array(embeddings, dtype="float32")
        dim = embeddings.shape[1]

        # --- Exact search index ---
        t0 = time.perf_counter()
        exact_index = faiss.IndexFlatIP(dim)
        exact_index.add(embeddings)
        exact_build_time = time.perf_counter() - t0

        # --- Approximate search index (HNSW) ---
        t0 = time.perf_counter()
        hnsw_index = faiss.IndexHNSWFlat(dim, 32)  # M=32, standard default
        hnsw_index.hnsw.efConstruction = 40
        hnsw_index.add(embeddings)
        hnsw_build_time = time.perf_counter() - t0

        # --- Pick real queries from the corpus itself ---
        rng = np.random.RandomState(7)
        query_indices = rng.choice(size, size=min(NUM_TEST_QUERIES, size), replace=False)
        query_embeddings = embeddings[query_indices]

        # --- Measure exact search latency ---
        t0 = time.perf_counter()
        exact_scores, exact_ids = exact_index.search(query_embeddings, TOP_K)
        exact_query_time_ms = (time.perf_counter() - t0) / len(query_indices) * 1000

        # --- Measure HNSW search latency ---
        t0 = time.perf_counter()
        hnsw_scores, hnsw_ids = hnsw_index.search(query_embeddings, TOP_K)
        hnsw_query_time_ms = (time.perf_counter() - t0) / len(query_indices) * 1000

        # --- Recall@10: how much HNSW's results overlap with exact's ---
        recalls = []
        for i in range(len(query_indices)):
            exact_set = set(exact_ids[i].tolist())
            hnsw_set = set(hnsw_ids[i].tolist())
            recalls.append(len(exact_set & hnsw_set) / TOP_K)
        avg_recall = sum(recalls) / len(recalls)

        print(f"{size:>8} | {exact_build_time:>9.3f}s | {hnsw_build_time:>9.3f}s | "
              f"{exact_query_time_ms:>12.3f} | {hnsw_query_time_ms:>11.3f} | {avg_recall:>9.3f}")