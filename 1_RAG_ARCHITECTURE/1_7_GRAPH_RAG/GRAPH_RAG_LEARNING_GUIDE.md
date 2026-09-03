# Graph RAG in Production: Learning Guide

This guide explains the complete `1_7_GRAPH_RAG` module. The code demonstrates graph extraction, Neo4j ingestion, entity resolution, Text-to-Cypher, grounded answer generation, and production failure analysis.

> The Python files are the source of truth for this guide. The accompanying DOCX is present in the folder, but its text could not be extracted by the available workspace reader.

## 1. What Is Graph RAG?

Traditional vector RAG usually follows this flow:

```text
Question
  -> embedding search
  -> similar text chunks
  -> LLM answer
```

Graph RAG follows this flow:

```text
Documents
  -> entity and relationship extraction
  -> graph construction in Neo4j
  -> Cypher retrieval
  -> graph facts
  -> LLM answer
```

A graph represents facts as:

```text
(Entity)-[RELATIONSHIP]->(Entity)
```

For example:

```text
(WorkFromHome)-[REQUIRES]->(ManagerApproval)
(WorkFromHome)-[MAXIMUM_DURATION]->(TwoDaysPerWeek)
(ProbationPeriod)-[EXCLUDES]->(WorkFromHome)
```

Vector search asks:

> Which text is semantically similar to the question?

Graph retrieval asks:

> Which entities are connected, and how are they connected?

Graph RAG is especially useful for relationships, dependencies, organizational structures, compliance rules, multi-hop reasoning, constraints, and provenance.

## 2. Module File Map

| File | Purpose |
|---|---|
| `lab1_7_common.py` | Shared LLM, Neo4j, policy-data, and canonicalization utilities |
| `lab1_7_connectivityTest.py` | Verifies Python-to-Neo4j connectivity |
| `lab1_7_extraction_test.py` | Tests LLM-based entity and relationship extraction |
| `lab1_7_disambiguation_experiment.py` | Measures inconsistent entity IDs across differently worded documents |
| `lab1_7_reproduce_failure.py` | Loads fragmented entities into Neo4j and demonstrates retrieval misses |
| `lab1_7_fix_normalization.py` | Canonicalizes extracted node IDs before ingestion |
| `lab1_7_text2cypher.py` | Converts a natural-language question into Cypher and generates an answer |
| `lab1_7_diagnose_qa_step.py` | Isolates the answer-generation failure using the exact retrieved context |
| `lab1_7_verify_context_hypothesis.py` | Compares incomplete and self-contained context |
| `lab1_7_fix_return_clause.py` | Adds a custom prompt requiring the anchor entity in `RETURN` clauses |
| `lab1_7_determinism_experiment.py` | Tests whether extraction is repeatable at `temperature=0` |

## 3. Shared Infrastructure

[`lab1_7_common.py`](lab1_7_common.py) provides the common building blocks.

### Environment variables

The scripts expect:

- `TOGETHER_STUDY_API_KEY`
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`

Together exposes an OpenAI-compatible API endpoint. Neo4j stores the graph.

### `get_neo4j_driver()`

Creates a Neo4j driver using the configured URI and credentials. A driver manages database communication; sessions execute Cypher statements.

### `generate_answer(context, question)`

Sends a strict grounding prompt to the LLM:

> Answer using only the supplied context. If the answer is absent, say exactly: `Not found in the provided context.`

This reduces hallucination, but it cannot recover information that retrieval did not provide.

### `build_policy_variants()`

Creates eight short documents describing two conceptual entities:

- Work from home
- Probation period

The same ideas use different surface forms:

```text
Work from home
Remote work
Telecommute
WFH
```

and:

```text
Probation period
Trial period
Evaluation window
```

This intentionally creates an entity-resolution problem.

### Canonical entities

```python
CANONICAL_REGISTRY = {
    "work_from_home": "WorkFromHome",
    "probation": "ProbationPeriod",
}
```

The registry defines stable IDs for known entities.

### `canonicalize_node_id()`

This function embeds an extracted node ID, compares it with canonical entity embeddings, and rewrites it when the similarity exceeds a threshold. The embeddings are normalized, so their dot product approximates cosine similarity:

$$
\text{similarity}(a,b) = a \cdot b
$$

This is embedding-based entity resolution.

## 4. Connectivity Test

[`lab1_7_connectivityTest.py`](lab1_7_connectivityTest.py) isolates infrastructure from application logic by executing:

```cypher
RETURN 'connected from Python' AS status
```

A useful debugging practice is to verify connectivity independently before investigating extraction, ingestion, or query behavior.

Interview explanation:

> I first verify the database connection independently. Otherwise, application failures can be confused with connectivity failures.

## 5. Graph Extraction

[`lab1_7_extraction_test.py`](lab1_7_extraction_test.py) uses `LLMGraphTransformer` to convert policy text into nodes and relationships.

The model is configured through Together's OpenAI-compatible endpoint:

```python
ChatOpenAI(
    model="openai/gpt-oss-20b",
    base_url="https://api.together.xyz/v1",
    temperature=0,
)
```

The transformer returns graph documents containing:

```text
nodes
relationships
```

The important lesson is that LLM extraction is probabilistic. Similar concepts may receive different IDs depending on wording, context, model behavior, provider behavior, parsing, or model versions.

## 6. Entity-Resolution Failure

[`lab1_7_disambiguation_experiment.py`](lab1_7_disambiguation_experiment.py) independently extracts each policy variant and collects the extracted node IDs.

The same real-world entity might become:

```text
Work From Home
Remote Work
Wfh_Arrangements
Wfh
```

Neo4j treats these as four different nodes. The database does not automatically know that they are semantically equivalent.

The failure is silent:

1. Extraction succeeds.
2. Insertion succeeds.
3. Cypher executes successfully.
4. The query finds only one surface form.
5. Facts under other surface forms are missed.

This is a graph-recall failure, not necessarily a database failure.

Interview explanation:

> Entity resolution is critical because graph traversal depends on node identity. If equivalent entities receive different IDs, their neighborhoods become fragmented and multi-hop retrieval misses evidence.

## 7. Reproducing the Retrieval Failure

[`lab1_7_reproduce_failure.py`](lab1_7_reproduce_failure.py) loads the extracted graph into Neo4j.

Nodes are inserted with:

```cypher
MERGE (n:Entity {id: $id})
SET n.type = $type, n.source_doc = $doc_id
```

Relationships are inserted with:

```cypher
MATCH (a:Entity {id: $source}),
      (b:Entity {id: $target})
MERGE (a)-[r:RELATED {type: $rel_type}]->(b)
```

The query searches for the literal ID `Work From Home`:

```cypher
MATCH (n:Entity {id: 'Work From Home'})-[r]-(connected)
RETURN n.id, type(r), connected.id
```

It does not retrieve facts stored under `Remote Work`, `Wfh`, or `Wfh_Arrangements`.

### Important Neo4j detail

`MERGE` prevents duplicate nodes with the same exact property value. It does not perform semantic matching.

These are different IDs:

```text
Work From Home
Remote Work
WFH
```

### Lab-only behavior

The script starts with:

```cypher
MATCH (n) DETACH DELETE n
```

This is acceptable for a disposable experiment but dangerous in a shared or production database.

## 8. Normalization Fix

[`lab1_7_fix_normalization.py`](lab1_7_fix_normalization.py) resolves IDs before writing them to Neo4j.

The flow becomes:

```text
LLM extraction
  -> embedding-based canonicalization
  -> relationship endpoint rewriting
  -> Neo4j insertion
```

If extraction produces:

```text
Remote Work -> Manager Approval
```

and `Remote Work` is canonicalized to `WorkFromHome`, the relationship must become:

```text
WorkFromHome -> Manager Approval
```

That is why the script records an `id_rewrites` mapping and applies it to relationship source and target IDs.

### Strengths

- Joins equivalent entities.
- Improves graph connectivity.
- Improves retrieval recall.
- Allows stable Cypher queries.

### Production improvements

A production entity-resolution system should include:

- Per-entity-type matching.
- A larger governed entity registry.
- Aliases rather than discarding original names.
- Confidence bands instead of one universal threshold.
- Human review or quarantine for borderline matches.
- Audit records for every rewrite.
- False-merge tests.
- Versioned resolution rules.
- Collision and duplicate checks.

Embedding similarity is useful for candidate generation, but it can incorrectly merge related yet distinct concepts.

Interview explanation:

> I would combine embeddings with type constraints, aliases, lexical rules, confidence thresholds, and human review for ambiguous matches. Embedding similarity alone is insufficient for high-risk entity resolution.

## 9. Text-to-Cypher

[`lab1_7_text2cypher.py`](lab1_7_text2cypher.py) demonstrates natural-language graph querying using:

```python
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
```

The sequence is:

```text
Natural-language question
  -> LLM receives schema and question
  -> LLM generates Cypher
  -> Neo4j executes Cypher
  -> result rows become context
  -> LLM generates final answer
```

The script calls `graph.refresh_schema()` so the model receives the current graph schema.

### Security concern

The chain uses:

```python
allow_dangerous_requests=True
```

This acknowledges that the LLM is generating executable database queries.

In production, use:

- Read-only database credentials.
- Cypher validation and allowlists.
- Write-operation blocking.
- Procedure restrictions.
- Query timeouts.
- Result-size limits.
- Rate limits.
- Query logging.
- Prompt-injection and schema-injection protection.
- Separate read and write databases.

Interview explanation:

> Text-to-Cypher creates an executable-code boundary. I would validate generated Cypher and execute it with a read-only database identity.

## 10. QA Context Failure

[`lab1_7_diagnose_qa_step.py`](lab1_7_diagnose_qa_step.py) isolates the answer-generation stage.

The retrieved rows contain values such as:

```text
Twodaysperweek
Supervisorsignoff
```

but do not include the anchor entity:

```text
WorkFromHome
```

The question is:

```text
What entities are connected to WorkFromHome?
```

The graph may contain the correct relationship, but the query projection returned insufficient information for the answer model to interpret the rows.

This is a context-construction failure.

### Three separate failure types

#### Retrieval failure

The graph query does not find the required facts.

#### Context-construction failure

The query finds relevant facts but returns incomplete or ambiguous rows.

#### Generation failure

The LLM receives adequate context but produces an unsupported or incorrect answer.

This lab primarily demonstrates context-construction failure.

## 11. Verifying the Context Hypothesis

[`lab1_7_verify_context_hypothesis.py`](lab1_7_verify_context_hypothesis.py) compares two contexts.

### Incomplete context

```text
connected.id = Twodaysperweek
connected.id = Supervisorsignoff
```

The anchor is absent.

### Self-contained context

```text
WorkFromHome is connected to Twodaysperweek.
WorkFromHome is connected to Supervisorsignoff.
```

The facts are equivalent, but the second version explicitly represents the relationship.

The lesson is:

> Retrieved context must be semantically self-contained, not merely technically relevant.

A useful result row should normally preserve:

```text
source entity
relationship type
target entity
provenance
```

## 12. Return-Clause Fix

[`lab1_7_fix_return_clause.py`](lab1_7_fix_return_clause.py) adds a custom Cypher-generation prompt requiring the anchor entity's own ID in every `RETURN` clause.

A complete projection should resemble:

```cypher
RETURN
  n.id AS entity,
  type(r) AS relationship,
  connected.id AS connected_to
```

rather than returning only:

```cypher
RETURN connected.id
```

This makes the context self-contained.

### Prompting is not enforcement

A production system should also:

1. Parse generated Cypher.
2. Validate that the anchor is returned.
3. Validate relationship and provenance fields.
4. Reject or regenerate incomplete queries.
5. Test directional and multi-hop questions.

Interview explanation:

> The custom prompt guides the model, but I would enforce the return contract programmatically before passing results to the QA model.

## 13. Determinism

[`lab1_7_determinism_experiment.py`](lab1_7_determinism_experiment.py) runs identical extraction five times with `temperature=0` and compares the node-ID sets.

Temperature zero reduces sampling randomness, but does not guarantee operational determinism. Differences can still arise from:

- Provider-side batching.
- Hardware-level numerical behavior.
- Reasoning-model behavior.
- Structured-output parsing.
- Model or provider updates.
- API retries and infrastructure.

The scripts use `max_tokens=8192` because reasoning tokens and structured JSON can exceed a smaller output budget.

For reproducible ingestion, persist:

- Original document text.
- Model and provider version.
- Prompt version.
- Extracted graph JSON.
- Extraction errors.
- Entity-resolution decisions.
- Timestamps.
- Reprocessing status.

Interview explanation:

> Temperature zero is not a complete reproducibility strategy. I would version models and prompts, persist raw outputs, validate structured output, and maintain regression datasets.

## 14. Production Data-Model Risks

The scripts are educational examples. Important production concerns include:

### Source-document overwrite

This statement overwrites the previous source:

```cypher
SET n.source_doc = $doc_id
```

If an entity appears in multiple documents, only the last document remains. Production should store source documents as a collection or model provenance as separate nodes or relationships.

### Generic relationship type

Every relationship is stored as `RELATED` with a `type` property. Production may need governed relationship types, confidence, source document, page or section, extraction timestamp, and validity interval.

### Missing constraints and indexes

A production graph should normally define a uniqueness constraint for entity IDs and indexes for common lookups.

### Missing endpoints

Because relationship loading uses `MATCH`, a relationship is skipped if either endpoint was not inserted.

### Direction is ignored

The query:

```cypher
MATCH (n)-[r]-(connected)
```

ignores relationship direction. That is appropriate for “what is connected to X?” but not for directional questions such as “who approved this?” or “who reports to whom?”

### No conflict handling

Real documents may disagree. A production graph needs authority ranking, effective dates, source provenance, conflict detection, and temporal queries.

### No transactional ingestion workflow

The scripts do not demonstrate batching, retries, dead-letter queues, or operational reprocessing.

## 15. End-to-End Architecture

```text
Documents
  |
  v
Chunking and preprocessing
  |
  v
LLM graph extraction
  |
  v
Node and relationship validation
  |
  v
Entity resolution and canonicalization
  |
  v
Neo4j ingestion with provenance
  |
  v
Schema refresh
  |
  v
Natural-language question
  |
  v
Text-to-Cypher generation
  |
  v
Cypher validation
  |
  v
Neo4j execution
  |
  v
Self-contained context construction
  |
  v
Grounded answer generation
  |
  v
Evaluation and observability
```

## 16. Interview Questions and Answers

### What is Graph RAG?

Graph RAG combines a graph database with a language model. Documents are converted into entities and relationships, stored in a graph, and retrieved through graph traversal or Cypher. The retrieved facts are passed to an LLM for grounded answer generation.

### Why use Graph RAG instead of vector RAG?

Vector RAG is strong for semantic similarity. Graph RAG is strong for explicit relationships, multi-hop reasoning, constraints, and provenance. A hybrid system often provides the best overall retrieval behavior.

### What is the main failure demonstrated in this module?

Independent LLM extraction can assign different IDs to the same real-world entity. That fragments the graph and causes silent retrieval misses.

### How would you solve entity fragmentation?

Use canonical registries, aliases, type-aware matching, embeddings, lexical rules, confidence thresholds, audit logs, and human review for ambiguous cases.

### Why might the QA model correctly say “not found”?

Because the returned context omitted the anchor entity. A strict grounding prompt cannot infer a relationship that is not represented in the context.

### Is successful Cypher execution proof that the answer is correct?

No. Cypher may execute successfully while returning incomplete, ambiguous, or semantically misaligned data.

### How would you secure Text-to-Cypher?

Use read-only credentials, validate and allowlist Cypher, block writes and unrestricted procedures, enforce timeouts and result limits, log generated queries, and protect against prompt and schema injection.

### Does `temperature=0` guarantee deterministic extraction?

No. Provider infrastructure, reasoning behavior, parsing, model changes, and hardware can still introduce variation.

### What should be evaluated?

Evaluate each layer separately:

- Entity extraction precision and recall.
- Relationship extraction precision and recall.
- Entity-resolution accuracy.
- Graph connectivity.
- Cypher validity.
- Query execution success.
- Context completeness.
- Multi-hop path accuracy.
- Answer groundedness.
- Final answer accuracy.
- Latency and cost.

## 17. Ten Core Takeaways

1. A graph is only as reliable as its entity identities.
2. `MERGE` provides exact identity matching, not semantic identity matching.
3. Retrieval correctness and answer-generation correctness are separate concerns.
4. Context should include the subject, relationship, target, and provenance.
5. Prompts guide models; critical requirements need programmatic validation.
6. Graph construction must be observable and reproducible.
7. Text-to-Cypher should be treated like generated executable code.
8. Production Graph RAG needs provenance, temporal validity, conflict handling, constraints, retries, and evaluation.
9. A strict grounding prompt should refuse when context is incomplete.
10. Graph RAG is strongest when the question depends on relationships and multi-hop structure.
