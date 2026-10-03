"""Deterministic opportunity detection (upsell, cross-sell, adoption).

Same idea as risk_scoring.py: fixed rules in code decide WHICH opportunities
exist; the model only explains them. Opportunities are shown for every
account, including at-risk ones: when an opportunity solves a risk, the
"addresses_risk" field links it to that problem, so it can be pitched as a
fix rather than a sale.
"""

# Same tier benchmark as the risk rules, so "healthy usage" means one thing.
from .risk_scoring import PROJECTS_BENCHMARK_BY_TIER

# --- Rule settings -------------------------------------------------------
OVER_CONSUMPTION_FROM = 1.0          # using more than 100% of committed GB
ADVANCED_SECURITY_MIN_CRITICAL = 10  # open critical vulnerabilities in Xray


def find_account_opportunities(account: dict) -> list[dict]:
    """Applies every opportunity rule to one account and returns the matches."""
    opportunities = []

    def add(kind: str, recommendation: str, reason: str,
            addresses_risk: str | None = None) -> None:
        opportunities.append({
            "type": kind,
            "recommendation": recommendation,
            "reason": reason,
            "addresses_risk": addresses_risk,
        })

    licensed = account["products_licensed"]
    active = account["products_active"]

    # 1. Adoption: products already paid for but not used
    unused = [p for p in licensed if p not in active]
    if unused:
        add("adoption", f"Enablement session to activate {', '.join(unused)}",
            f"Licensed but not active: {', '.join(unused)}",
            addresses_risk="shelfware")

    # 2. Tier upgrade: consuming more than committed (SaaS only)
    used, committed = account["consumption_gb_last_month"], account["consumption_gb_committed"]
    if used is not None and committed and used / committed > OVER_CONSUMPTION_FROM:
        add("tier_upgrade", "Upgrade tier or increase the consumption commitment",
            f"Using {used / committed:.0%} of committed consumption ({used} of {committed} GB)")

    # 3. Security cross-sell: no Xray at all
    if "Xray" not in licensed:
        add("security_cross_sell", "Introduce Xray and Curation",
            "No software composition analysis (Xray) in the subscription")

    # 4. Advanced Security: Xray finds many critical issues the team isn't resolving
    critical = account["critical_vulnerabilities_open"]
    if ("Xray" in active and "Advanced Security" not in licensed
            and critical is not None and critical >= ADVANCED_SECURITY_MIN_CRITICAL):
        add("advanced_security", "Introduce Advanced Security",
            f"{critical} open critical vulnerabilities found by Xray",
            addresses_risk="critical_vulnerabilities")

    # 5. Expansion: usage growing and adoption at or above the tier norm
    benchmark = PROJECTS_BENCHMARK_BY_TIER.get(account["subscription_tier"])
    growing = (account["artifact_downloads_last_30_days"]
               > account["artifact_downloads_previous_30_days"])
    if growing and benchmark and account["active_projects"] >= benchmark:
        add("expansion", "Discuss expansion to more teams or a higher tier",
            f"Downloads growing and {account['active_projects']} active projects "
            f"(benchmark for {account['subscription_tier']}: {benchmark})")

    # 6. SaaS migration
    if account["deployment"] == "Self-Managed":
        add("saas_migration", "Explore migration to JFrog SaaS",
            "Currently on a Self-Managed deployment")

    return opportunities
