"""Data access layer: the ONLY file that knows where data lives.

Today it reads local mock files. In production this file would be replaced
by one that calls real systems (e.g. Salesforce for accounts, Confluence for
the playbook), keeping the same function names and return shapes, so the
tools and the agent stay unchanged.
"""

import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data"
_ACCOUNTS_FILE = _DATA_DIR / "accounts.json"
_PLAYBOOK_FILE = _DATA_DIR / "playbook.md"
_TASKS_FILE = _DATA_DIR / "crm_tasks.json"  # created on first save


def _load_accounts() -> list[dict]:
    with open(_ACCOUNTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def list_accounts() -> list[dict]:
    """Returns all accounts."""
    return _load_accounts()


def find_account(query: str) -> dict | None:
    """Returns one account matched by ID or name (case-insensitive), or None."""
    q = query.strip().lower()
    for account in _load_accounts():
        if q == account["account_id"].lower() or q in account["name"].lower():
            return account
    return None


def load_playbook_sections() -> list[dict]:
    """Returns playbook sections as [{"title", "keys", "content"}].

    In playbook.md each section starts with "## Title", followed by a
    "Keys: a, b" line; everything until the next "## " is its content.
    """
    sections = []
    text = _PLAYBOOK_FILE.read_text(encoding="utf-8")
    for block in text.split("\n## ")[1:]:
        title, _, rest = block.partition("\n")
        keys_line, _, content = rest.partition("\n")
        keys = [k.strip() for k in keys_line.removeprefix("Keys:").split(",")]
        sections.append({"title": title.strip(), "keys": keys, "content": content.strip()})
    return sections


def list_tasks() -> list[dict]:
    """Returns all CRM tasks (empty list if none were created yet)."""
    if not _TASKS_FILE.exists():
        return []
    with open(_TASKS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_task(task: dict) -> None:
    """Appends one task to the CRM."""
    tasks = list_tasks()
    tasks.append(task)
    with open(_TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
