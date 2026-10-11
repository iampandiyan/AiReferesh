# Prompting Techniques: Quick Review (Module 3 · Lesson 3.2)
**Zero-shot · Few-shot · CoT · ReAct, "climbing the pyramid"**

## The Big Idea
**Pick the lowest rung of the pyramid that solves your task. Don't over-climb.** Each rung costs more (tokens, latency, money) and adds capability.

**The story:** A customer wanted to fine-tune a ticket classifier (about $6,000 + 2 weeks). An FDE added 3-5 few-shot examples instead (about 800 tokens, 30 minutes). Accuracy went from about **71% to 89%**. Fine-tuning kick-off cancelled.

---

## 1. The Pyramid (cheapest to most powerful)

| Rung | What it is | Extra cost | Best for |
|------|------------|-----------|----------|
| **Zero-shot** | Instructions only, no examples | Cheapest | Clear, simple tasks (sentiment, simple intent) |
| **Few-shot** | 2-5 input/output examples in the prompt | ~+800 tokens | Distribution shift (Spanglish, Taglish, new vocabulary) |
| **CoT** (chain-of-thought) | "Think step by step" or `<thinking>` tags | ~+1200 tokens | Multi-step reasoning (math, logic, debugging) |
| **ReAct** | Reason → Act (tool call) → Observe → loop | + tool calls | Tool-using agents |

---

## 2. Zero-shot
- No examples, just instructions.
- Works for well-defined, simple tasks.
- **Fails** when inputs differ from what the model usually sees (distribution shift).

---

## 3. Few-shot (the 30-minute fix)
- Put **3-5 examples** in the `[EXAMPLES]` section of the L3.1 structure.
- Does roughly what thousands of fine-tuning examples do for a distribution-shift problem, with no training time or vendor lock-in.
- **Use when:** task is new, volume is low or medium.
- **Don't use when:** over about **1M calls/month**, where fine-tuning wins on per-call cost.
- **Trade-off:** few-shot = fast iteration; fine-tune = cheaper at huge scale.

**Choosing examples (the "load-bearing 5"):**
- Cover your most **different** cases, one example per category.
- Use the messiest real-world samples (Spanglish, French-English, etc.).
- Don't pick 2 "billing" and 1 "technical". That teaches "billing is the default."
- **Re-check every quarter** as customer language drifts.

---

## 4. Chain-of-Thought (CoT)
- Model writes out reasoning before answering. Use `<thinking>...</thinking>` and then `<decision>...</decision>`.

| Task | CoT effect |
|------|-----------|
| Multi-step math, logic, code debugging | +5-15 points accuracy |
| Multi-hop RAG (3+ docs) | +3-8 points |
| **Simple classification / sentiment** | **Neutral or slightly worse**, extra tokens wasted |
| Tasks the model already "thinks" through internally | Neutral, just costs more |

- **Cost:** about 3-5x latency (example: 0.6s → 2.1s; 12 → 280 output tokens).
- **Two benefits:** reasoning is **auditable** (a debug log) and the customer only sees the clean `<decision>`.
- **Rule:** Only add CoT for multi-step tasks.

---

## 5. ReAct (Reason → Act → Observe)
- A loop: the model thinks, calls a tool, reads the result, repeats until done.
- Needed when the model must **fetch real data** (e.g. look up customer tier, check refund eligibility). CoT only *explains* reasoning; it doesn't fetch data.
- **Always cap iterations at 5** to prevent infinite loops that burn money.
- Log iteration count and alert if the average goes over 3 (a sign of prompt degradation).
- **Note:** In 2026, prefer **native `tool_use`** for new code. Same correctness, about 1/10 the code. ReAct text scaffolding is mostly legacy knowledge.

---

## 6. Self-Consistency (majority voting)
- Sample the answer **k=5 times** at temperature about 0.7, then take the **most common** answer.
- **Cost:** about 5x. **Gain:** about +3-5 points on hard tasks.
- **Use when:** discrete right answer + high-stakes (financial, regulatory).
- **Don't use when:** open-ended generation or simple classification.
- **Decision rule:** `cost of a wrong answer × accuracy gain > 5x extra inference cost`
- **Gotcha:** temperature=0 gives 5 identical answers. You need temperature above 0 (about 0.5-0.9).

---

## 7. PII in Few-Shot Examples
- Never put real SSNs, national IDs, card numbers or phone numbers in examples (GDPR / CCPA / EU AI Act issue). They can leak via logs, caching and snapshot tests.
- **Fix:** Use **synthetic placeholders** + a `strip_pii` validator (Pydantic `AfterValidator`) so real PII can't reach `[EXAMPLES]`.
- **Interview signal:** Name the validator + synthetic data + the regulator (GDPR Art. 5 / 32, CCPA).

---

## 8. Five Production Gotchas
1. **Examples in the wrong section:** Keep them in `[EXAMPLES]`, not `[CONTEXT]`. Mixing them breaks caching.
2. **CoT leaks to the customer:** Wrap in `<thinking>` and only parse `<decision>`. Thinking may mention other customers' data.
3. **ReAct infinite loops:** Always cap at 5.
4. **Self-consistency at temperature 0:** Useless. Use temperature above 0.
5. **Few-shot drift:** Examples from May may not cover customer language in November. Re-evaluate quarterly.

---

## 9. Real-World Cases
- **Code-mixed text** (Spanglish, Taglish, French-English) = distribution shift → few-shot, not fine-tuning.
- **Low-resource sub-segments** that stay below about 90%: route to a **regional model** (Mistral for European languages, Qwen for CJK). Don't fine-tune. Same schema, different endpoint.
- **Compliance:** Expect the DPO to review your `[EXAMPLES]` section. Use `strip_pii`.

---

## 10. Analogy: Onboarding a Junior Engineer
- **Zero-shot** = "Drop them in and hope."
- **Few-shot** = "Pair-program for an afternoon, show 3 examples."
- **CoT** = "Narrate your thinking out loud."
- **ReAct** = "Use the runbook, check after each step, adapt."

**Where it breaks down:** The LLM starts fresh every call (no carried context), it will follow nonsense instructions, and it doesn't "learn on the job." Improvement comes from changing the prompt or upgrading the model.

---

## 11. Quiz Answers (Self-Check)
| Q | Answer | Why |
|---|--------|-----|
| Q1 | **b** | Few-shot beats fine-tuning with low data + distribution shift + fast iteration |
| Q2 | **b** | CoT on simple classification: neutral or slightly worse, 3-5x more tokens |
| Q3 | **a** | Self-consistency: about 5x cost for about +3-5 points on hard tasks |
| Q4 | **b** | ReAct is for tool-using agents chaining calls based on observations |
| Q5 | **c** | Synthetic PII + `AfterValidator(strip_pii)` on prompt assembly |

---

## 12. Quick Memory Hooks
- **Pyramid:** Zero-shot → Few-shot → CoT → ReAct (stop at the lowest rung that works)
- **Few-shot** = fixes *distribution shift* (cheap, fast)
- **CoT** = fixes *multi-step reasoning* (hurts simple classification)
- **ReAct** = needed for *tools*, cap at **5**
- **Self-consistency** = 5x cost, only for high-stakes
- **Temperature above 0** for voting
- **Synthetic PII only** in examples
- **Don't fine-tune before trying few-shot**
