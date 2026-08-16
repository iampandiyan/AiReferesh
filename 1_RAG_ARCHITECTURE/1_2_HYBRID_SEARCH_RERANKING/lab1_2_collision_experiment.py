"""
lab1_2_collision_experiment.py
================================
An actual experiment, not a guess: generates many pairs of adjacent
error-code articles, queries each one, and measures how often pure
vector search retrieves the WRONG (opposite-instruction) sibling first.
Run this BEFORE the naive/hybrid/reranked scripts -- its output is what
picks the one real, reproduced failing example the rest of this lab uses.
"""
 
import numpy as np
from sentence_transformers import SentenceTransformer
from lab1_2_common import get_chunks
 
if __name__ == "__main__":
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
 
    articles = get_chunks(num_pairs=40, seed=42)
    # Rebuild the (code_a, code_b, idx_a, idx_b) pairing the same way
    # get_chunks() constructed it, so we know which indices are siblings.
    import random
    random.seed(42)
    used_bases = set()
    pairs = []
    idx = 0
    while len(used_bases) < 40:
        base = random.randint(1000, 9998)
        if base in used_bases:
            continue
        used_bases.add(base)
        pairs.append((base, base + 1, idx, idx + 1))
        idx += 2
 
    print(f"Corpus built: {len(articles)} articles, {len(pairs)} adjacent pairs\n")
    embeddings = model.encode(articles, normalize_embeddings=True)
 
    wrong_top1_count = 0
    wrong_and_opposite_count = 0
    failing_examples = []
 
    for code_a, code_b, idx_a, idx_b in pairs:
        question = f"I'm getting ERR-{code_a}, what should I do?"
        q_emb = model.encode([question], normalize_embeddings=True)[0]
        scores = embeddings @ q_emb  # cosine similarity (embeddings are normalized)
        ranked = np.argsort(scores)[::-1]
        top1_idx = ranked[0]
 
        if top1_idx != idx_a:
            wrong_top1_count += 1
        if top1_idx == idx_b:
            wrong_and_opposite_count += 1
            failing_examples.append({
                "question": question, "correct_code": code_a, "wrong_code": code_b,
                "correct_score": float(scores[idx_a]), "wrong_score": float(scores[idx_b]),
                "correct_article": articles[idx_a], "wrong_article": articles[idx_b],
            })
 
    print("=" * 60)
    print("AGGREGATE RESULTS")
    print("=" * 60)
    print(f"Total pairs tested: {len(pairs)}")
    print(f"Top-1 was WRONG (any article): {wrong_top1_count} "
          f"({100 * wrong_top1_count / len(pairs):.1f}%)")
    print(f"Top-1 was the OPPOSITE-INSTRUCTION sibling (worst case): "
          f"{wrong_and_opposite_count} ({100 * wrong_and_opposite_count / len(pairs):.1f}%)")
 
    if failing_examples:
        print(f"\n{'=' * 60}\nCONCRETE FAILING EXAMPLE(S)\n{'=' * 60}")
        for ex in failing_examples[:3]:
            print(f"\nQuestion: {ex['question']}")
            print(f"Correct article (ERR-{ex['correct_code']}) score: {ex['correct_score']:.4f}")
            print(f"WRONG article (ERR-{ex['wrong_code']}) score: {ex['wrong_score']:.4f}  <-- retrieved as top-1")
