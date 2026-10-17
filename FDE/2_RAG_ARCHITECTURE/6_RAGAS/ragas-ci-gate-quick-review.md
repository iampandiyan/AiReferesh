# Module 4 · Lesson 4.6 — Ragas Evaluation as a CI Gate (Quick Review)

> **One-line idea:** You can't fix what you can't measure. Run Ragas on an SME-authored golden set on every pull request, and **fail the build** when quality drops below the line.

---

## 1. The AcmeCorp "Prove It" Story (Why This Matters)

- **Situation:** Eng team's RAG "feels good" (20 internal queries looked right). Customer VP asks: **"How do you know?"**
- **Day 1 Ragas results (50-question SME golden set):**

| Metric | Day 1 | Day 90 |
|---|---|---|
| **Faithfulness** | 0.62 | **0.91** |
| **Context precision** | 0.71 | **0.86** |
| **Answer relevancy** | 0.83 | 0.92 |
| **Context recall** | 0.78 | 0.89 |

- The team thought they were at ~90% because **answer relevancy** looked fine. It's the metric that lies.
- **What changed over 3 months:** per-content-type chunking (L4.2), hybrid + Cohere rerank (L4.3), embedding swap to Cohere embed-v4.0 (L4.1), prompt restructuring with citations (L3.1), all driven by the L4.5 8-FM diagnostic.
- Same docs, same Claude model. The only difference: **what was measurable**.
- This is an **industry-default pattern** (Klarna, Anthropic cookbook, DeepEval, Vercel AI evals), not just Ragas.

---

## 2. What You Should Be Able To Do

- Define the 4 Ragas metrics and which layer each measures.
- Build a 50-question golden set with customer SMEs (labeling protocol, agreement check, refresh cadence).
- Wire Ragas as a **pytest fixture** and gate CI (faithfulness < 0.85, precision < 0.80 → fail).
- Produce a 1-page customer scorecard for procurement renewal.

---

## 3. Key Numbers

| Number | Meaning |
|---|---|
| **0.62 → 0.91** | AcmeCorp faithfulness, day 1 → day 90 |
| **≥ 0.85 / ≥ 0.80** | CI gate: faithfulness / context precision |
| **~80%+** | Strong LLM judge agreement with humans (≈ human-human) |
| **~$1.75–3.50** | Full nightly eval, 50 Qs × 4 metrics, Sonnet 5 judge |
| **~$0.05–0.15** | Same run on a Haiku judge |
| **50 questions** | Golden set minimum (grow to 100–200 by month 3) |

---

## 4. The 4 Ragas Metrics

| Metric | Question it answers | Layer | Needs gold answer? | Target |
|---|---|---|---|---|
| **Faithfulness** | Does each claim follow from the retrieved context? (hallucination detector) | Generator | No | ≥ 0.85 |
| **Answer relevancy** | Does the answer address the question? | Generator | No | ≥ 0.85 |
| **Context precision** | Are relevant chunks ranked near the top? | Retriever | Depends on variant | ≥ 0.80 |
| **Context recall** | Do retrieved chunks cover the gold answer? (missing-evidence detector) | Retriever | **Yes** | ≥ 0.80 |

### How each works
- **Faithfulness:** decomposes the answer into atomic claims, runs NLI against context. Score = supported claims / total claims.
- **Answer relevancy:** generates ~3 synthetic questions the answer would answer, embeds them, takes mean cosine similarity to the original question.
- **Context precision:** rank-weighted (relevant chunk at rank 1 beats rank 8). Variants: WithReference vs WithoutReference.
- **Context recall:** decomposes the gold answer into claims; fraction supported by retrieved context (5 claims, 4 supported → 0.8). **Most under-measured metric.**

### Origin note
- The RAGAS paper (Es 2023) introduced **faithfulness, answer relevance, context relevance**. Context precision and recall are **later library additions**. Cite the paper for the idea, the docs for the implementation.

### Relevancy is the metric that lies
- Reference-free and **blind to factual correctness**. A confidently hallucinated answer aimed at the question scores high.
- **High relevancy + low faithfulness = the model is making things up confidently.** Always measure both.

### When to use which
- **Faithfulness:** when a hallucinated claim is costly (legal, medical, financial, regulated). Don't ship below 0.85; harden to **0.95** for regulated tiers.
- **Answer relevancy:** smoke test only, never alone.
- **Context precision:** when noisy retrieval drives hallucination (FM2/FM3).
- **Context recall:** when answers are plausible but miss the right citation (FM5/FM7).
- **Skip Ragas:** tiny POC (<10 queries) or pure chat with no RAG. **Bring it in** the moment a customer asks "how do you know?"

---

## 5. Two Anti-Examples

### Vanity thresholds
- Gate at faithfulness > 0.50 and precision > 0.40 "to avoid blocking PRs." A chunker bug drops faithfulness 0.88 → 0.61, still green. Customer escalates 7 wrong-policy answers 3 weeks later.
- **Fix:** set the gate at the current scorecard floor minus a small buffer (current 0.91 → gate 0.88).
- **A gate that never fires is theatre, not engineering.**

### The 0.95 faithfulness that ships a hallucination
- Question about clause 3.2; retriever returns clause 4.1; generator paraphrases 4.1 cleanly.
- **Faithfulness 0.95** (faithful to the wrong chunk), **context precision 0.12**, **context recall 0.0**.
- Faithfulness alone says "ship"; the 4-metric view says "FM7 root cause, fix the retriever."
- **Never average the 4 metrics** into one number. Per-metric thresholds show which stage broke.

---

## 6. The Eval-Tool Landscape

**TruLens RAG Triad:** Context Relevance, Groundedness, Answer Relevance. Maps to Ragas precision / faithfulness / relevancy. **The triad has no recall analog**, which is why recall is the most under-measured leg.

| Tool | Wins when |
|---|---|
| **Ragas** | RAG-specific 4-metric CI gate, fast |
| **DeepEval** | Pytest-native; adds G-Eval + hallucination metric (M6.3) |
| **TruLens** | RAG-triad framing + app-level tracing |
| **Braintrust** | Experiment tracking across prompt/retriever iterations |
| **Langfuse** | Trace-linked, self-hostable eval beside prod traces |
| **OpenAI Evals** | OpenAI-centric stack |
| **promptfoo** | YAML red-team / prompt-matrix CI tests |

---

## 7. Building the Golden Dataset

**The SME owns the gold; the FDE owns the harness.**

### Each row has
- **Question** as a real user would phrase it (mixed register, multilingual after expansion).
- **Expected answer** written by the SME (CS lead for deflection, trust & safety for policy, legal for compliance; DPO/GRC for regulated).
- **Expected source docs** (used for context recall).
- **Metadata:** type (citation / paraphrase / multi-hop), SME, language.

Stored as `golden.jsonl`: `question`, `ground_truth`, `reference_contexts`, `metadata`.

### Why the SME, not the FDE
- The FDE doesn't know what customers will ask in 6 months. FDE-authored sets cover only the queries the FDE thought were hard.

### Growth path
| Size | When |
|---|---|
| **50** | Day-1 floor (smaller = smoke test, not eval) |
| **100–200** | Month 3, after first quarterly refresh |
| **200+** | Post-production, stratified per segment (consumer/enterprise, multilingual, regulated) |

A static golden set ages. It's a maintenance artifact, not a one-time deliverable.

### Anti-example: auto-generated golden set
- LLM generates 200 questions → faithfulness 0.94, but prod hallucinates on ~30% of queries.
- Real users ask "I cancelled but got charged, wtf?", not "What does clause 3.2 say…?"
- **Use LLM-generated questions only as a scaffold for SMEs.**

### Reference-free vs reference-required (online / offline hinge)

| Reference-FREE (online-capable) | Reference-REQUIRED (offline only) |
|---|---|
| faithfulness, answer_relevancy, context precision (without reference) | context_recall, context precision (with reference), answer_correctness |
| Score sampled **prod traffic** live (guardrail / drift monitor) | Need SME gold; run on the **golden set** only |

- You can watch faithfulness on every prod request, but **not recall** (no reference at inference time).
- **Loop:** prod trace → sample → reference-free online score → triage with L4.5's 8-FM → hard failures become SME-labeled golden questions → back into the CI gate.

---

## 8. Ragas + pytest CI Gate

### How it's wired (Ragas 0.4.x)
1. Load `golden.jsonl`; run your RAG on each question.
2. Build `SingleTurnSample(user_input, response, retrieved_contexts, reference)` per row → `EvaluationDataset`.
3. `evaluate()` with `Faithfulness`, `ResponseRelevancy`, `LLMContextPrecisionWithReference`, `LLMContextRecall`; pass the judge LLM (**pinned** Claude Sonnet 5, temperature 0) and an embedder (needed for relevancy).
4. `to_pandas()` → assert each metric **mean ≥ threshold**, per metric.
5. GitHub Actions runs `pytest tests/test_ragas_gate.py` on every `pull_request`, with API keys from secrets.

### Thresholds (module deliverable)
`faithfulness 0.85 · context_precision 0.80 · answer_relevancy 0.85 · context_recall 0.80`

### The flaky gate: judge noise
LLM judges drift a few points run-to-run, even at temperature 0. A naive point-estimate gate fails green PRs and passes red ones.
1. **Quantify noise:** run the full eval ~5 times, compute per-metric std. **Std > ~0.04 = noise-dominated.**
2. **Self-consistency:** score each question k=3–5 times and average (variance falls ~1/k; costs k× more).
3. **One-sided bound:** fail only when `mean + margin < threshold`.
4. **Paired delta (the move most gates omit):** same questions, same seed on `main` and candidate; judge noise is correlated, so it cancels. **Fail if `candidate − baseline < −epsilon`** (e.g. 0.03).
5. **Sizing:** n=20 is fine for a paired-delta gate; an absolute-threshold gate needs 50+.

### LLM-as-judge: why trust it
- Strong judge agrees with humans **~80%+**, about the rate two humans agree (Zheng 2023, MT-Bench).
- **Biases:** position, verbosity, **self-enhancement** (a judge favours its own style).
- **G-Eval (Liu 2023):** chain-of-thought + form-filling + probability-weighted scoring (what DeepEval implements).
- **For Ragas specifically:** metrics are pointwise claim-level NLI, so **less** exposed to position/verbosity bias, **more** exposed to self-enhancement and **claim-decomposition instability**.

### CI gate vs nightly vs human review

| Layer | Scope | Cost | Use |
|---|---|---|---|
| **CI gate** | ~20-q dev subset, per commit | ~$0.02–0.06 (Haiku) | Fast PR feedback |
| **Nightly batch** | Full 50–200 q | ~$1.75–3.50 (Sonnet 5) | Customer scorecard inputs |
| **Pre-prod human review** | Bottom-decile failures | Human time | Required for regulated workloads |

- **Never skip the CI gate** on a customer-facing RAG (skip only for internal prototypes).

---

## 9. The Customer-Facing Scorecard

**1 page, 4 metrics, 3-month trend, next-quarter targets.** This is the document the CIO reads at procurement renewal; compliance and DPO sign off.

| Metric | Q1 | Q2 | Q3 | Target Q4 | Status |
|---|---|---|---|---|---|
| Faithfulness | 0.62 | 0.78 | 0.91 | ≥ 0.92 | On track |
| Answer relevancy | 0.83 | 0.88 | 0.92 | ≥ 0.90 | Exceeded |
| Context precision | 0.71 | 0.81 | 0.86 | ≥ 0.85 | Exceeded |
| Context recall | 0.78 | 0.84 | 0.89 | ≥ 0.88 | Exceeded |

- `scorecard.json` fields: build, as_of, judge, golden_set_size, per-metric quarterly values + target + status, ci_gate state, next_review.
- **Per-metric, never averaged.** If the customer wants one number, give **`min(faithfulness, context_precision)`**, the bottleneck-aware floor.
- **Scorecard vs dashboard:**
  - *Scorecard (quarterly, customer):* 4 metrics + thresholds + trend + targets.
  - *Internal dashboard (daily, Langfuse/Braintrust):* per-question scores, judge-vs-human agreement, judge cost, p95 latency, drift, per-segment.
  - Share the dashboard when the customer has an engineering team or regulated audits need evidence trails.

### Anti-example: the scorecard that hides regressions
- "Average 0.87" → faithfulness silently fell 0.91 → 0.74 while recall rose 0.78 → 0.95. Average unchanged; bad answers ship.

---

## 10. What Ragas Does NOT Catch

| Gap | Add alongside |
|---|---|
| Hard multi-hop reasoning (faithful but wrong conclusion) | Hand-curated reasoning eval |
| Customer business rules ("never recommend above risk profile") | Business-rule snapshot suite (mandatory for finance, health-tech, legal-tech) |
| Injection attacks | L3.7 prompt-injection red-team |
| Latency + cost regressions | OTel metrics |
| Drift on out-of-distribution queries | Sample real queries quarterly into the golden set |
| Interpretation/reasoning grading | DeepEval G-Eval / hallucination metrics (M6.3) |

**Ragas is necessary but not sufficient.**

---

## 11. Calibrate the Judge to the SME

A round 0.85 is a **starting guess**, not a calibrated gate.
1. Two SMEs hand-label ~50 golden rows **supported / unsupported**.
2. Run Ragas on those rows; compute **Cohen's kappa** (target > ~0.6, ideally > ~0.8), correlation vs. human pass-rate, and a confusion matrix at the candidate threshold.
3. Pick the cutoff whose precision/recall matches the bar the SME accepts. **Gate on the calibrated cutoff.**
4. **Ceiling:** inter-SME agreement is the upper bound on judge quality.

---

## 12. Faithfulness Failure Modes + Test the Retriever in Isolation

### Faithfulness fails in specific ways
- **Extractive bias:** rewards verbatim quoting; can penalise a correct paraphrase.
- **Claim-decomposition instability:** judge splits the same answer into different claim counts run to run (score noise).
- **Faithful-to-wrong-context:** perfectly faithful to a wrong chunk.
- **Blind to omission:** scores what the answer says, not what it should have said.

### Component before end-to-end
- `context_precision` and `context_recall` need only **query + retrieved chunks + reference**, no generator call.
- Debug the retriever cheaply and deterministically **first**, then measure the generator.

---

## 13. Analogy

Ragas = a **quality audit** for your RAG.
- **Faithfulness:** did the agent respect the actual policy?
- **Answer relevancy:** did it answer the customer's real question?
- **Context precision:** did it look at the right help articles?
- **Context recall:** did it miss any key articles?

**Limit of the analogy:** a financial audit checks past behaviour against fixed rules. Ragas checks current behaviour against a golden set **you authored**, which drifts (SMEs change roles, policies update, regulations like GDPR amendments and the EU AI Act age the set fast). **Refresh every 90 days.** Regulated customers audit monthly.

---

## 14. Production Gotchas

1. **Judge cost is non-trivial.** Library default is an OpenAI model; this lesson **pins `claude-sonnet-5`**. Sonnet 5 ≈ $0.035–0.07/question vs Haiku ≈ $0.001–0.003. (Claude 5 tokenizer emits ~30% more tokens, partly offsetting the price cut.)
   - **Levers:** **cache** by `hash(question+answer+contexts)` (a chunker-only PR reuses ~70% of scores); **batch/concurrency**; **per-metric selectivity** (faithfulness + precision in PR gate, recall nightly).
   - **Rule:** Haiku judge for PR-CI, Sonnet 5 for nightly + customer scorecard.
2. **Threshold churn:** 0.85 is the day-1 floor. **Ratchet up on a cadence, never down.** Document history in `eval/thresholds.md`.
3. **Judge bias / self-preference:** a Claude judge on a Claude-generated RAG is the self-enhancement case. Keep Sonnet 5 as primary but **cross-check a sample with a different-family judge (GPT-5.6 / Gemini)** during calibration. Track inter-judge agreement. Calibrate on **n=50–100 human labels** (Shankar 2024); recalibrate after any judge snapshot bump.
4. **Golden-set drift:** refresh quarterly; revalidate with SMEs (policy and regulatory changes).
5. **Don't ship without context recall:** otherwise you miss plausible-but-wrong answers from missing evidence.
6. **Pin the judge version:** Ragas scores shift on a Sonnet version bump even if your RAG is unchanged. Pin `model="claude-sonnet-5"`; recalibrate before unpinning.

---

## 15. AcmeCorp Procurement-Renewal Context

- **Co-authors:** CS lead + Head of Trust & Safety + Legal counsel; weekly for 90 days, then quarterly. Without their authorship, **the eval is theatre.**
- **Citation requirement:** faithfulness won't enforce verbatim clause citations. Add a **separate snapshot test** that greps for `clause X.Y` / `section X.Y` in every answer.
- **Multilingual golden set:** after the Mexico / Madrid / Singapore expansion, English-only on a ~30% multilingual audience = measuring ~70% of traffic.
- **Procurement gate:** CIO expects **faithfulness > 0.90** before enterprise-tier rollout. First-90-day target: climb from baseline to > 0.90.
- **Regulated customers (EU bank/GDPR, US health-tech/HIPAA, SOX):** gate hardens (often **faithfulness > 0.95**), audit cadence goes quarterly → **monthly**.

---

## 16. Interview Q&A (M4 Close-Out)

| Question | Strong answer |
|---|---|
| **"RAG 'feels good' but a customer says it's wrong. How do you evaluate?"** | Ragas faithfulness + context precision + context recall on a 50+ SME golden set, pytest gate, quarterly refresh; use the L4.5 8-FM diagnostic to categorize drops |
| **"Faithfulness is 0.91 but a customer reported a hallucinated citation."** | 0.91 is an average; the customer hit a tail case. (a) Add the question to the golden set and re-evaluate; (b) tighten citation validation (every cited doc-id in the retrieved set, per FM7). For regulated: verify cited content supports the claim (M6.3 DeepEval) |
| **"Ragas vs DeepEval vs Braintrust vs LangSmith?"** | Ragas = M4 default for RAG metrics + CI gate. DeepEval = pytest-native with G-Eval/hallucination. Braintrust = experiment tracking. LangSmith = LangGraph observability. Pick by the customer's existing stack |

---

## 17. Bridge to Module 6

| Lesson | What returns |
|---|---|
| **M6.1** | Golden-dataset construction with SMEs, in depth |
| **M6.2** | Ragas metric internals + custom domain metrics + judge calibration |
| **M6.3** | Port the CI gate to DeepEval (pytest-native) |
| **M6.5** | Self-hosted Langfuse + Ragas |
| **M6.7** | 5-axis scorecard: Ragas vs DeepEval vs Braintrust vs LangSmith vs hand-rolled |
| **M11 capstone** | Same CI gate required on every PR |

Named systems: Klarna eval CI (the ~47% figure is resolution/CSAT, **not** hallucination reduction), Anthropic eval cookbook, Vercel AI evals, TruLens, Hamel Husain eval-CI, Confident AI / DeepEval, Langfuse + Ragas.

---

## 18. Spaced-Retrieval Check (Modules 2–4)

| Q | Short answer |
|---|---|
| **M2:** Why a Pydantic model at every boundary where an LLM reply enters code? | LLM output is untrusted text. Pydantic turns it into a validated contract and fails loudly on a bad shape (wrong enum, string-for-int), so you can re-prompt instead of corrupting downstream. Discriminated unions kill "wrong shape" |
| **M3:** Junior edits tone rule, breaks the language-compliance rule. What prevents it? | Structure prompts into **named sections** (system, role, context, instructions, examples, format) so each rule has one home and changes stay local; the snapshot suite catches drift |
| **M3:** Why isn't a single input filter enough against prompt injection? | Any single filter can be bypassed. **Layer defenses:** spotlight/delimit untrusted content, instruction hierarchy, output allow-list/validation, sandbox side-effectful tools. Attackers must beat all layers |
| **M4:** Dev strong, Spanish + code-mixed queries fail in prod. Which FM? | **FM8 language mismatch.** English-only embedder misplaces non-English queries. Fix: multilingual embedder. It's a retrieval failure, not generation |
| **M4:** Prod accuracy dropped. What before rollback? | Run the failure-mode diagnostic on failing prod queries. The model rarely regressed; prod exposes modes the dev set missed (stale conflicts, non-English). Diagnosis tells you if the fix is retrieval, generation, or data |

---

## 19. Quick-Fire Quiz Answers

| Q | Answer |
|---|---|
| Q1: Ragas faithfulness measures | **c)** Whether the answer follows from the retrieved context (1.0 = perfect grounding) |
| Q2: Precision vs recall | **b)** Precision: of retrieved docs, how many are relevant. Recall: of relevant docs, how many were retrieved. Both target > 0.80 |
| Q3: Best golden-set author | **b)** Customer SMEs own gold answers + sources; FDE owns the harness |
| Q4: CI gate thresholds | **a)** Faithfulness > 0.85 + context precision > 0.80; fail CI if either drops |
| Q5: Ragas judge cost | **b)** Depends on judge: ~$0.001–0.003/q on Haiku vs ~$0.035–0.07/q on Sonnet 5; budget like CI infra |

---

## 20. Practice Exercises (Topics Only)

- **Easy:** Install ragas 0.4.x; score 3 deliberately broken rows to light up the right metric.
- **Easy:** Build a 10-question golden set for an EU-bank policy corpus (citation, paraphrase, multi-hop, non-English).
- **Medium:** pytest fixture with the Ragas threshold gate (stubbed so it never flakes).
- **Medium:** GitHub Actions workflow + PR comment listing breached metrics.
- **Hard:** Customer scorecard generator (1-page PDF/HTML: value, delta, traffic light, trend).
- **Graded:** 50-question golden + Ragas eval + CI gate for the EU-bank RAG (including a renewal-tier gate).
- **Hard:** Judge noise and the flaky gate (paired-delta approach).
- **Hard:** Calibrate the judge to the SME (derive the cutoff from accept/reject calls).

---

## 21. Cheat Sheet (Memorize These)

- **"How do you know?" → Ragas on an SME golden set, gated in CI.**
- **4 metrics:** faithfulness (hallucination), answer relevancy (on-topic), context precision (signal vs noise), context recall (missing evidence).
- **Generator = faithfulness + relevancy. Retriever = precision + recall.**
- **Relevancy lies** (correctness-blind); **faithfulness can bless a wrong chunk.** Read all four.
- **Gate:** faithfulness ≥ 0.85, precision ≥ 0.80 (regulated: 0.95). **Per-metric, never averaged.**
- **Set the gate at the current floor minus a small buffer.** Vanity thresholds = theatre. **Ratchet up, never down.**
- **SME owns the gold; FDE owns the harness.** 50 → 200 questions; refresh every **90 days**.
- **Reference-free (faithfulness, relevancy) = online. Reference-required (recall) = offline only.**
- **Judge noise:** measure std (> 0.04 = noisy), use self-consistency, one-sided bound, or a **paired-delta gate**.
- **Judge:** Haiku for PR-CI, Sonnet 5 for nightly/scorecard. **Pin the version.** Cross-check with a different-family judge (self-enhancement bias).
- **Calibrate to the SME:** **Cohen's kappa** > 0.6–0.8; inter-SME agreement caps judge quality.
- **Debug the retriever first** (precision/recall need no generator call).
- **Scorecard:** 4 metrics + trend + targets; one-number fallback = **min(faithfulness, precision)**.
- **Ragas isn't enough:** add reasoning evals, business-rule snapshots, injection red-team, latency/cost via OTel.
- **Auto-generated golden sets mislead.** Real users don't talk like LLMs.
