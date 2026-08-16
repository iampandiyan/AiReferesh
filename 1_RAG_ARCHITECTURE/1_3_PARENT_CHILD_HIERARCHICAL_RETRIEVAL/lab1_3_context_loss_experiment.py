"""
lab1_3_context_loss_experiment.py
====================================
Measures, across many policy sections, how often small (sentence-level)
child chunking separates a rule from its qualifying exception -- and
whether even top-2 retrieval reliably keeps the two together, or
whether OTHER sections' similarly-worded chunks crowd the real
qualifier out. Run this BEFORE any naive/parent-child scripts.
"""
 
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from lab1_3_common import build_sections, get_child_chunks
 
if __name__ == "__main__":
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
 
    sections = build_sections(num_sections=50, seed=42)
    chunks, meta = get_child_chunks(sections)
    print(f"Corpus built: {len(sections)} sections, {len(chunks)} child chunks\n")
 
    embeddings = model.encode(chunks, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
 
    top1_missing_qualifier = 0
    top2_missing_own_qualifier = 0
    crowded_out_examples = []
 
    for section in sections:
        q_emb = model.encode([section["query"]], normalize_embeddings=True)
        scores, indices = index.search(np.array(q_emb, dtype="float32"), 2)
        top2_meta = [meta[i] for i in indices[0]]
 
        top1_is_own_qualifier = (
            top2_meta[0]["section_id"] == section["id"]
            and top2_meta[0]["role"] == "qualifier"
        )
        if not top1_is_own_qualifier:
            top1_missing_qualifier += 1
 
        own_qualifier_in_top2 = any(
            m["section_id"] == section["id"] and m["role"] == "qualifier"
            for m in top2_meta
        )
        if not own_qualifier_in_top2:
            top2_missing_own_qualifier += 1
            crowded_out_examples.append({
                "section": section, "top2_meta": top2_meta,
                "top2_scores": [float(s) for s in scores[0]],
            })
 
    n = len(sections)
    print("=" * 60)
    print("AGGREGATE RESULTS")
    print("=" * 60)
    print(f"Total sections tested: {n}")
    print(f"Top-1 retrieval missing the qualifier: {top1_missing_qualifier} "
          f"({100 * top1_missing_qualifier / n:.1f}%)")
    print(f"Top-2 retrieval STILL missing this section's OWN qualifier "
          f"(crowded out): {top2_missing_own_qualifier} "
          f"({100 * top2_missing_own_qualifier / n:.1f}%)")
 
    if crowded_out_examples:
        print(f"\n{'=' * 60}\nCONCRETE CROWDED-OUT EXAMPLE(S)\n{'=' * 60}")
        for ex in crowded_out_examples[:3]:
            s = ex["section"]
            print(f"\nSection: {s['id']} -- Query: {s['query']}")
            print(f"Own rule: {s['rule_text']}")
            print(f"Own qualifier (NOT retrieved): {s['qualifier_text']}")
            print("Top-2 actually retrieved:")
            for m, score in zip(ex["top2_meta"], ex["top2_scores"]):
                print(f"  [score={score:.4f}] section={m['section_id']} role={m['role']}")
