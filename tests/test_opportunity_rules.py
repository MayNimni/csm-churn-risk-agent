"""Unit tests for the opportunity rules.

Each test starts from an account with no opportunities and changes only
what one rule looks at.
"""

import pytest

from csm_agent.opportunity_rules import find_account_opportunities


@pytest.fixture
def no_opportunities():
    return {
        "subscription_tier": "Enterprise X",
        "deployment": "SaaS",
        "products_licensed": ["Artifactory", "Xray", "Advanced Security"],
        "products_active": ["Artifactory", "Xray", "Advanced Security"],
        "consumption_gb_last_month": 80,
        "consumption_gb_committed": 100,
        "critical_vulnerabilities_open": 0,
        "artifact_downloads_last_30_days": 1000,
        "artifact_downloads_previous_30_days": 1000,
        "active_projects": 5,
    }


def types_found(account):
    return [o["type"] for o in find_account_opportunities(account)]


def test_baseline_has_no_opportunities(no_opportunities):
    assert find_account_opportunities(no_opportunities) == []


def test_adoption_links_to_shelfware_risk(no_opportunities):
    no_opportunities["products_active"] = ["Artifactory", "Xray"]
    [opp] = find_account_opportunities(no_opportunities)
    assert opp["type"] == "adoption"
    assert "Advanced Security" in opp["recommendation"]
    assert opp["addresses_risk"] == "shelfware"


@pytest.mark.parametrize("used, found", [(100, False), (101, True), (None, False)])
def test_tier_upgrade_only_above_commitment(no_opportunities, used, found):
    no_opportunities["consumption_gb_last_month"] = used
    assert ("tier_upgrade" in types_found(no_opportunities)) is found


def test_security_cross_sell_when_no_xray(no_opportunities):
    no_opportunities["products_licensed"] = ["Artifactory"]
    no_opportunities["products_active"] = ["Artifactory"]
    assert types_found(no_opportunities) == ["security_cross_sell"]


@pytest.mark.parametrize("critical, found", [(9, False), (10, True), (None, False)])
def test_advanced_security_threshold(no_opportunities, critical, found):
    no_opportunities["products_licensed"] = ["Artifactory", "Xray"]
    no_opportunities["products_active"] = ["Artifactory", "Xray"]
    no_opportunities["critical_vulnerabilities_open"] = critical
    assert ("advanced_security" in types_found(no_opportunities)) is found


def test_advanced_security_needs_active_xray(no_opportunities):
    no_opportunities["products_licensed"] = ["Artifactory", "Xray"]
    no_opportunities["products_active"] = ["Artifactory"]  # Xray licensed but unused
    no_opportunities["critical_vulnerabilities_open"] = 50
    assert "advanced_security" not in types_found(no_opportunities)


@pytest.mark.parametrize("downloads_now, projects, found", [
    (1100, 5, True),   # growing, at benchmark
    (1000, 5, False),  # flat
    (1100, 4, False),  # growing but below benchmark
])
def test_expansion(no_opportunities, downloads_now, projects, found):
    no_opportunities["artifact_downloads_last_30_days"] = downloads_now
    no_opportunities["active_projects"] = projects
    assert ("expansion" in types_found(no_opportunities)) is found


def test_saas_migration_for_self_managed(no_opportunities):
    no_opportunities["deployment"] = "Self-Managed"
    no_opportunities["consumption_gb_last_month"] = None
    no_opportunities["consumption_gb_committed"] = None
    assert types_found(no_opportunities) == ["saas_migration"]
