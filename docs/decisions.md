# Design decisions

> Learning project. All data is fictional. See the [README](../README.md).

Each decision lists the alternatives considered and why this one was chosen.

---

## D1. Risk is calculated in code, not by the model

**Decision:** `calculate_risk` applies fixed rules in `risk_scoring.py`. The model reports the result and explains it, but never estimates or adjusts it.

| Option | Pros | Cons |
|---|---|---|
| **Rules in code** ✅ | Consistent, explainable ("+25 because downloads dropped 42%"), testable | Rules must be designed and tuned by hand |
| Ask the model for a score | No code | Different answers between runs, can't be tested, can't explain why |

**Why:** A CSM must trust the number and be able to defend it to their manager. "The AI felt it was high" isn't an answer.

---

## D2. Tools take an account name, not the data

**Decision:** `calculate_risk("Acme")` fetches the data itself. The model never passes numbers into the calculation.

**Why:** If the model relayed the data, it could copy a number wrong or round it, and silently change the score. The model only identifies *which* account. Code handles the rest.

---

## D3. Human approval is enforced by the framework

**Decision:** `create_task` is wrapped in `FunctionTool(create_task, require_confirmation=True)`.

| Option | Enforcement |
|---|---|
| Prompt: "ask the user before creating tasks" | A request. The model can ignore it |
| **`require_confirmation=True`** ✅ | The function physically can't run without approval |

**Why:** Anything that writes to a system of record needs a guarantee, not a suggestion. One approval per task, so the CSM can approve some and reject others.

---

## D4. One file knows where data lives

**Decision:** All reads and writes go through `data_source.py`. Tools, logic, and the agent never open files.

**Why:** Moving from mock JSON to Salesforce/Confluence means replacing one file, with the same function names and return shapes.

---

## D5. Thresholds and weights live in one place, as constants

**Decision:** Every threshold, weight, and benchmark sits at the top of `risk_scoring.py` / `opportunity_rules.py`.

| Option | How | Pros | Cons |
|---|---|---|---|
| **A. Constants in code** ✅ | Numbers at the top of the file | Simple, transparent, reviewed in PRs, history in git | Changing a number needs a developer and a deploy |
| B. Config file (YAML/JSON) | Rules in a separate file | CS Ops can tune without code | Must validate the format |
| C. Data-driven benchmarks | Recompute tier medians daily from all accounts | Stays current as the customer base changes | Moving baseline, harder to compare scores over time |
| D. ML model | Learn from historical churn | More accurate, finds unexpected patterns | Needs labeled history, harder to explain, possible bias |
| E. Let the LLM decide | Ask Gemini for a score | Zero code | Inconsistent, untestable, unexplainable. This project avoids it on purpose |

**Path forward:** Start with A, because there's no historical data yet and CSMs must understand and trust the score. Once churn history exists, use ML to **calibrate the weights** while keeping the rule structure, as in credit scorecards:

1. **Collect labeled data:** each past renewal, with account signals 90 days before it and the outcome (renewed / churned).
2. **Per-rule lift analysis (no ML):** churn rate when a rule fired vs. when it didn't. Works even with little data.
3. **Logistic regression:** each rule becomes a feature, coefficients become weights, scaled to 100 points.
4. **Backtest** old vs. new weights on a held-out period before switching.

**Pitfalls:** too few churn events · CSM interventions change outcomes (a saved account looks like a "false alarm") · correlated signals (downloads and logins drop together) · data leakage (using signals from after the customer already decided to leave).

---

## D6. Relative thresholds, not absolute numbers

**Decision:** Each rule compares against something, because "4 projects" means nothing without context.

| Relativity | Compares | Example |
|---|---|---|
| **vs. itself** (trend) | Account now vs. account before | Downloads dropped 42% vs. previous 30 days |
| **vs. contract** | Usage vs. what was purchased | Using 60% of committed GB; 1 of 3 licensed products active |
| **vs. peers** (benchmark) | Account vs. tier norm | 3 projects is low for Enterprise X (norm 5) but high for Pro (norm 2) |

Exception: high-severity tickets are counted absolutely. A broken production build hurts at any account size.

---

## D7. Domain-specific signals (JFrog scenario)

**Decision:** The main usage signal is **artifact downloads**, not UI logins.

**Why:** On a platform like JFrog, most usage comes from machines (CI pipelines pulling packages), not people in the UI. UI logins stay as a weak signal (5 points). Terms were checked against JFrog's public website (tiers differ by deployment: SaaS = Pro / Enterprise X / Enterprise+, Self-Managed = Pro X / Enterprise X / Enterprise+; SaaS billing is consumption-based on storage + data transfer).

---

## D8. Renewal proximity is in the score and also a separate urgency field

**Decision:** Renewal under 60 days adds 15 points, **and** `calculate_risk` returns `days_to_renewal` and `urgency` (Critical < 30 · High < 60 · Medium < 90 · Low).

**Why:** If there's a problem close to renewal, it must be solved urgently, because revenue is directly at stake. The separate field also lets BI tools plot risk vs. urgency.

---

## D9. Opportunities are shown for every account, including at-risk ones

**Decision:** `find_opportunities` returns opportunities for all accounts. When an opportunity solves a risk, `addresses_risk` links them (e.g. adoption → shelfware), so it's presented as a fix, not a sales pitch.

**Why:** For an at-risk account, the right product can solve the problem that creates the risk. For example, Advanced Security for an account drowning in critical vulnerabilities.

---

## D10. Playbook search: exact key first, keyword fallback

**Decision:** Playbook sections are tagged with the same keys the rules return (`download_drop`, `shelfware`...). Exact key match first, keyword search as fallback.

| Option | Fits when |
|---|---|
| **Key match + keyword fallback** ✅ | Small playbook, topics map 1:1 to rules. Deterministic |
| RAG (embeddings + vector DB) | Hundreds of pages, semantic questions |

**Why:** Deterministic, and a test guarantees that every rule has a playbook section. Because search sits behind a tool, switching to RAG later changes nothing on the agent side.

---

## D11. `list_accounts` returns summaries; the model scores each account

**Decision:** For portfolio questions, the model calls `list_accounts`, then `calculate_risk` per account.

| Option | Pros | Cons |
|---|---|---|
| **Model loops over accounts** ✅ | The agent decides what to check. Composable | More model calls (quota, latency) |
| One tool that scores everything | One call, cheaper | Less agentic. The tool makes the decision |

---

## D12. Model choice and quota

**Decision:** `gemini-3.5-flash-lite`.

**Why:** The free tier allows about 20 requests per day per model, and one agent question uses several requests (one per tool round-trip). The lite model has a separate quota and responds faster. For a production or live demo, use a paid key with monitoring.
