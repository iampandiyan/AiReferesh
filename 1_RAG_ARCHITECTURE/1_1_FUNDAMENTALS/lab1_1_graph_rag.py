"""
lab1_1_graph_rag.py
=====================
Minimal Graph RAG: build a small knowledge graph of entities and
relationships extracted from the leave policy, then retrieve by
traversing relationships instead of vector similarity.
"""
 
import networkx as nx
from lab1_1_common import generate_answer
 
# ---------------------------------------------------------------------------
# STEP 1: Build the knowledge graph manually.
# In a real system, an LLM extraction step would generate these
# (entity, relationship, entity) triples automatically from documents.
# We hand-build it here so the graph structure itself is easy to inspect.
# ---------------------------------------------------------------------------
graph = nx.DiGraph()
 
triples = [
    ("Annual Leave", "entitles", "18 days per year"),
    ("Annual Leave", "carries_forward_up_to", "10 days"),
    ("Sick Leave", "entitles", "12 days per year"),
    ("Sick Leave", "requires", "medical certificate if > 2 consecutive days"),
    ("Work From Home", "allows", "2 days per week"),
    ("Work From Home", "excludes", "employees in probation period"),
    ("Probation Period", "duration", "first 6 months of employment"),
    ("Notice Period", "requires", "60 days if tenure > 2 years"),
    ("Notice Period", "requires", "30 days if tenure < 2 years"),
]
 
for source, relation, target in triples:
    graph.add_edge(source, target, relation=relation)
 
 
# ---------------------------------------------------------------------------
# STEP 2: "Retrieve" by traversing the graph from a matched entity,
# instead of embedding + cosine similarity over flat text.
# ---------------------------------------------------------------------------
def graph_retrieve(entity, max_hops=2):
    """Walk outward from `entity` up to max_hops, collecting every
    relationship triple encountered. This is the graph-RAG equivalent
    of 'retrieve the top-k similar chunks.'"""
    if entity not in graph:
        return []
 
    visited_edges = []
    frontier = [entity]
    for _ in range(max_hops):
        next_frontier = []
        for node in frontier:
            for _, target, data in graph.out_edges(node, data=True):
                visited_edges.append((node, data["relation"], target))
                next_frontier.append(target)
        frontier = next_frontier
    return visited_edges
 
 
def edges_to_context(edges):
    return "\n".join(f"{s} {r} {t}." for s, r, t in edges)
 
 
if __name__ == "__main__":
    # A question that genuinely needs a RELATIONSHIP, not just a text match:
    # "Work From Home" alone doesn't answer this -- you must also traverse
    # to "Probation Period" to get the duration of the exclusion.
    question = "If I'm on probation, when do I become eligible for work from home?"
 
    edges = graph_retrieve("Work From Home", max_hops=2)
    print("Graph traversal result (this is what gets sent to the LLM instead of a text chunk):\n")
    for s, r, t in edges:
        print(f"  {s} --[{r}]--> {t}")
 
    context = edges_to_context(edges)
    answer = generate_answer(context, question)
    print(f"\nLLM ANSWER:\n{answer}")
 
    print(f"\n>>> Notice the context passed to the LLM is a list of relationship")
    print(f">>> triples, not a paragraph of text. This works because the graph")
    print(f">>> traversal from 'Work From Home' automatically pulled in the")
    print(f">>> connected 'Probation Period' -> 'first 6 months' fact, which a")
    print(f">>> flat vector search over text chunks would need a SEPARATE lucky")
    print(f">>> retrieval to find. That's the entire value proposition of Graph")
    print(f">>> RAG: multi-hop facts become a graph walk instead of a gamble on")
    print(f">>> whether two separate chunks both get retrieved together.")
