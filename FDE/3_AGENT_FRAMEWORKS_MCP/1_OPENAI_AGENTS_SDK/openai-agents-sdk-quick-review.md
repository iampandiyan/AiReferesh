# Lesson 5.1 · OpenAI Agents SDK — Quick Review

**One-line summary:** The Agents SDK gives you the whole agent loop (describe tools → validate → run → feed result back → trace) in a few lines of Python. It is the simplest production-ready default for a *linear loop with tools*.

---

## Highlights (read this if you read nothing else)

- **3 primitives:** `Agent` (model + instructions + tools), `Runner` (runs the loop), `@function_tool` (any Python function becomes a tool).
- **The loop = ReAct:** Reason → Act → Observe, repeated until the model gives a final answer.
- **`max_turns` is a budget**, not a safety net (default 10). Every turn = one model call.
- **Handoff = sequential delegation** (single Runner, shared context). It is **not** concurrent multi-agent.
- **Tracing is on by default.** Great for debugging, but watch for **PII** leaving to the OpenAI dashboard.
- **Know when to stop:** Linear loop → Agents SDK. Branching/durable state → LangGraph. Concurrent agents → CrewAI / Microsoft Agent Framework. Predictable flow → raw SDK.

---

## 1. Basics

- Released by OpenAI in **March 2025**; production evolution of the experimental **Swarm** prototype.
- Install: `pip install openai-agents` → import as `from agents import ...` (not `openai_agents`).
- Works with any OpenAI-compatible endpoint (Claude, Ollama, etc.) and 100+ models via **LiteLLM**.
- Agent is **stateless by default**: each `Runner.run()` starts fresh unless you add a `Session`.

**Analogy:** Agent = recipe, Runner = kitchen, Tools = appliances. Swap the model (oven) by changing one line.

---

## 2. Agent + Runner + Tools (the 3 primitives)

| Primitive | What it is |
|---|---|
| **Agent** | Model name + system instructions + list of tools |
| **Runner** | Takes an Agent + input and runs the loop until a final answer |
| **Tool** | Python function with `@function_tool`; SDK builds the JSON schema and validates calls via Pydantic |

**What the SDK does for you (invisibly):**
1. Builds the tool-call JSON schema from your function signature.
2. Calls the model → runs your tool → feeds the result back → repeats.
3. Emits a trace to the OpenAI Dashboard.

**Rule:** Use a **tool for anything deterministic** (math, dates, ID lookups). LLMs hallucinate these at small but nonzero rates.

**Real-world anchor:** Klarna's support assistant (~2.3M conversations/month) uses this same single-agent, small-toolset pattern.

### Depth A: RunContext (dependency injection)
- Pass a typed object once with `context=...`; every tool receives it via `RunContextWrapper`.
- **The model never sees it** → right place for `customer_id`, DB handle, secrets.
- Avoids leaking one customer's data into another's request when requests run concurrently.
- Tradeoff: tools need a fake context in unit tests (cheap insurance).

### Depth B: Sessions (memory)
- Pass `session=SQLiteSession("id")` to carry history across turns (chat widget, Slack, phone).
- **SQLite = local demo only.** Use Postgres/Redis in production so state survives restarts and is shared across replicas.

---

## 3. The Loop: Reason / Act / Observe

- Based on **ReAct** (Yao et al., 2023).
- Default cap: **10 turns**. Exceed it → `MaxTurnsExceeded`.
- **Loop economics:** N turns = N model calls. Cost and latency grow linearly. Hitting the ceiling costs ~10× a clean answer.
- Set `max_turns` per agent type: ~6 triage, ~4 FAQ, ~20 code-execution.
- Alert when runs creep toward the ceiling; it means a tool returns ambiguous data and the model is thrashing.

**Running example: AcmeCorp triage agent** (3 tools: `get_customer_tier`, `lookup_order`, `escalate_to_human`).
- First tool call errored → SDK fed the error back as an observation → model **recovered**.
- **Read the FINAL output**, not the intermediate trace, to judge success.
- Cost: ~2,500 input + ~400 output tokens ≈ **$0.0098 (~1 cent per ticket)**.

### 3 production gotchas
1. **Infinite loops** → tune `max_turns`.
2. **PII in traces** → disable tracing per run or redact upstream.
3. **Tool exceptions kill the run** → catch errors in tools and *return an error string* so the model can recover.

### Depth C: `output_type` (structured output)
- Set `output_type=` to a Pydantic model → `final_output` becomes a **validated typed object** (no regex on prose).
- Always keep an **escalate / needs_human** escape hatch so a tight schema doesn't force a bad answer.

### Depth D: Guardrails
- **Input guardrail:** runs *before* the loop; a tripwire aborts the run (blocks prompt injection / off-topic cheaply).
- **Output guardrail:** checks the final result (PII leak, policy break).
- Usually a small cheap-model call; runs alongside the first step to limit latency.
- Raises `InputGuardrailTripwireTriggered` when tripped.

### Depth E: Streaming
- `Runner.run_streamed` + `stream_events()` → show tokens and "checking your order..." live.
- Use for **interactive UIs**; skip for batch/backend jobs.
- **Gotcha:** you must drain the stream to completion to get `final_output` and flush the trace.

---

## 4. Handoffs: sequential delegation

- A handoff transfers **control + conversation context** from one agent to another **within one Runner call**.
- Example: triage agent → billing specialist (with refund tool). Billing owns the rest of the conversation.
- SDK exposes the target as a synthetic tool (e.g. `handoff_billing_agent`).
- Why a distinct primitive: preserves shared context and shows up as **nested spans** in the trace.
- **Anti-pattern:** calling `Runner.run(other_agent)` inside a tool → no shared context, unrelated trace.
- Tradeoff: adds one model call. Fine to skip the split for < 4 tools.
- **Not** concurrent multi-agent (that is Lesson 5.3).

**Analogy:** Hotel front desk routes you to the right specialist; you don't retell your story. Handoffs are one-shot: the original agent doesn't get the conversation back.

### Depth F: `as_tool` vs `handoff`

| Primitive | Control flow | Use when |
|---|---|---|
| `handoffs=[billing]` | Delegate, **don't come back** | Routing / triage; other agent finishes the job |
| `billing.as_tool(...)` | Call sub-agent, **get result, caller keeps control** | Need sub-answers to merge (translator, summarizer) |

Mental model: `as_tool` = function call (composition). `handoff` = transfer (delegation).

---

## 5. Tracing: free production debugging

- Every run auto-emits a trace to **platform.openai.com/traces**: input, every model call, every tool call (args + result), handoffs (nested), final output, timings.
- Turns "agent did something weird in prod" into a ~60-second diagnosis.
- Core SDK is ~3,000 lines → readable cold at a customer site.
- **Cost of tracing:** full prompts/payloads are sent (PII risk).
- **PII fix (layered):**
  - Redact upstream **before** data enters the agent (stripping only inside tools is too late; it's already in the trace).
  - Disable tracing for sensitive runs: `RunConfig(tracing_disabled=True)`.
  - Document it (DPIA; Module 10).

### Depth G: Custom trace processors
- `add_trace_processor(...)` → also send spans to **Langfuse / Arize Phoenix / any OTel backend**.
- `set_trace_processors([...])` → **replace** the default when data must never leave the customer's VPC.
- Feeds Module 6 (evals & observability).

---

## 6. When the Agents SDK is enough

| Engagement shape | Agents SDK? | Use instead |
|---|---|---|
| Linear support triage, 2–8 tools | ✅ Yes (default) | n/a |
| Branching workflow with conditional state | ❌ | LangGraph (5.2) |
| Multi-step research with checkpoints | ❌ | LangGraph |
| Concurrent agents on one task | ❌ | CrewAI / Microsoft Agent Framework (5.3) |
| Predictable, never-branching workflow | ❌ | Raw SDK (5.4) |
| Fully vendor-neutral tooling | Maybe | Any OpenAI-compatible endpoint; MCP (5.5–5.7) |
| Durable execution / resume after restart | ❌ | LangGraph + Postgres checkpointer |
| Human-in-the-loop interrupts | Partial | Cleaner in LangGraph |

**Shorthand:** Linear loop → Agents SDK · Branching state machine → LangGraph · Concurrent collaborators → CrewAI/MAF · Predictable workflow → raw SDK.

**FDE mindset:** Defending "we don't need anything heavier than the Agents SDK" is more valuable than reaching for the fanciest tool. Small, maintainable systems win.

---

## Quick Check: Answers at a glance

1. **Why a tool for `add(a, b)`?** Deterministic operations belong in tools; LLMs hallucinate them at nonzero rates.
2. **`MaxTurnsExceeded` after repeated `search_kb` calls?** Find *why* it loops (ambiguous tool output / vague stop criteria). Fix the tool or prompt; don't just raise `max_turns`.
3. **Two concurrent agents with merged output?** Not a handoff. That's CrewAI / MAF territory (5.3).
4. **PII flowing to the trace dashboard?** Redact upstream + disable tracing for high-sensitivity runs (+ DPIA).
5. **3 ERPs + approve/reject + human resumes hours later?** **LangGraph** (branching + durable checkpoints).

---

## Cheat sheet: code names to remember

| Need | Use |
|---|---|
| Define a tool | `@function_tool` |
| Run (sync / async / stream) | `Runner.run_sync` / `Runner.run` / `Runner.run_streamed` |
| Limit iterations | `max_turns=` |
| Request-scoped state | `context=` + `RunContextWrapper` |
| Multi-turn memory | `Session` (e.g. `SQLiteSession`) |
| Typed final answer | `output_type=` (Pydantic) |
| Safety checks | `input_guardrails=` / output guardrails |
| Delegate permanently | `handoffs=[...]` |
| Call sub-agent and return | `agent.as_tool(...)` |
| Turn off tracing | `RunConfig(tracing_disabled=True)` |
| Custom trace export | `add_trace_processor` / `set_trace_processors` |

---

## Practice exercises (summary)

- **Easy:** Hello agent with a calculator tool; swap to a Claude model via the OpenAI-compatible endpoint / LiteLLM.
- **Medium:** AcmeCorp triage agent (3 tools); add billing handoff with `issue_refund`; streaming or 2-turn memory; framework decision memo.
- **Hard:** Typed output + injection guardrail; PII redaction + tracing-disabled for sensitive runs.
