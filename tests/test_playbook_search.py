"""Tests for the playbook: the search logic, the file parser, and that every
rule and opportunity the code can return has advice in the playbook."""

from datetime import date

import pytest

from csm_agent import data_source
from csm_agent.opportunity_rules import find_account_opportunities
from csm_agent.playbook_search import search_sections
from csm_agent.risk_scoring import score_account

FAKE_SECTIONS = [
    {"title": "Key user / champion left", "keys": ["key_user_left"],
     "content": "Find the new owner."},
    {"title": "Unused licensed products", "keys": ["shelfware", "adoption"],
     "content": "Run an enablement session."},
    {"title": "Renewal approaching", "keys": ["renewal_soon"],
     "content": "Hold a value review with the champion."},
]


def titles(result):
    return [s["title"] for s in result["sections"]]


# --- Search logic (fake sections, independent of the real file) ----------

def test_exact_key_match():
    result = search_sections("key_user_left", FAKE_SECTIONS)
    assert result["match_type"] == "key"
    assert titles(result) == ["Key user / champion left"]


def test_second_key_of_a_section_matches():
    assert titles(search_sections("adoption", FAKE_SECTIONS)) == ["Unused licensed products"]


def test_several_keys_return_several_sections():
    result = search_sections("shelfware, renewal_soon", FAKE_SECTIONS)
    assert titles(result) == ["Unused licensed products", "Renewal approaching"]


def test_key_match_is_case_insensitive():
    assert search_sections("KEY_USER_LEFT", FAKE_SECTIONS)["match_type"] == "key"


def test_keyword_fallback_prefers_title_match():
    # "champion" is in the title of section 1 and only in the content of section 3
    result = search_sections("What do I do when a champion leaves?", FAKE_SECTIONS)
    assert result["match_type"] == "keyword"
    assert titles(result) == ["Key user / champion left", "Renewal approaching"]


def test_stopwords_alone_do_not_match():
    assert search_sections("what should they do", FAKE_SECTIONS)["match_type"] == "none"


def test_no_match():
    result = search_sections("pricing", FAKE_SECTIONS)
    assert result == {"match_type": "none", "sections": []}


def test_results_do_not_expose_internal_keys():
    [section] = search_sections("renewal_soon", FAKE_SECTIONS)["sections"]
    assert set(section) == {"title", "content"}


# --- The real playbook file --------------------------------------------

@pytest.fixture(scope="module")
def real_sections():
    return data_source.load_playbook_sections()


def test_playbook_file_parses(real_sections):
    assert len(real_sections) == 12
    for section in real_sections:
        assert section["title"] and section["keys"] and section["content"]
        assert "Talking point" in section["content"]


def test_playbook_keys_are_unique(real_sections):
    keys = [k for s in real_sections for k in s["keys"]]
    assert len(keys) == len(set(keys))


def test_every_risk_rule_has_playbook_advice(real_sections):
    worst_account = {
        "account_id": "X", "name": "X", "subscription_tier": "Enterprise X",
        "products_licensed": ["Artifactory", "Xray"], "products_active": [],
        "artifact_downloads_last_30_days": 0, "artifact_downloads_previous_30_days": 100,
        "consumption_gb_last_month": 0, "consumption_gb_committed": 100,
        "active_projects": 0, "logins_last_30_days": 0, "logins_previous_30_days": 100,
        "key_user_left": True, "key_user_note": "", "high_severity_tickets": 5,
        "renewal_date": "2026-10-10",
    }
    rules = {r["rule"] for r in score_account(worst_account, date(2026, 10, 3))["reasons"]}
    assert len(rules) == 8  # every rule fired
    keys = {k for s in real_sections for k in s["keys"]}
    assert rules <= keys, f"Missing playbook sections for: {rules - keys}"


def test_every_opportunity_type_has_playbook_advice(real_sections):
    types = {o["type"] for a in data_source._load_accounts()
             for o in find_account_opportunities(a)}
    types |= {o["addresses_risk"] for a in data_source._load_accounts()
              for o in find_account_opportunities(a) if o["addresses_risk"]}
    assert len(types) >= 6
    keys = {k for s in real_sections for k in s["keys"]}
    assert types <= keys, f"Missing playbook sections for: {types - keys}"
