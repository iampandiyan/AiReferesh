"""
lab1_2_common.py
==================
Fully standalone shared module for Lab 1.2. Nothing here is imported from
Lab 1.1 -- this lab can be handed to someone else as its own folder.
"""
 
import os
import re
import random
from dotenv import load_dotenv
from together import Together
 
load_dotenv()
client = Together(api_key=os.environ.get("TOGETHER_STUDY_API_KEY"))
MODEL = "openai/gpt-oss-20b"
 
TEMPLATE_RESTART = (
    "Article ERR-{code}: Contact the support team using this reference "
    "code for resolution steps. Action required: restart the payment "
    "service, then retry."
)
TEMPLATE_NO_RESTART = (
    "Article ERR-{code}: Contact the support team using this reference "
    "code for resolution steps. Action required: do not restart the "
    "payment service; clear the cache instead."
)
 
 
def get_chunks(num_pairs=40, seed=42):
    """Generates the SAME 82-article corpus every run (fixed seed) --
    40 pairs of adjacent error codes with opposite instructions, plus
    2 distractors. Each article is already an atomic single-fact unit,
    so no text-splitting step is applied here -- see the note in Part 2
    of the document. This corpus is what empirically reproduced a real
    20% opposite-instruction collision rate (see lab1_2_collision_experiment.py)."""
    random.seed(seed)
    articles = []
    used_bases = set()
    while len(used_bases) < num_pairs:
        base = random.randint(1000, 9998)
        if base in used_bases:
            continue
        used_bases.add(base)
        articles.append(TEMPLATE_RESTART.format(code=base))
        articles.append(TEMPLATE_NO_RESTART.format(code=base + 1))
 
    articles.append(
        "Article ERR-3310: Authentication Token Expired. Resolution: "
        "ask the user to log out and log back in. This is a client-side "
        "issue and does not require any server-side restart."
    )
    articles.append(
        "Article NET-0001: General Network Timeout. Check the network "
        "monitoring dashboard before raising a ticket."
    )
    return articles
 
 
def tokenize(text):
    """Keeps codes like 'ERR-5012' intact as a single token instead of
    splitting on the hyphen -- important for BM25 to exact-match codes."""
    return re.findall(r"[a-z0-9\-]+", text.lower())
 
 
def rrf_fuse(ranked_id_lists, k=60):
    """Reciprocal Rank Fusion. Input: a list of ranked lists, where each
    ranked list is a list of item ids in rank order (best first). Output:
    dict of {id: fused_score}, higher is better. Operates purely on RANK
    POSITION, never on raw scores -- this is what makes it safe to combine
    BM25 (unbounded) and cosine similarity ([-1, 1]) without normalizing."""
    scores = {}
    for ranked_ids in ranked_id_lists:
        for rank, item_id in enumerate(ranked_ids, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    return scores
 
def build_or_tsquery1(text):
    """CONFIRMED via direct inspection of to_tsvector() output: Postgres's
    'english' parser tokenizes 'ERR-5012' into 'err' and '-5012' -- the
    leading hyphen stays attached to the numeric part. (Verified with
    SELECT to_tsvector('english', ...) directly in pgAdmin -- see Lab 1.2
    debugging notes.) AND the two real lexemes together; no adjacency,
    no bare-number assumption."""
    code_match = re.search(r"([A-Za-z]+)-(\d+)", text)
    if code_match:
        word_part = code_match.group(1).lower()
        num_part = f"-{code_match.group(2)}"  # keep the hyphen -- that's the real lexeme
        return f"{word_part} & {num_part}"
    words = re.findall(r"[a-zA-Z0-9]+", text)
    return " | ".join(words) if words else text

def build_or_tsquery(text):
    """CONFIRMED via direct inspection of to_tsvector() output in pgAdmin
    (SELECT to_tsvector('english', 'Article ERR-5012: ...')): Postgres's
    'english' parser tokenizes 'ERR-5012' into TWO lexemes -- 'err' and
    '-5012' -- with the leading hyphen still attached to the numeric part.
    Three earlier attempts failed by assuming this differently: (1) OR-ing
    all query words together let the near-universal lexeme 'err' (present
    in all 80 error articles) drown out the one discriminating term; (2)
    a '<->' adjacency requirement matched nothing, because 'err' and the
    number are not stored as strictly adjacent positions the way expected;
    (3) querying for a bare '5012' (no hyphen) also matched nothing, since
    that exact lexeme never existed in the index. The fix: AND 'err' with
    the REAL lexeme '-5012' (hyphen included), verified directly against
    Postgres's actual tokenizer output rather than assumed."""
    code_match = re.search(r"([A-Za-z]+)-(\d+)", text)
    if code_match:
        word_part = code_match.group(1).lower()
        num_part = f"-{code_match.group(2)}"  # keep the hyphen -- that's the real lexeme
        return f"{word_part} & {num_part}"
    words = re.findall(r"[a-zA-Z0-9]+", text)
    return " | ".join(words) if words else text


def generate_answer(context, question):
    prompt = f"""Answer the support question using ONLY the context below.
If the context doesn't fully answer the question, say what it says and nothing more.
 
CONTEXT:
{context}
 
QUESTION: {question}
 
ANSWER:"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content
 
 
def print_section(title):
    print(f"\n{'=' * 40}\n{title}\n{'=' * 40}")
 
 
def print_lab_output(all_chunks, query, retrieved, answer):
    """Standard console output format used across every lab in this series:
    all chunks -> query -> retrieved chunk(s) -> LLM answer."""
    print_section("ALL CHUNKS CREATED")
    for i, c in enumerate(all_chunks):
        print(f"[{i}] {c}")
 
    print_section("QUERY")
    print(query)
 
    print_section("RETRIEVED CHUNK(S)")
    for chunk_text, score in retrieved:
        print(f"[score={score:.4f}] {chunk_text}")
 
    print_section("LLM ANSWER")
    print(answer)
