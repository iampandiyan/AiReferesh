"""
lab1_3_faiss_parentchild.py
==============================
Version 1 of 2 (FAISS). Parent-Child retrieval: still SEARCH using the
small child embeddings (same precision as naive), but RETURN the full
parent section text -- which always contains both the rule and its
qualifier by construction, regardless of which child chunk matched.
"""
 
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from lab1_3_common import build_sections, get_child_chunks, generate_answer, print_lab_output
 
if __name__ == "__main__":
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    sections = build_sections(num_sections=50, seed=42)
    chunks, meta = get_child_chunks(sections)
    parent_lookup = {s["id"]: s["parent_text"] for s in sections}
 
    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
 
    target = next(s for s in sections if s["id"] == "POL-1000")
    question = target["query"]
 
    q_emb = embed_model.encode([question], normalize_embeddings=True)
    scores, indices = index.search(np.array(q_emb, dtype="float32"), 1)
 
    # Same child-level match as naive -- but resolve to the PARENT text
    top_child_meta = meta[indices[0][0]]
    parent_text = parent_lookup[top_child_meta["section_id"]]
    retrieved = [(parent_text, float(scores[0][0]))]
 
    answer = generate_answer(parent_text, question)
 
    print_lab_output(chunks, question, retrieved, answer)
    print(f"\n>>> Same child-level match as the naive version, but the context")
    print(f">>> sent to the LLM is now the FULL parent section, which always")
    print(f">>> contains the qualifier by construction. Check whether the")
    print(f">>> answer now correctly mentions the temporary-role exception.")
