# Risk & opportunity model

> Learning project. **All accounts, numbers, thresholds, and benchmarks are fictional**, chosen for the demo.
> In production, benchmarks would be computed from real data (e.g. the median per tier).

## Account data (per account)

| Field | Meaning | Why it matters for churn |
|---|---|---|
| `subscription_tier`, `deployment` | Pro / Pro X / Enterprise X / Enterprise+ · SaaS / Self-Managed | Context for benchmarks |
| `products_licensed` vs `products_active` | Paid for vs. actually used | Unused products (shelfware) are easy to cut at renewal |
| `artifact_downloads` (last vs previous 30 days) | Package traffic, mostly from CI | **Main usage signal** |
| `consumption_gb` (last month vs committed) | SaaS usage vs. commitment | Under = risk, over = upsell. `null` for Self-Managed |
| `active_projects` | Breadth of adoption | Fewer teams means a more fragile account |
| `logins` (last vs previous 30 days) | UI usage by people | Weak signal, since most usage is machines |
| `key_user_left` | Champion or admin left | No one inside defends the renewal |
| `high_severity_tickets` | Critical support issues | Broken builds erode trust fast |
| `critical_vulnerabilities_open` | Open critical issues found by Xray | Security gap. `null` if Xray is inactive |
| `renewal_date` | Contract renewal | Time left to fix problems |

## Risk rules (max 100 points)

| # | Rule | Relativity | Threshold | Points |
|---|---|---|---|---|
| 1 | Artifact downloads dropping | vs. itself | > 30% / 15–30% | **25** / 12 |
| 2 | Key user left | binary | `true` | **20** |
| 3 | Shelfware | vs. contract | ≥ half unused / ≥ 1 unused | **15** / 8 |
| 4 | Renewal soon | time | < 60 days | **15** |
| 5 | High-severity tickets | absolute | ≥ 2 / 1 | **10** / 5 |
| 6 | Under-consuming (SaaS) | vs. contract | < 70% of committed | **5** |
| 7 | Few projects for tier | vs. peers | below tier benchmark | **5** |
| 8 | UI logins dropping | vs. itself | > 30% | **5** |

**Risk level:** 0–29 Low · 30–59 Medium · 60+ High
**Urgency** (separate field): < 30 days Critical · < 60 High · < 90 Medium · otherwise Low
**Project benchmark by tier:** Pro 2 · Pro X 3 · Enterprise X 5 · Enterprise+ 10

## Opportunity rules

| # | Opportunity | Condition | Addresses risk |
|---|---|---|---|
| 1 | **Adoption** of products already paid for | A licensed product is not active | `shelfware` |
| 2 | **Tier upgrade** / bigger commitment | Consumption > 100% of committed (SaaS) | — |
| 3 | **Security cross-sell** (Xray, Curation) | No Xray in the subscription | — |
| 4 | **Advanced Security** | Xray active, no Advanced Security, ≥ 10 critical vulnerabilities | `critical_vulnerabilities` |
| 5 | **Expansion** | Downloads growing and projects ≥ tier benchmark | — |
| 6 | **SaaS migration** | Self-Managed deployment | — |

## Results on the fictional accounts

| Account | Risk | Level | Days to renewal | Urgency | Opportunities |
|---|---|---|---|---|---|
| Acme Logistics | 100 | High | 45 | High | Adoption (Xray, Curation) → fixes shelfware |
| Cedar Retail | 50 | Medium | 50 | High | Advanced Security → 14 critical vulns |
| Fusion Media | 45 | Medium | 300 | Low | Advanced Security → 58 critical vulns |
| Delta Fintech | 38 | Medium | 120 | Low | Adoption (Advanced Security), SaaS migration |
| Evergreen Education | 15 | Low | 30 | High | Tier upgrade (1240% consumption), security cross-sell, expansion |
| Brightpath Health | 0 | Low | 200 | Low | Security cross-sell, expansion, SaaS migration |

*Days to renewal are calculated from the current date (values shown for 2026-10-03).*

Each account is risky for a different reason, which is what makes the ranking meaningful.
At-risk accounts get opportunities that solve their problems, and healthy accounts get growth opportunities.

## Tests that protect the model

| Test file | What it guarantees |
|---|---|
| `test_risk_scoring.py` | Every rule fires at the right threshold, including boundaries (exactly 30% → 12 points, not 25) |
| `test_opportunity_rules.py` | Every opportunity rule and boundary (exactly 100% consumption is not over-consumption) |
| `test_playbook_search.py` | **Every risk rule and opportunity has a playbook section**: adding a rule without advice fails the build |
| `test_tasks.py` | Validation, duplicate prevention, code-set fields (owner, priority, due date) |
| `test_tools.py` | Portfolio listing and filtering |
