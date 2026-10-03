# CSM Churn-Risk Agent

> ⚠️ **Learning project. All data is fictional.**
> Every customer, number, and person in this repo is made up for demonstration.
> This is a personal project for learning [Google ADK](https://google.github.io/adk-docs/) and is
> **not affiliated with, endorsed by, or based on internal data of JFrog** or any other company.
> JFrog product and tier names are used only to make the scenario realistic, based on JFrog's public website.

An AI agent that helps a Customer Success Manager (CSM) answer one question:

> **"Which accounts need my attention this week, and what should I do about them?"**

Built with **Google ADK (Agent Development Kit)** and **Gemini**.

---

## Executive summary

| | |
|---|---|
| **Problem** | CSMs manage many accounts and spot churn signals too late. Signals are spread across usage data, support tickets, contracts, and people changes. |
| **Solution** | A conversational agent that checks the portfolio, scores churn risk, finds growth opportunities, recommends actions from a playbook, and creates CRM follow-up tasks after the CSM approves them. |
| **Core principle** | **The model decides *what to do*. Code calculates *the answer*.** Gemini chooses which tools to call and explains the results. The risk score is calculated by fixed rules in code, so it's consistent, explainable, and testable. |
| **Safety** | Writing to the CRM requires human approval. The framework enforces it (`require_confirmation`), not the prompt. |
| **Production path** | All data access is in one file (`data_source.py`). Moving from mock JSON to Salesforce/Confluence means replacing only that file. |
| **Quality** | 69 unit tests cover every rule, threshold boundary, and the links between components. They run without the model or internet. |

### What it looks like

```
You:    Which accounts need attention this week?

Agent:  [calls list_accounts → calculate_risk × 6]

        1. Acme Logistics   Risk 100 (High)   Urgency High   Renewal in 45 days
           Downloads -42%, champion left, Xray & Curation unused, 2 high-severity tickets...
        2. Cedar Retail     Risk 50 (Medium)  Urgency High   Renewal in 50 days
        3. Fusion Media     Risk 45 (Medium)  Urgency Low
        ...

You:    What should I do about Acme? Create follow-up tasks.

Agent:  [calls find_opportunities → search_playbook → create_task]
        ⏸️ Approval required: create task "Identify new champion" for Acme, due in 2 days?
```

### The six tools

| Tool | Question it answers | Writes data? |
|---|---|---|
| `list_accounts` | Who is in my portfolio? | No |
| `get_account_usage` | What does this account's usage look like? | No |
| `calculate_risk` | How risky is this account, and why? | No |
| `find_opportunities` | What can we offer them (adoption, upsell, cross-sell)? | No |
| `search_playbook` | What does our playbook recommend? | No |
| `create_task` | Create a follow-up in the CRM | **Yes, 🔒 approval required** |

---

## Documentation

| Document | Contents |
|---|---|
| [Architecture](docs/architecture.md) | System diagrams, layers, request flow |
| [Design decisions](docs/decisions.md) | Key decisions, alternatives considered, trade-offs |
| [Risk & opportunity model](docs/risk-model.md) | Every rule, threshold, and weight, and why |
| [How to run](docs/how-to-run.md) | Setup, demo scenarios, tests, troubleshooting |
| [Roadmap](docs/roadmap.md) | Known gaps and next steps: output guardrails, evals, production |

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # then add your free Gemini key from Google AI Studio
.venv/bin/adk web             # open http://127.0.0.1:8000
```

See [How to run](docs/how-to-run.md) for details.

## Project structure

```
risk_agent/
├── csm_agent/
│   ├── agent.py              # The agent: model, instruction, tools
│   ├── tools.py              # The 6 tools the model can call
│   ├── risk_scoring.py       # Deterministic risk rules (no AI)
│   ├── opportunity_rules.py  # Deterministic opportunity rules (no AI)
│   ├── playbook_search.py    # Playbook search: key match + keyword fallback
│   ├── tasks.py              # CRM task validation and building
│   ├── data_source.py        # The ONLY file that knows where data lives
│   └── data/
│       ├── accounts.json     # 6 fictional accounts
│       └── playbook.md       # CSM playbook (12 sections)
├── tests/                    # 69 unit tests (no model, no network)
└── docs/
```
