"""Deterministic churn-risk scoring.

Pure Python, no AI: the same account data always produces the same score.
All thresholds, weights and benchmarks live at the top of this file, so
tuning the model means editing numbers here and nothing else.
"""

from datetime import date

# --- Rule settings: (threshold, points) ---------------------------------
DOWNLOAD_DROP_HIGH = (0.30, 25)      # downloads dropped more than 30%
DOWNLOAD_DROP_MEDIUM = (0.15, 12)    # downloads dropped 15%-30%
KEY_USER_LEFT_POINTS = 20
SHELFWARE_MAJOR = (0.5, 15)          # at least half of licensed products unused
SHELFWARE_MINOR_POINTS = 8           # at least one licensed product unused
RENEWAL_SOON = (60, 15)              # renewal in less than 60 days
HIGH_SEVERITY_MANY = (2, 10)         # 2+ high-severity tickets
HIGH_SEVERITY_ONE_POINTS = 5         # exactly 1 high-severity ticket
LOW_CONSUMPTION = (0.70, 5)          # SaaS: using under 70% of committed GB
LOW_PROJECTS_POINTS = 5              # fewer projects than the tier benchmark
LOGIN_DROP = (0.30, 5)               # UI logins dropped more than 30%

# Expected number of active projects per tier (peer benchmark).
# Invented for the demo; in production, compute from real customer data
# (e.g. the median per tier).
PROJECTS_BENCHMARK_BY_TIER = {
    "Pro": 2,
    "Pro X": 3,
    "Enterprise X": 5,
    "Enterprise+": 10,
}

# --- Output levels -------------------------------------------------------
HIGH_RISK_FROM = 60
MEDIUM_RISK_FROM = 30

# (days_to_renewal is below this) -> urgency label
URGENCY_LEVELS = [(30, "Critical"), (60, "High"), (90, "Medium")]


def _drop(current: int, previous: int) -> float:
    """Fraction lost vs the previous period (0.42 = dropped 42%)."""
    if not previous:
        return 0.0
    return (previous - current) / previous


def _urgency(days_to_renewal: int) -> str:
    for limit, label in URGENCY_LEVELS:
        if days_to_renewal < limit:
            return label
    return "Low"


def score_account(account: dict, today: date | None = None) -> dict:
    """Applies every rule to one account and returns score, level and reasons."""
    today = today or date.today()
    reasons = []

    def add(rule: str, points: int, reason: str) -> None:
        reasons.append({"rule": rule, "points": points, "reason": reason})

    # 1. Artifact downloads trend (vs itself)
    drop = _drop(account["artifact_downloads_last_30_days"],
                 account["artifact_downloads_previous_30_days"])
    if drop > DOWNLOAD_DROP_HIGH[0]:
        add("download_drop", DOWNLOAD_DROP_HIGH[1],
            f"Artifact downloads dropped {drop:.0%} vs the previous 30 days")
    elif drop > DOWNLOAD_DROP_MEDIUM[0]:
        add("download_drop", DOWNLOAD_DROP_MEDIUM[1],
            f"Artifact downloads dropped {drop:.0%} vs the previous 30 days")

    # 2. Key user left
    if account["key_user_left"]:
        note = account.get("key_user_note") or "A key user left"
        add("key_user_left", KEY_USER_LEFT_POINTS, note)

    # 3. Shelfware (vs contract)
    licensed = account["products_licensed"]
    unused = [p for p in licensed if p not in account["products_active"]]
    if licensed and len(unused) / len(licensed) >= SHELFWARE_MAJOR[0]:
        add("shelfware", SHELFWARE_MAJOR[1],
            f"{len(unused)} of {len(licensed)} licensed products unused: {', '.join(unused)}")
    elif unused:
        add("shelfware", SHELFWARE_MINOR_POINTS,
            f"{len(unused)} of {len(licensed)} licensed products unused: {', '.join(unused)}")

    # 4. Renewal soon
    days_to_renewal = (date.fromisoformat(account["renewal_date"]) - today).days
    if days_to_renewal < RENEWAL_SOON[0]:
        add("renewal_soon", RENEWAL_SOON[1],
            f"Renewal in {days_to_renewal} days")

    # 5. High-severity tickets (absolute: a P1 hurts at any account size)
    high_sev = account["high_severity_tickets"]
    if high_sev >= HIGH_SEVERITY_MANY[0]:
        add("high_severity_tickets", HIGH_SEVERITY_MANY[1],
            f"{high_sev} open high-severity support tickets")
    elif high_sev == 1:
        add("high_severity_tickets", HIGH_SEVERITY_ONE_POINTS,
            "1 open high-severity support ticket")

    # 6. Consumption vs commitment (SaaS only; null for Self-Managed)
    used, committed = account["consumption_gb_last_month"], account["consumption_gb_committed"]
    if used is not None and committed:
        ratio = used / committed
        if ratio < LOW_CONSUMPTION[0]:
            add("low_consumption", LOW_CONSUMPTION[1],
                f"Using {ratio:.0%} of committed consumption ({used} of {committed} GB)")

    # 7. Projects vs tier benchmark (vs peers)
    benchmark = PROJECTS_BENCHMARK_BY_TIER.get(account["subscription_tier"])
    if benchmark and account["active_projects"] < benchmark:
        add("low_projects", LOW_PROJECTS_POINTS,
            f"{account['active_projects']} active projects, below the "
            f"{account['subscription_tier']} benchmark of {benchmark}")

    # 8. UI logins trend (weak signal: most JFrog usage is machines)
    login_drop = _drop(account["logins_last_30_days"], account["logins_previous_30_days"])
    if login_drop > LOGIN_DROP[0]:
        add("login_drop", LOGIN_DROP[1],
            f"UI logins dropped {login_drop:.0%} vs the previous 30 days")

    score = min(sum(r["points"] for r in reasons), 100)
    if score >= HIGH_RISK_FROM:
        level = "High"
    elif score >= MEDIUM_RISK_FROM:
        level = "Medium"
    else:
        level = "Low"

    return {
        "account_id": account["account_id"],
        "name": account["name"],
        "risk_score": score,
        "risk_level": level,
        "reasons": reasons,
        "days_to_renewal": days_to_renewal,
        "urgency": _urgency(days_to_renewal),
    }
