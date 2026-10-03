"""Tests for task creation: validation, de-duplication, code-set fields,
and saving to the mock CRM file."""

from datetime import date, datetime

import pytest

from csm_agent import data_source
from csm_agent.tasks import build_task

TODAY = date(2026, 10, 3)
NOW = datetime(2026, 10, 3, 14, 0)
ACCOUNT = {"account_id": "ACC-004", "name": "Delta Fintech", "csm_owner": "Yossi"}


def make(existing=None, **overrides):
    args = {"subject": "Find new admin", "description": "Ask for intro",
            "due_in_days": 2, "playbook_key": "key_user_left", "risk_level": "Medium"}
    args.update(overrides)
    return build_task(ACCOUNT, args["risk_level"], args["subject"], args["description"],
                      args["due_in_days"], args["playbook_key"], existing or [], TODAY, NOW)


def test_code_sets_owner_priority_due_date_and_id():
    task = make()["task"]
    assert task["task_id"] == "TASK-0001"
    assert task["owner"] == "Yossi"           # from the account, not the model
    assert task["priority"] == "Medium"       # from the risk level
    assert task["due_date"] == "2026-10-05"   # computed in code: today + 2
    assert task["status"] == "Open"


@pytest.mark.parametrize("level", ["High", "Medium", "Low"])
def test_priority_follows_risk_level(level):
    assert make(risk_level=level)["task"]["priority"] == level


@pytest.mark.parametrize("days, ok", [(0, False), (1, True), (90, True), (91, False)])
def test_due_in_days_range(days, ok):
    assert (make(due_in_days=days)["status"] == "success") is ok


def test_empty_subject_rejected():
    assert make(subject="   ")["status"] == "error"


def test_duplicate_open_task_rejected():
    first = make()["task"]
    result = make(existing=[first])
    assert result["status"] == "error"
    assert result["existing_task"]["task_id"] == "TASK-0001"


def test_same_issue_allowed_once_previous_task_closed():
    first = make()["task"] | {"status": "Completed"}
    assert make(existing=[first])["status"] == "success"


def test_different_issue_is_not_a_duplicate():
    first = make()["task"]
    second = make(existing=[first], playbook_key="shelfware")["task"]
    assert second["task_id"] == "TASK-0002"


def test_save_and_list_tasks(tmp_path, monkeypatch):
    # Point the CRM at a temporary file so tests never touch real data.
    monkeypatch.setattr(data_source, "_TASKS_FILE", tmp_path / "crm_tasks.json")
    assert data_source.list_tasks() == []
    data_source.save_task(make()["task"])
    assert [t["task_id"] for t in data_source.list_tasks()] == ["TASK-0001"]
