# Architecture

> Learning project. All data is fictional. See the [README](../README.md).

## 1. The system map

Where everything lives. Gemini is the only part outside your machine, and the only part that "thinks". It never touches data directly. It can only ask to call a tool.

```mermaid
flowchart TB
    subgraph CLOUD["☁️ Google Cloud"]
        GEMINI["🧠 Gemini<br/>decides which tool to call<br/>and writes the answer"]
    end

    subgraph MAC["💻 Local machine"]
        USER["🌐 Browser (ADK Web)<br/>the CSM"]

        subgraph ADK["⚙️ ADK process (adk web, port 8000)"]
            subgraph PKG["📦 csm_agent"]
                AGENT["🤖 agent.py<br/>instruction + tool list"]

                subgraph TOOLS["🧰 tools.py: the doors the model may open"]
                    T1[list_accounts]
                    T2[get_account_usage]
                    T3[calculate_risk]
                    T4[find_opportunities]
                    T5[search_playbook]
                    T6["create_task 🔒"]
                end

                subgraph LOGIC["⚙️ Logic: pure Python, no AI"]
                    L1[risk_scoring.py]
                    L2[opportunity_rules.py]
                    L3[playbook_search.py]
                    L4[tasks.py]
                end

                subgraph DATA["🗄️ data_source.py: the only file that knows where data lives"]
                    D1[(accounts.json)]
                    D2[(playbook.md)]
                    D3[(crm_tasks.json)]
                end
            end
        end

        ENV["🔐 .env<br/>API key, never in git"]
        TESTS["🧪 tests/<br/>69 tests, no model, no network"]
    end

    USER <--> ADK
    ADK <-->|"API calls"| GEMINI
    AGENT --- TOOLS
    TOOLS --> LOGIC
    TOOLS --> DATA
    TESTS -.->|"test directly"| LOGIC
    TESTS -.-> DATA
```

## 2. The layers and why each exists

| Layer | File(s) | Responsibility | Without it... |
|---|---|---|---|
| 🧠 **Model** | Gemini (cloud) | Understands the question, decides which tools to call, explains results | You'd need an `if` for every possible CSM question |
| 🤖 **Agent** | `agent.py` | Instruction (system prompt) + list of allowed tools | The model wouldn't know its role or its rules |
| 🧰 **Tools** | `tools.py` | The only actions the model can take. Docstrings are the model's "manual" | The model would invent data it has no access to |
| ⚙️ **Logic** | `risk_scoring.py`, `opportunity_rules.py`, `playbook_search.py`, `tasks.py` | Deterministic calculations: same input, same output | The score would change between runs and couldn't be explained or tested |
| 🗄️ **Data access** | `data_source.py` | Reads and writes accounts, playbook, tasks | Moving to Salesforce would mean changing every file |
| 🔒 **Approval** | `FunctionTool(..., require_confirmation=True)` | Framework pauses before the CRM write | The model could write to the CRM on its own, even when wrong |

**One sentence:** the model decides *what* to do, tools define *what is possible*, logic calculates *the answer*, and the data layer knows *where data lives*. Each layer can be replaced without touching the others.

## 3. How a request flows

### Portfolio question: "Which accounts need attention this week?"

The model chooses the sequence on its own. No code says "first list, then score".

```mermaid
sequenceDiagram
    actor CSM as 🌐 CSM
    participant ADK as ⚙️ ADK
    participant LLM as 🧠 Gemini
    participant Tools as 🧰 Tools
    participant Logic as ⚙️ Logic
    participant Data as 🗄️ data_source

    CSM->>ADK: "Which accounts need attention this week?"
    ADK->>LLM: question + instruction + 6 tool descriptions
    LLM-->>ADK: call list_accounts()
    ADK->>Tools: list_accounts()
    Tools->>Data: list_accounts()
    Data-->>Tools: 6 accounts
    Tools-->>LLM: account summaries
    LLM-->>ADK: call calculate_risk() for each account
    loop for each account
        ADK->>Tools: calculate_risk("Acme")
        Tools->>Data: find_account("Acme")
        Tools->>Logic: score_account(data)
        Logic-->>Tools: score 100, High, reasons
    end
    Tools-->>LLM: 6 risk results
    LLM-->>CSM: ranked list with reasons
```

### Writing to the CRM: human in the loop

```mermaid
sequenceDiagram
    actor CSM as 🌐 CSM
    participant ADK as ⚙️ ADK
    participant LLM as 🧠 Gemini
    participant Tool as 🧰 create_task
    participant Data as 🗄️ crm_tasks.json

    CSM->>ADK: "Create a follow-up for Acme"
    ADK->>LLM: question
    LLM-->>ADK: call create_task(account, subject, due_in_days, ...)
    Note over ADK: 🔒 require_confirmation=True<br/>The code has NOT run yet
    ADK-->>CSM: ⏸️ Approve this task?
    alt Approved
        CSM->>ADK: ✅ Approve
        ADK->>Tool: run create_task
        Note over Tool: code sets owner, priority,<br/>due date, checks duplicates
        Tool->>Data: save task
        Tool-->>LLM: TASK-0001 created
        LLM-->>CSM: "Created TASK-0001 for Dana, due Oct 5"
    else Rejected
        CSM->>ADK: ❌ Reject
        ADK-->>LLM: tool was rejected
        LLM-->>CSM: "OK, no task created"
    end
```

## 4. Who decides what

The model is responsible only for language and judgment. Everything that must be consistent or exact is decided in code.

| Decision | Model 🧠 | Code ⚙️ |
|---|---|---|
| Which tools to call, in what order | ✅ | |
| Risk score, level, reasons | | ✅ |
| Urgency (days to renewal) | | ✅ |
| Which opportunities exist | | ✅ |
| Which playbook section matches | | ✅ |
| Task subject and description (wording) | ✅ | |
| Task due date (from `due_in_days`) | | ✅ (models get date math wrong) |
| Task priority | | ✅ (from risk level) |
| Task owner | | ✅ (account's CSM) |
| Whether a task is a duplicate | | ✅ |
| Whether the task is created at all | | 👤 **The human** |

## 5. Moving to production

Only `data_source.py` changes. Every other file stays the same.

| Today (mock) | Production example |
|---|---|
| `accounts.json` | Salesforce (accounts, contracts) + product telemetry (downloads, consumption) + support system (tickets) |
| `playbook.md` | Confluence / Notion / Gainsight. For a large playbook, a RAG search such as Vertex AI Search |
| `crm_tasks.json` | Salesforce Task object |
| `adk web` locally | Deployed agent, e.g. Cloud Run or Vertex AI Agent Engine |
| Free-tier API key | Paid key with quota and monitoring |
