"""Tests for the tool layer that don't need the model."""

from csm_agent.tools import list_accounts


def test_list_accounts_returns_summaries_only():
    result = list_accounts()
    assert result["status"] == "success"
    assert len(result["accounts"]) == 6
    first = result["accounts"][0]
    assert set(first) == {"account_id", "name", "csm_owner", "subscription_tier",
                          "arr_usd", "renewal_date"}  # no usage details


def test_list_accounts_filters_by_owner_case_insensitive():
    names = {a["csm_owner"] for a in list_accounts(" dana ")["accounts"]}
    assert names == {"Dana"}


def test_list_accounts_unknown_owner_is_empty():
    assert list_accounts("Nobody")["accounts"] == []
