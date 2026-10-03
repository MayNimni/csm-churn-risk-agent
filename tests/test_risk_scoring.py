"""Unit tests for the deterministic risk rules.

Each test starts from a perfectly healthy account (score 0) and changes
exactly one field, so a failing test points at exactly one rule.
"""

from datetime import date

import pytest

from csm_agent.risk_scoring import score_account

TODAY = date(2026, 10, 3)  # fixed date so results never depend on when tests run


@pytest.fixture
def healthy():
    return {
        "account_id": "TEST-1",
        "name": "Healthy Co",
        "subscription_tier": "Enterprise X",
        "products_licensed": ["Artifactory", "Xray"],
        "products_active": ["Artifactory", "Xray"],
        "artifact_downloads_last_30_days": 1000,
        "artifact_downloads_previous_30_days": 1000,
        "consumption_gb_last_month": 100,
        "consumption_gb_committed": 100,
        "active_projects": 5,
        "logins_last_30_days": 100,
        "logins_previous_30_days": 100,
        "key_user_left": False,
        "key_user_note": "",
        "high_severity_tickets": 0,
        "renewal_date": "2027-10-03",  # a year away
    }


def rules_fired(result):
    return {r["rule"]: r["points"] for r in result["reasons"]}


def test_healthy_account_scores_zero(healthy):
    result = score_account(healthy, TODAY)
    assert result["risk_score"] == 0
    assert result["risk_level"] == "Low"
    assert result["reasons"] == []


@pytest.mark.parametrize("downloads_now, expected_points", [
    (1000, None),  # no drop
    (850, None),   # exactly 15%: not above the threshold
    (800, 12),     # 20% drop
    (700, 12),     # exactly 30%: still the medium band
    (600, 25),     # 40% drop
])
def test_download_drop(healthy, downloads_now, expected_points):
    healthy["artifact_downloads_last_30_days"] = downloads_now
    assert rules_fired(score_account(healthy, TODAY)).get("download_drop") == expected_points


def test_key_user_left_uses_note_as_reason(healthy):
    healthy["key_user_left"] = True
    healthy["key_user_note"] = "Champion left"
    result = score_account(healthy, TODAY)
    assert rules_fired(result) == {"key_user_left": 20}
    assert result["reasons"][0]["reason"] == "Champion left"


@pytest.mark.parametrize("active, expected_points", [
    (["Artifactory", "Xray"], None),  # nothing unused
    (["Artifactory"], 15),            # 1 of 2 unused = half -> major
])
def test_shelfware_two_products(healthy, active, expected_points):
    healthy["products_active"] = active
    assert rules_fired(score_account(healthy, TODAY)).get("shelfware") == expected_points


def test_shelfware_minor_when_less_than_half_unused(healthy):
    healthy["products_licensed"] = ["Artifactory", "Xray", "Curation"]
    healthy["products_active"] = ["Artifactory", "Xray"]
    assert rules_fired(score_account(healthy, TODAY)).get("shelfware") == 8


@pytest.mark.parametrize("renewal_date, points, urgency", [
    ("2026-10-20", 15, "Critical"),  # 17 days
    ("2026-11-02", 15, "High"),      # 30 days: boundary -> High, not Critical
    ("2026-12-02", None, "Medium"),  # 60 days: no points
    ("2027-03-01", None, "Low"),
])
def test_renewal_points_and_urgency(healthy, renewal_date, points, urgency):
    healthy["renewal_date"] = renewal_date
    result = score_account(healthy, TODAY)
    assert rules_fired(result).get("renewal_soon") == points
    assert result["urgency"] == urgency


@pytest.mark.parametrize("tickets, expected_points", [(0, None), (1, 5), (2, 10), (7, 10)])
def test_high_severity_tickets(healthy, tickets, expected_points):
    healthy["high_severity_tickets"] = tickets
    assert rules_fired(score_account(healthy, TODAY)).get("high_severity_tickets") == expected_points


def test_low_consumption(healthy):
    healthy["consumption_gb_last_month"] = 60  # 60% of committed
    assert rules_fired(score_account(healthy, TODAY)).get("low_consumption") == 5


def test_self_managed_skips_consumption_rule(healthy):
    healthy["consumption_gb_last_month"] = None
    healthy["consumption_gb_committed"] = None
    assert score_account(healthy, TODAY)["risk_score"] == 0


@pytest.mark.parametrize("tier, projects, expected_points", [
    ("Enterprise X", 4, 5),   # below benchmark of 5
    ("Enterprise X", 5, None),
    ("Pro", 2, None),         # same 2 projects are fine for Pro...
    ("Enterprise+", 2, 5),    # ...but low for Enterprise+
])
def test_projects_relative_to_tier(healthy, tier, projects, expected_points):
    healthy["subscription_tier"] = tier
    healthy["active_projects"] = projects
    assert rules_fired(score_account(healthy, TODAY)).get("low_projects") == expected_points


def test_login_drop(healthy):
    healthy["logins_last_30_days"] = 60
    assert rules_fired(score_account(healthy, TODAY)) == {"login_drop": 5}


def test_score_levels_and_cap(healthy):
    healthy.update({
        "artifact_downloads_last_30_days": 100,
        "key_user_left": True,
        "products_active": [],
        "renewal_date": "2026-10-10",
        "high_severity_tickets": 3,
        "consumption_gb_last_month": 10,
        "active_projects": 0,
        "logins_last_30_days": 0,
    })
    result = score_account(healthy, TODAY)
    assert result["risk_score"] == 100
    assert result["risk_level"] == "High"


def test_same_input_same_output(healthy):
    healthy["artifact_downloads_last_30_days"] = 600
    assert score_account(healthy, TODAY) == score_account(healthy, TODAY)
