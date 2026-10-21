# Lesson 5.2 · LangGraph for Stateful, Multi-Step Workflows — Quick Review

**One-line summary:** LangGraph = an explicit graph of **nodes + state + conditional edges + checkpoints**. Use it when a workflow must **branch, pause for a human, resume later, and be replayed/debugged**.

---

## Highlights (read this if you read nothing else)

- **3 primitives:** Node (function of state), Edge (control flow), State (TypedDict with reducers).
- **Every state field needs a reducer decision.** Default = **overwrite**. Lists need `Annotated[list, add_messages]` (append).
- **Routers must be pure and deterministic** (no LLM calls, no I/O). If an LLM must decide, do it in the source node and write the result to state.
- **Checkpointer = git commits for your agent.** Saved after every node, keyed by `thread_id`. Gives **resume** and **time-travel**.
- **`interrupt()` + `Command(resume=...)`** = durable human-in-the-loop. **Needs a checkpointer.**
- **Checkpointer ≠ Store.** Checkpointer = short-term, one thread. Store = long-term, across threads.
- **Framework choice:** Branch/pause/resume → LangGraph. Simple loop → Agents SDK. Role-based concurrent agents → CrewAI.

---

## 0. Why LangGraph? (the AcmeCorp problem)

- Agents SDK (L5.1) handled single-loop support. Then product asked for:
  1. Classify intent → fetch account → propose refund.
  2. If refund **≥ $500**, **pause** for human approval (customer leaves).
  3. **47 hours later** human approves → agent **resumes** exactly where it stopped.
  4. QA wants to **time-travel** back to `classify_intent`, fix the prompt, rerun.
- That is a directed graph with persistent state, conditional routing, and durable pause/resume.

**Analogy:** Airline boarding flow. Nodes = stations, edges = queues, checkpointer = airline database, `interrupt()` = gate agent asking for ID.

**Quick comparison**

| Property | Agents SDK (L5.1) | LangGraph |
|---|---|---|
| Control flow | Implicit loop in Runner | Explicit graph |
| State persistence | In-memory, run-scoped | Checkpointer (InMemory/SQLite/Postgres) |
| Pause for human | Synchronous handoff | `interrupt()` + durable resume |
| Time-travel | Not first-class | `get_state_history` + replay |
| Best for | Single-loop agents | Multi-step, durable workflows |
| Overhead | ~10 lines | ~30 lines |

---

## 1. The three primitives: nodes, edges, state

- **Node:** `(state) -> partial_state_update`. Returns only what changed.
- **Edge:** arrow from one node to another (or `END`).
- **State:** `TypedDict`; each field has a **reducer**.
- Build flow: `StateGraph(State)` → `add_node` → `add_edge(START, ...)` → `compile()` → `invoke()`.
- Benefit over Agents SDK: control flow is an **inspectable artifact** (print it, render it, test it).
- **Don't need LangGraph if:** just one stateless LLM call. **Do need it if:** conditional routing, HITL pause, inspect/time-travel state, or workflow spanning process lifetimes.

**Analogy:** Node = one dbt/Airflow transform; graph = the DAG above it.

---

## 2. State with reducers (where ~60% of bugs live)

- **Reducer** = how a field's old value and a node's update get combined.
- **Default = overwrite.** Fine for scalars. **Wrong for lists.**
- Chat history → `Annotated[list[BaseMessage], add_messages]` (appends + dedups by ID).
- Other lists → `operator.add` or a custom reducer.
- **Nodes return PARTIAL updates**, not the full state. LangGraph reduces them in.
- **Bug example:** `messages: list[BaseMessage]` with no reducer → each turn **replaces** history; by turn 2 you only have the latest reply.

**AcmeCorp state (5 decisions):** `messages` (append), `customer_id`, `customer_tier`, `intent`, `refund_amount_usd`, `approval_status` (overwrite).

**Analogy:** Redux reducers / per-column policy in SQL `MERGE`.

---

## 3. Conditional edges: branch by state

- `add_conditional_edges(source, router_fn, mapping)`.
- **Router = pure function** `state -> next-node-name`.
- AcmeCorp routing: non-refund → `confirm_to_customer`; refund **≥ $500** → `request_human_approval`; else → `auto_execute`.
- **Why deterministic?** LangGraph **replays** routers during time-travel and resume. An LLM router could pick a different branch on replay.
- **If you need an LLM to choose:** do it in the source node, write e.g. `state["next_action"]`, router just reads it.
- **Anti-example (silent dead branch):** `state.get("refund_amount_usd")` returns `None` → router always picks `auto_execute` → a $5,000 refund slips through. **Fix:** `or 0.0` default **and unit-test the boundary** (0, 499.99, 500.00, 500.01, None).
- **Recursion limit:** default **25** steps, raises `GraphRecursionError`. Raise via `config={"recursion_limit": 50}` or fix the termination logic. Prove termination with an eval.

---

## 4. Checkpoints: resumable + replayable

- `graph.compile(checkpointer=...)` saves a snapshot **after every node**, keyed by `thread_id` (conversation) and `checkpoint_id` (step).
- **Resume:** process dies → restart → invoke with same `thread_id` → continues from last checkpoint.
- **Time-travel:** `get_state_history(cfg)` lists checkpoints → pick one (optionally edit state) → `invoke(None, config=target)` → re-runs from there.

**Analogy:** git. `thread_id` = branch, `checkpoint_id` = SHA, `get_state_history` = git log.

**Checkpointer choice (rule-of-thumb, not benchmark)**

| Checkpointer | Scale | Use for | Watch out |
|---|---|---|---|
| `InMemorySaver` | ~10s of threads | Tests, notebooks, demos | Wipes on restart |
| `SqliteSaver` | ~10K threads | Pilots, single-node prod | WAL mode, `check_same_thread=False` |
| `AsyncPostgresSaver` | ~1M threads | Multi-node prod, regulated | Connection-pool tuning (M8) |
| Redis (community) | High write rate, small state | Heavy streaming agents | Small values, ephemeral by default |

- **Never InMemorySaver in production.** Don't jump to Postgres before you need it.

### Checkpointer vs Store

| | Checkpointer | Store (`BaseStore`) |
|---|---|---|
| Scope | One `thread_id` | Across threads/conversations |
| Holds | Full run state per step | Facts, preferences, memories |
| Memory type | **Short-term** | **Long-term** |
| Prod impl | `AsyncPostgresSaver` | `PostgresStore` |

- Resume **this** chat after a crash → checkpointer. Remember something from **last week's** chat → Store.
- Use: `store.search(('acme', customer_id))`, `store.put(('acme', customer_id), 'prefs', {...})`.

---

## 5. Human-in-the-loop with `interrupt()`

- Inside a node: `human_decision = interrupt(payload)` → graph **pauses**, state persisted, payload returned to caller.
- Later: `app.invoke(Command(resume="approved"), config=cfg)` (same `thread_id`) → resumes **inside the same node**; `interrupt()` returns the decision.
- **Requires a checkpointer**; otherwise it raises `NotImplementedError`.
- It is **not** `input()`. `input()` blocks the process, deadlocks under concurrency, and is lost on restart.

**Analogy:** Python `yield` + durable persistence.

**Production gotchas**
- **Timeouts:** sweep job resumes stale threads with `Command(resume="timed_out")`.
- **Approver identity:** authenticate and audit-log the resume (regulatory need).
- **UI:** you build the approver surface (web/Slack/email); LangGraph just hands you the payload.
- **Observability:** `stream_events` emits an interrupt event for your dashboard.

---

## 6. Composing, parallelizing, hardening

### Subgraphs
- `compile()` a graph, then use it as **one node** in a bigger supervisor graph.
- **Shared state key:** `add_node("escalation", escalation_app)`, simplest when schemas overlap.
- **Transform pattern:** wrap subgraph in a node that maps parent state ↔ subgraph state; use when schemas differ or the subgraph has **private fields**.
- Checkpoints compose: a 47-hour HITL pause inside a subgraph still resumes from the top-level `thread_id`.

### Send API (map-reduce / parallel fan-out)
- Conditional edge returns a **list of `Send(node, state_slice)`** → N parallel branches, N known only at runtime.
- Results merge via reducers → use `Annotated[list, operator.add]` so branches **concatenate**, not clobber.
- Example: classify 40 tickets in parallel → 40 results.

### Node retries
- `add_node("retrieve_account", fn, retry=RetryPolicy(max_attempts=3))`.
- If retries are exhausted, the last checkpoint is intact → re-invoke same `thread_id` → resumes **from the failed node**, not the start.
- **Rules:** retry narrow exceptions (e.g. timeouts, not `ValueError`); make nodes **idempotent** (idempotency key so a retry doesn't double-refund); retries ≠ recursion limit (different failures, bound both).

---

## 7. Streaming and observability (light, deep dive in M6.4)

- `stream()` / `astream_events()` for live dashboards.

| `stream_mode` | Emits | Use when |
|---|---|---|
| `values` | Full state after each node | Dashboards, audit trails |
| `updates` | Only the delta per node | Efficient live logs |
| `messages` | LLM tokens as generated | Chat UI typewriter effect |
| `debug` | Every internal event | Debugging the graph / trace view |
| `custom` | Your own via `get_stream_writer()` | Node-computed progress |

- Combine: `stream_mode=["updates", "messages"]`.

---

## 8. Production hosting: LangGraph Platform

- Managed deploy + runtime (formerly LangGraph Cloud): hosts the graph as an API with persistence, task queues, scaled checkpointer, LangSmith tracing.
- Tradeoff: **less ops burden vs. less control** (self-hosted is yours to run).

---

## 9. Which framework, when (3-way rubric)

| Reach for | Workload | Because |
|---|---|---|
| **LangGraph** | Branch, pause, resume, inspect (HITL, durable, time-travel) | Explicit graph + checkpointer + `interrupt()` |
| **OpenAI Agents SDK** | Single-provider loop, tools, a few handoffs, ship fast | Minimal ceremony |
| **CrewAI** | Role-based, concurrent multi-agent teams | Built-in crew + delegation |

**Senior move:** don't be a framework partisan. One stack can use all three (CrewAI for research, Agents SDK for simple support bot, LangGraph for money-touching escalation).

---

## Quiz answers at a glance

1. **Why LangGraph for the 47-hour pause?** Explicit checkpoints + `interrupt()`; state survives restarts and resumes from the exact node.
2. **State field with no reducer?** Default is overwrite → history lost. Fix: `Annotated[list, add_messages]`.
3. **Router calls an LLM, why bad?** Non-deterministic → replay/resume can pick a different branch.
4. **~50K concurrent threads, two regions?** `AsyncPostgresSaver`.
5. **`interrupt()` without a checkpointer?** `NotImplementedError`; compile with at least `SqliteSaver`.

---

## Cheat sheet: names to remember

| Need | Use |
|---|---|
| Define state | `TypedDict` + `Annotated[..., reducer]` |
| Append messages | `add_messages` |
| Concatenate lists (fan-in) | `operator.add` |
| Build graph | `StateGraph`, `add_node`, `add_edge`, `START`, `END` |
| Branching | `add_conditional_edges` (pure router) |
| Persist/resume | `compile(checkpointer=...)` + `thread_id` |
| Time-travel | `get_state_history(cfg)` |
| Pause for human | `interrupt(payload)` |
| Resume | `Command(resume=...)` |
| Parallel fan-out | `Send(node, slice)` |
| Retries | `RetryPolicy(max_attempts=3)` |
| Loop cap | `config={"recursion_limit": N}` |
| Long-term memory | `BaseStore` (`InMemoryStore` / `PostgresStore`) |
| Live events | `stream_mode` / `astream_events` |

---

## Four most common failure modes

1. **Reducer surprise:** list field with no reducer → history clobbered.
2. **In-memory checkpointer in prod:** state lost on every restart/deploy.
3. **Recursion-limit loop:** no termination → `GraphRecursionError`.
4. **Interrupt without checkpointer:** `NotImplementedError`.

---

## Practice exercises (summary)

- **Easy:** 2-node graph with one conditional edge; five-field state with correct reducers + a test proving `messages` appends.
- **Medium:** boundary-test the router (0, 499.99, 500.00, 500.01, None); SQLite resume across a process restart; stream `updates` vs `messages`.
- **Hard:** full AcmeCorp escalation (auto path + paused-then-resumed path); time-travel a bad `classify_intent`; use the Store for returning-customer memory.
