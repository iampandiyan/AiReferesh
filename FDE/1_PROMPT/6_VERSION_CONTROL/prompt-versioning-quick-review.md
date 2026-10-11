# Prompt Versioning "Prompt as Code": Quick Review (Module 3 · Lesson 3.6)

## The Big Idea
**Prompts are code. Treat them like SQL migrations:** versioned in Git, reviewed in a PR, rolled out gradually, and easy to roll back.

**The story:** Compliance couldn't tell what changed in a Notion-doc prompt (47 edit sessions) and the review took **3 weeks**. After moving prompts to versioned YAML in Git, the reviewer clicked a PR link, saw a 4-line diff, and approved in **30 minutes**.

---

## 1. What "Prompt as Code" Means
- Versioned in **Git**
- Reviewed in a **PR** (with a diff)
- Rolled out **gradually** (10% → 50% → 100%)
- **Rollback-able**
- Not just "write prompts in Python source" and not just "use a prompt store"

**Common misconception:** "We have evals, so we don't need snapshots." Evals catch **quality drift**. Snapshots catch **exact-output regressions**. You need both. Skipping snapshots leaves about 12-hour windows where bugs ship unnoticed.

---

## 2. Prompts as YAML Files
One file per version (e.g. `prompts/support-triage/v3.yaml`) with:
- `version`, `prompt_id`, `created_at`, `authors`
- `reviewers` (compliance, DPO, approved_at)
- `change_summary` (what changed and why)
- `golden_set_hash` (links to the snapshot suite)
- `eval_results` (accuracy, cost)
- `body` (the 6-section prompt from L3.1)

**Loading in code:** `load_prompt("support-triage", version="v3")`
- `"v3"` = explicit pin
- `"latest"` = follows the Git tag
- `"prod"` = follows the feature flag
- Send the version in a header / trace attribute (`x-prompt-version`).

**Use when:** engineering-led, git-native team. **Not when:** non-engineers must author prompts.

---

## 3. In-Repo vs Prompt Store

| | **In-repo (Git)** | **Prompt store** (PromptLayer / Langfuse / Braintrust) |
|---|---|---|
| Cost | Free | SaaS bill (usage-based) |
| Audit | Diffs, blame, PRs, tags | Built-in metrics and A/B, weaker audit by default |
| Speed | Slow (edit + deploy + cache invalidate) | **Hot-swap**, no deploy |
| Outage risk | None | Store down = your outage |
| Best for | Engineering teams, full audit trail | Non-engineer authors |

**Hybrid (what senior FDEs ship):** In-repo YAML is the **source of truth**. A **feature-flag override** gives ops hot-swap. The override is logged, alerted, and **time-boxed** (e.g. expires in 24h). With no override, production reads the repo version pinned by Git tag.

---

## 4. Git Tag Conventions
| Tag | Meaning |
|-----|---------|
| `prompt-support-triage-v3` | **Immutable** version tag |
| `prompt-support-triage-prod` | **Moving** tag → current production version |
| `prompt-support-triage-canary` | **Moving** tag → A/B candidate |

- Changing which prompt is live = **move a tag**, not a deploy.
- Without versioning you can't answer "which prompt was in prod when the bug happened?", which costs hours per incident.

---

## 5. A/B Rollout (10% → 50% → 100%)
- **Stable bucketing:** `sha256(customer_id) % 100`. The same customer always sees the same version.
- Tag every span with `gen_ai.prompt.version` and `gen_ai.prompt.id`.
- **Gates are metric checks, not calendar slots:**
  - **10% → 50%:** accuracy(v3) ≥ accuracy(v2) − 0.5 points, P95 latency stable, cost within about 5%, zero compliance complaints
  - **50% → 100%:** about 24h at 50% with all of the above + no DPO escalations + expected cost trajectory
  - **Rollback:** any gate fails → set `canary_pct` to 0, alert ops, open incident review (a one-line config change)
- Gates live in **CI / dashboards**, not in a runbook.
- Canary costs delay (about 4 days vs 1) but catches about 5% of regressions staging missed.
- **Skip it** for internal-only prompts you can roll back in 5 minutes.

---

## 6. Review Gates (Compliance + DPO + Domain Expert)
- **CODEOWNERS** on `prompts/**` makes compliance and DPO **required reviewers**.
- **CI checks on every prompt PR:**
  1. Snapshot suite against the new prompt
  2. Cost projection vs main
  3. Regression eval (multilingual code-mixed)
  4. Block merge without compliance approval
- Required for regulated workloads (finance, health, GDPR scope). The gate adds review time, but the alternative is six-figure fines.
- **Enforced > checklist:** CODEOWNERS + required-approver check beats "a checklist in the PR description."
- **Interview signal:** CODEOWNERS + required CI checks + snapshot suite + A/B with metric gates. Not "we'll add approval steps in JIRA."

---

## 7. Five Production Gotchas
1. **Prompt-store outage = your outage.** Use the hybrid (in-repo fallback).
2. **Cache invalidation on promotion:** Going to 100% invalidates the prompt cache (L3.5). Roll out off-peak and coordinate cache warming.
3. **Bucket drift:** Changing the hash function or bucket size mid-rollout flips customers between versions mid-conversation. Pin the formula in a constant; treat changes as breaking.
4. **Compliance not in CODEOWNERS:** A PR can merge without their signature.
5. **Untracked prod edits:** A 2 AM "quick fix" in the store UI leaves no audit trail. **Make the store read-only in production**. All edits go through repo + PR + CI.

---

## 8. Regulatory Cases
- **GDPR / CCPA / EU AI Act record-keeping:** Must record which automated-decision logic processed whose data. Git tag + `gen_ai.prompt.version` answers "for customer X in April, support-triage ran at v3 (commit abc123)."
- **Compliance officers as reviewers:** They aren't code-fluent but they **are diff-fluent**. Notion → GitHub PR is a small shift: same text, highlighted diff, approve button.
- **Convention:** Use the standard `prompts/` folder + YAML + tag + CODEOWNERS shape (Anthropic Cookbook, Mistral). Don't invent your own.

---

## 9. Analogy: A SQL Migration
- Numbered, authored, timestamped, reviewed as a diff, staged dev → staging → prod, rolled back with one command.
- **Where it breaks down:** SQL migrations are **one-way**; prompts are **fully reversible**. SQL has no A/B mode; prompts do, and should, because correctness is measured on a **metric**.

---

## 10. Quiz Answers (Self-Check)
| Q | Answer | Why |
|---|--------|-----|
| Q1 | **b** | Versioned in Git, reviewed in PR, gradual rollout, rollback-able |
| Q2 | **a** | Versioned YAML in your repo (hybrid with feature-flag hot-reload) |
| Q3 | **c** | 10% → 50% → 100% with metric watch, rollback on any regression |
| Q4 | **b** | Compliance + DPO sign-off + snapshot suite on a frozen golden set |
| Q5 | **b** | Hybrid: in-repo YAML as fallback keeps the service up |

---

## 11. Quick Memory Hooks
- **Prompt = code = SQL migration**
- **YAML in Git** is the source of truth; **feature-flag override** for hot-swap (time-boxed)
- **Tags:** `-v3` (immutable), `-prod` and `-canary` (moving)
- **Rollout: 10 → 50 → 100, gated by metrics, rollback = `canary_pct = 0`**
- **Stable bucket:** `sha256(customer_id) % 100`
- **CODEOWNERS + CI = enforced review**
- **Evals ≠ snapshots (need both)**
- **Store read-only in prod**
- **Tag every call with the prompt version**
