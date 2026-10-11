# Function Calling & Tool Use: Quick Review (Module 3 · Lesson 3.4)
**The tool description IS a prompt**

## The Big Idea
The model reads your tool descriptions on **every call**. They are a hidden prompt-engineering surface, not documentation. Better descriptions beat a bigger model.

**The story:** A 5-tool support agent with one-line descriptions ("refund a payment") hit about **64%** accuracy. It skipped the eligibility check in 19 of 50 cases and refunded already-refunded orders. Rewriting the descriptions took about 90 minutes and lifted accuracy to about **91%**, with no model upgrade.

---

## 1. The 5 Elements of a Good Tool Description

| # | Element | What it says |
|---|---------|--------------|
| 1 | **Purpose** | One sentence: what the tool does at the business level |
| 2 | **Pre-requisites** | Which tools must run first |
| 3 | **Do NOT call if** | Guard rails (**the biggest accuracy lever**) |
| 4 | **Use the result** | What to do with the output (and what not to do, like calling again) |
| 5 | **Side effects** | Money moved? Idempotency needed? Customer-visible change? |

**Bad:** `"Process a refund for an order."`
**Good:** Purpose + "call lookup_order and check_refund_eligibility first" + "do NOT call if already refunded / window expired / ineligible" + "return refund_id + ETA, don't call twice" + "moves real money, always pass `idempotency_key`".

- Writing a precise description takes about 30 seconds and prevents roughly 20-50% accuracy loss.
- **Watch the token cost:** The model re-reads descriptions every call. Keep them dense, not exhaustive. Snapshot tests cover the edge cases.

---

## 2. Single-turn vs Multi-turn

| | Single-turn | Multi-turn (agent loop) |
|---|---|---|
| Flow | Model emits one tool call → you run it → model answers | Model keeps deciding: call another tool, answer, or escalate |
| Use for | Structured output (forced tool call, L3.3) | Triage-style flows (3-5 tool calls per ticket) |
| Cost | Low | More LLM calls = more cost, so **cap iterations** |

**Loop shape:** call model → find the `tool_use` block → run tool → send back `tool_result` → repeat. If no tool call, you have the final answer.

---

## 3. Parallel Tool Calls
- Sonnet 5 and GPT-5.6 support parallel tool use by default.
- **Independent calls** (no shared inputs) go in **one turn**, run concurrently (`asyncio.gather`), return all results in one `tool_result` turn.
- **Gain:** about 2-3x lower latency (example: about 3.6s → 1.4s).
- **Dependent calls** must run sequentially.

**The refund-agent pattern:**
- **Parallel:** `get_customer_tier` + `lookup_order` + `check_refund_eligibility`
- **Then sequential:** `process_refund` or `escalate_to_human` (needs all 3 results)

**Encode dependencies in the descriptions:** "Can be called in parallel with X" and "Call ONLY AFTER A, B, C have returned." The model learns the order from the text. Letting the model guess works about 70% of the time; explicit encoding pushes it to about 98%.

---

## 4. Defending Against Infinite Loops
A confused agent can call the same tool again and again, billing you each time.

**4 defences:**
1. **Hard cap: 5 iterations** (default). Too low (3) cuts off legit work; too high (20) burns budget.
2. **Iteration metric:** OTel attribute `gen_ai.tool.iterations`. Alert when P50 goes above 3.
3. **Same-tool-twice guard:** Same tool + same args twice in a row → force a final answer or escalate.
4. **Per-request cost cap:** Track tokens; abort over budget.

Flag `agent.loop_detected` and `agent.cap_hit` too. All are mandatory for production agents.

**Interview signal:** Name the 5-iteration default + same-tool guard + OTel metric + cost cap. Not "just retry."

---

## 5. Side-Effectful Tools → Idempotency
- Any tool that changes the world (refunds, payments) **must take an `idempotency_key`**, so retries don't double-execute.
- **Derive it deterministically** from inputs: `sha256(order_id + reason + customer_id)`.
- **Never** use `uuid4()`. Every retry gets a new key = double refund (about $1.4K per incident).
- Document the formula in the tool description.

---

## 6. Five Production Gotchas
1. **Shared tool names:** Two services with `lookup_user` cause silent mis-routing. **Namespace them:** `acmecorp_lookup_user`.
2. **Oversized tool results:** A 200KB result gets truncated. Return a **summary + fetch_id** for drill-down.
3. **Side-effect tools inside CoT:** If the model "thinks" then calls `process_refund`, it's a real refund. Add "Inside `<thinking>` do NOT call side-effectful tools," or better, separate the two passes.
4. **Random idempotency keys:** See above. Derive from inputs.
5. **Description token bloat:** 12 tools × 800 tokens = about 10K tokens per call. **Cache the tools block** (L3.5).

---

## 7. Real-World Cases
- **Purpose-of-access parameter:** Add `purpose: Literal["triage_classification", "eligibility_check", "fraud_check"]` to any tool touching PII. Needed for GDPR Art. 5, CCPA, EU AI Act and HIPAA (log every access with a declared purpose). Pair with the `gen_ai.tool.purpose` attribute.
- **5-tool refund agent = the reference design:** 3 parallel lookups → 1 decision → 1 escalation. Generalizes to most SaaS support agents.
- **Regional providers** (Mistral, Qwen, DeepSeek, open models): OpenAI-compatible function calling. Same schema, one URL change. Good for sovereign-cloud workloads.

---

## 8. Analogy: A README for an Internal API
- **Good README:** when to call, what to do with the response, when NOT to call, what errors mean.
- **Bad README:** "POST /refund - process a refund."
- **Where it breaks down:** A human reads a README once. The LLM reads tool descriptions **every call** and pays for them in tokens.

---

## 9. Quiz Answers (Self-Check)
| Q | Answer | Why |
|---|--------|-----|
| Q1 | **c** | Hidden prompt-engineering surface, read on every call |
| Q2 | **b** | Multiple tool calls in one turn when calls are independent (parallel on by default) |
| Q3 | **b** | `idempotency_key`, so retries don't double-process |
| Q4 | **b** | About 5 (configurable) |
| Q5 | **b** | Independent tools → parallel in one response, 2-3x faster |

---

## 10. Quick Memory Hooks
- **Description = prompt** (read every call)
- **5 elements:** Purpose, Pre-reqs, Do-NOT-call, Use-result, Side-effects ("P-P-D-U-S")
- **Do NOT call if** = biggest lever
- **Independent → parallel. Dependent → sequential** (and say so in the description)
- **Cap at 5**, alert if average iterations > 3
- **Idempotency key = hash of inputs, never uuid4**
- **Namespace tool names, summarize big results, cache the tools block**
