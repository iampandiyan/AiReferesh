"""
lab1_6_semantic_cache_experiment.py
======================================
Uses GPTCache FOR REAL (pip install gptcache) as the semantic caching
layer in front of our LLM calls -- not a hand-rolled substitute. Note:
GPTCache's own default embedding needs network access this environment
doesn't allow me to test from my side, so this script plugs in our
existing SentenceTransformer model as GPTCache's embedding_func instead.
Run this on your machine (real internet) to get real numbers.

Measures: real cache hit rate on a realistic query stream containing
near-duplicate paraphrases, real time saved vs. calling the LLM every
time, AND an explicit false-positive check -- does the cache ever
return a WRONG cached answer for a query that only LOOKS similar but
needs a different answer?
"""

import time
import numpy as np
from sentence_transformers import SentenceTransformer
from gptcache import Cache
from gptcache.manager import get_data_manager, CacheBase, VectorBase
from gptcache.similarity_evaluation.distance import SearchDistanceEvaluation
from gptcache.processor.pre import get_prompt
from gptcache.adapter.api import put, get
from gptcache.config import Config
from lab1_6_common import build_scale_corpus, generate_answer

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
DIM = 384
SIMILARITY_THRESHOLD = 0.90  # GPTCache's similarity_threshold is on a
                              # 0-1 "confidence" scale after internal
                              # distance normalization, not raw cosine --
                              # start here and tune based on real hits below

if __name__ == "__main__":
    print("Loading embedding model...")
    embed_model = SentenceTransformer(EMBED_MODEL_NAME)

    def embedding_func(data, **kwargs):
        return embed_model.encode(data, normalize_embeddings=True).astype("float32")

    cache = Cache()
    data_manager = get_data_manager(CacheBase("sqlite"), VectorBase("faiss", dimension=DIM))
    cache.init(
        embedding_func=embedding_func,
        data_manager=data_manager,
        similarity_evaluation=SearchDistanceEvaluation(),
        pre_embedding_func=get_prompt,
        config=Config(similarity_threshold=SIMILARITY_THRESHOLD),
    )

    # Small, focused knowledge base so answers are simple and checkable
    knowledge = {
        "billing": "Billing cycles run monthly and invoices are generated on the 1st.",
        "authentication": "Password resets require email verification and expire after 24 hours.",
        "deployment": "Deployments to production require two approvals and a passing test suite.",
    }

    def answer_question(question, topic):
        context = knowledge[topic]
        return generate_answer(context, question)

    # Query stream: base questions, near-duplicate paraphrases (should HIT),
    # and same-topic-but-different-question near-misses (should MISS, and
    # must NOT return the wrong cached answer if they do hit).
    stream = [
        ("billing", "When does the billing cycle start?", "base"),
        ("billing", "When does my billing cycle begin?", "paraphrase"),
        ("billing", "What day of the month are invoices generated?", "paraphrase"),
        ("authentication", "How long is a password reset link valid?", "base"),
        ("authentication", "How long does a password reset link last before expiring?", "paraphrase"),
        ("deployment", "How many approvals are needed to deploy to production?", "base"),
        ("deployment", "How many people need to approve a production deployment?", "paraphrase"),
        ("billing", "Do invoices get generated on the 1st of the month?", "paraphrase"),
        ("authentication", "What happens if I forget my password?", "near_miss"),  # different question, same topic
        ("deployment", "What test suite is required before deployment?", "near_miss"),  # different question, same topic
    ]

    hits = 0
    misses = 0
    total_hit_time = 0.0
    total_miss_time = 0.0

    print_section = lambda t: print(f"\n{'=' * 60}\n{t}\n{'=' * 60}")
    print_section("QUERY STREAM RESULTS")

    for topic, question, kind in stream:
        t0 = time.perf_counter()
        cached = get(question, cache_obj=cache)
        lookup_time = time.perf_counter() - t0

        if cached is not None:
            hits += 1
            total_hit_time += lookup_time
            print(f"\n[{kind.upper()}] Q: {question}")
            print(f"  CACHE HIT ({lookup_time*1000:.1f}ms) -> {cached}")
            if kind == "near_miss":
                print(f"  !!! CHECK: is this cached answer actually correct for THIS question,")
                print(f"  !!! or did the cache incorrectly reuse an answer to a DIFFERENT question?")
        else:
            t0 = time.perf_counter()
            answer = answer_question(question, topic)
            call_time = time.perf_counter() - t0
            misses += 1
            total_miss_time += call_time
            put(question, answer, cache_obj=cache)
            print(f"\n[{kind.upper()}] Q: {question}")
            print(f"  CACHE MISS ({call_time*1000:.1f}ms LLM call) -> {answer}")

    n = len(stream)
    print_section("AGGREGATE RESULTS")
    print(f"Total queries: {n}")
    print(f"Cache hits: {hits} ({100*hits/n:.1f}%)")
    print(f"Cache misses: {misses} ({100*misses/n:.1f}%)")
    print(f"Avg cache hit lookup time: {total_hit_time/hits*1000:.1f}ms" if hits else "No hits")
    print(f"Avg LLM call time (miss): {total_miss_time/misses*1000:.1f}ms" if misses else "No misses")
    if hits and misses:
        speedup = (total_miss_time/misses) / (total_hit_time/hits)
        print(f"Cache hit is ~{speedup:.0f}x faster than an LLM call")