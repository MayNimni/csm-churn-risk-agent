# How to run

> Learning project. All data is fictional. See the [README](../README.md).

## Prerequisites

- Python 3.11+ (developed on 3.14)
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

## Setup

```bash
git clone <this-repo-url>
cd risk_agent

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env
```

Open `.env` and paste your key after `GEMINI_API_KEY=`, with no quotes or spaces.
**Never commit `.env`.** It's already listed in `.gitignore`.

## Run the agent

**Browser UI (recommended).** Shows every tool call and its result:

```bash
.venv/bin/adk web
```

Open http://127.0.0.1:8000 and select `csm_agent`.

**Terminal:**

```bash
.venv/bin/adk run csm_agent
```

## Demo scenarios

Start each one with **New Session**, and watch the **Events** tab to see which tools the agent chose.

| # | Ask | Expected tools | What it shows |
|---|---|---|---|
| 1 | `Which accounts need attention this week?` | `list_accounts` → `calculate_risk` × 6 | The agent plans on its own. Ranking comes from code |
| 2 | `Why is Acme high risk?` | `calculate_risk` | Transparent reasons with points |
| 3 | `What can we offer Fusion Media?` | `find_opportunities` | Opportunity linked to a risk |
| 4 | `What should I do about Delta this week?` | several tools + `search_playbook` | Advice grounded in the playbook |
| 5 | `Create a follow-up task for Acme about the champion who left` | `create_task` 🔒 | Approval dialog. Try both reject and approve |

View created tasks:

```bash
cat csm_agent/data/crm_tasks.json
```

Reset the CRM before a demo:

```bash
rm csm_agent/data/crm_tasks.json
```

## Run the tests

No model, API key, or internet needed:

```bash
.venv/bin/pytest -v
```

## Debugging

Follow the request through the layers and find where it stopped:

| Layer | Where to look |
|---|---|
| 🌐 Browser / ⚙️ ADK | **Events** tab in ADK Web: every tool call, its arguments, and its result |
| 🧰 Tool returned an error | Click the tool event. The `message` explains why (e.g. duplicate task) |
| ⚙️ Logic / 🗄️ Data | Run the tests for that layer, e.g. `.venv/bin/pytest tests/test_tasks.py -v` |
| Step through code | VS Code → Run and Debug → choose a config from `.vscode/launch.json` → set a breakpoint |

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `address already in use` (port 8000) | Another `adk web` is still running | Stop it with `Ctrl+C` in its terminal, or run `lsof -i :8000` to find it |
| `503 UNAVAILABLE` / "high demand" | Gemini is temporarily overloaded | Wait and retry, or switch the model in `agent.py` |
| `429 RESOURCE_EXHAUSTED` | Free-tier daily quota used up (about 20 requests/day per model) | Wait for reset, use another model, or use a paid key |
| Agent doesn't see code changes | Server loaded the old code | Restart `adk web` |
| `zsh: command not found` | Typed a chat message in the terminal | Chat in the browser. The terminal only runs the server |
