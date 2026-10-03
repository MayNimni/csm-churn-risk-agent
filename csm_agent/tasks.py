"""Builds CRM tasks. Pure logic, no file access: validation, de-duplication,
due date and priority are decided here in code; the model only supplies the
wording (subject, description) and how many days until the task is due."""

from datetime import date, datetime, timedelta

MAX_DUE_IN_DAYS = 90

# Task priority follows the account's risk level, so it is consistent.
PRIORITY_BY_RISK_LEVEL = {"High": "High", "Medium": "Medium", "Low": "Low"}


def build_task(
    account: dict,
    risk_level: str,
    subject: str,
    description: str,
    due_in_days: int,
    playbook_key: str,
    existing_tasks: list[dict],
    today: date | None = None,
    now: datetime | None = None,
) -> dict:
    """Returns {"status": "success", "task": {...}} or {"status": "error", ...}."""
    today = today or date.today()
    now = now or datetime.now()

    if not subject.strip():
        return {"status": "error", "message": "Task subject cannot be empty."}
    if not 1 <= due_in_days <= MAX_DUE_IN_DAYS:
        return {"status": "error",
                "message": f"due_in_days must be between 1 and {MAX_DUE_IN_DAYS}."}

    for task in existing_tasks:
        if (playbook_key and task["status"] == "Open"
                and task["account_id"] == account["account_id"]
                and task["playbook_key"] == playbook_key):
            return {"status": "error",
                    "message": f"An open task already exists for this issue: {task['task_id']}.",
                    "existing_task": task}

    return {"status": "success", "task": {
        "task_id": f"TASK-{len(existing_tasks) + 1:04d}",
        "account_id": account["account_id"],
        "account_name": account["name"],
        "owner": account["csm_owner"],
        "subject": subject.strip(),
        "description": description.strip(),
        "playbook_key": playbook_key,
        "due_date": (today + timedelta(days=due_in_days)).isoformat(),
        "priority": PRIORITY_BY_RISK_LEVEL[risk_level],
        "status": "Open",
        "created_at": now.isoformat(timespec="seconds"),
        "created_by": "csm_agent (approved by user)",
    }}
