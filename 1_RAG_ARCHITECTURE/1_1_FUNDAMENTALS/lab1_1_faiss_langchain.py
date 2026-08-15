"""
lab1_1_faiss_langchain.py
============================
Version 1 of 2 (FAISS). Production-style chunking using LangChain's
RecursiveCharacterTextSplitter instead of the hand-rolled sentence_aware_chunk.
"""

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from lab1_1_common import DOCUMENT, generate_answer, print_lab_output

if __name__ == "__main__":
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")

    # Tries paragraph breaks first, then sentence-ish breaks, then words,
    # then raw characters as a last resort -- never fails to produce a
    # valid chunk, unlike a custom regex written for one specific edge case.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=250,
        chunk_overlap=30,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(DOCUMENT)

    embeddings = embed_model.encode(chunks, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))

    question = "I just joined last month, can I work from home two days a week?"
    q_emb = embed_model.encode([question], normalize_embeddings=True)
    scores, indices = index.search(np.array(q_emb, dtype="float32"), 1)
    retrieved = [(chunks[i], float(scores[0][j])) for j, i in enumerate(indices[0])]

    answer = generate_answer(retrieved[0][0], question)

    print_lab_output(chunks, question, retrieved, answer)
