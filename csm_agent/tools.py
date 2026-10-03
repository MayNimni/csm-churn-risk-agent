"""Tools the agent can call. ADK reads each function's name, parameters and
docstring and shows them to the model, so the docstring is the 'manual' the
model uses to decide when to call the tool."""

from . import data_source
from .opportunity_rules import find_account_opportunities
from .playbook_search import search_sections
from .risk_scoring import score_account
from .tasks import build_task


def list_accounts(csm_owner: str = "") -> dict:
    """Lists customer accounts (the portfolio), optionally for one CSM.

    Use this first for portfolio-wide questions such as "which accounts need
    attention this week?", then check each account with the other tools.

    Args:
        csm_owner: Optional CSM name (e.g. "Dana") to list only their
            accounts. Leave empty for all accounts.

    Returns:
        A dict with "status" and "accounts": a short summary per account
        (account_id, name, csm_owner, subscription_tier, arr_usd,
        renewal_date). Use calculate_risk for the risk of each account.
    """
    accounts = data_source.list_accounts()
    if csm_owner:
        accounts = [a for a in accounts if a["csm_owner"].lower() == csm_owner.strip().lower()]
    summary_fields = ["account_id", "name", "csm_owner", "subscription_tier",
                      "arr_usd", "renewal_date"]
    return {"status": "success",
            "accounts": [{f: a[f] for f in summary_fields} for a in accounts]}


def get_account_usage(account: str) -> dict:
    """Gets usage and health data for one customer account.

    Args:
        account: The account ID (e.g. "ACC-001") or the account name
            (e.g. "Acme Logistics"). Partial names are accepted.

    Returns:
        A dict with "status" ("success" or "error"). On success, "account"
        holds JFrog platform usage for one customer:
        - subscription_tier (Pro / Pro X / Enterprise X / Enterprise+) and
          deployment (SaaS or Self-Managed), ARR and CSM owner.
        - products_licensed vs products_active: licensed products that are
          not active are paid-for but unused (shelfware).
        - artifact_downloads (last vs previous 30 days): the main usage
          signal, since most traffic comes from CI pipelines, not people.
        - consumption_gb (last month vs committed): SaaS billing is based on
          storage + data transfer; null for Self-Managed.
        - active_projects, UI logins, key_user_left, open/high-severity
          support tickets, critical_vulnerabilities_open (from Xray; null if
          Xray is not active) and renewal_date.
    """
    account_data = data_source.find_account(account)
    if account_data is None:
        return {"status": "error", "message": f"No account found for '{account}'."}
    return {"status": "success", "account": account_data}


def calculate_risk(account: str) -> dict:
    """Calculates the churn-risk score for one customer account.

    The score is computed by fixed, deterministic rules in code (not by AI),
    so it is consistent and explainable. Always use this tool for risk
    questions instead of estimating risk yourself.

    Args:
        account: The account ID (e.g. "ACC-001") or the account name
            (e.g. "Acme Logistics"). Partial names are accepted.

    Returns:
        A dict with "status" ("success" or "error"). On success, "risk" holds:
        - risk_score (0-100) and risk_level (Low / Medium / High).
        - reasons: every rule that fired, with its points and a plain-English
          explanation. Use these when explaining the score.
        - days_to_renewal and urgency (Critical / High / Medium / Low).
    """
    account_data = data_source.find_account(account)
    if account_data is None:
        return {"status": "error", "message": f"No account found for '{account}'."}
    return {"status": "success", "risk": score_account(account_data)}


def find_opportunities(account: str) -> dict:
    """Finds growth opportunities for one customer account: adoption of
    unused products, tier upgrade, cross-sell, Advanced Security, expansion
    and SaaS migration.

    Opportunities are detected by fixed rules in code. They apply to every
    account, including at-risk ones: when "addresses_risk" is set, present
    the opportunity as a solution to that problem, not as a sales pitch.

    Args:
        account: The account ID (e.g. "ACC-001") or the account name
            (e.g. "Acme Logistics"). Partial names are accepted.

    Returns:
        A dict with "status" ("success" or "error"). On success,
        "opportunities" is a list (possibly empty), each with type,
        recommendation, reason and addresses_risk (or null).
    """
    account_data = data_source.find_account(account)
    if account_data is None:
        return {"status": "error", "message": f"No account found for '{account}'."}
    return {
        "status": "success",
        "account": account_data["name"],
        "opportunities": find_account_opportunities(account_data),
    }


def search_playbook(query: str) -> dict:
    """Searches the CSM playbook for recommended actions.

    Best used with the exact rule or opportunity names returned by
    calculate_risk ("rule") and find_opportunities ("type"), e.g.
    "download_drop" or "shelfware, renewal_soon". Free-text questions
    (e.g. "champion left") are also supported via keyword search.

    Args:
        query: One or more rule/opportunity names separated by commas,
            or a short free-text question.

    Returns:
        A dict with "status". On success, "match_type" ("key" or "keyword")
        and "sections", each with a title and the playbook content
        (why it matters, actions by timeframe, talking point, when to
        escalate). Base recommendations on this content, not on general
        knowledge.
    """
    sections = data_source.load_playbook_sections()
    result = search_sections(query, sections)
    if result["match_type"] == "none":
        all_keys = sorted(k for s in sections for k in s["keys"])
        return {"status": "error",
                "message": f"No playbook section found for '{query}'.",
                "available_keys": all_keys}
    return {"status": "success", **result}


def create_task(
    account: str,
    subject: str,
    description: str,
    due_in_days: int,
    playbook_key: str = "",
) -> dict:
    """Creates a follow-up task in the CRM for the account's CSM.

    The user must approve every call (enforced by the framework). Owner,
    priority (from the risk level) and due date are set by code.

    Args:
        account: The account ID (e.g. "ACC-001") or name.
        subject: Short task title, e.g. "Identify new Artifactory admin".
        description: What to do, based on the playbook actions.
        due_in_days: Days from today until the task is due (1-90). Use the
            playbook timeframes, e.g. 2 for "first 48 hours", 14 for
            "next 2 weeks".
        playbook_key: The rule or opportunity name this task addresses,
            e.g. "key_user_left". Prevents duplicate open tasks.

    Returns:
        A dict with "status". On success, "task" is the saved task.
    """
    account_data = data_source.find_account(account)
    if account_data is None:
        return {"status": "error", "message": f"No account found for '{account}'."}
    risk_level = score_account(account_data)["risk_level"]
    result = build_task(account_data, risk_level, subject, description,
                        due_in_days, playbook_key, data_source.list_tasks())
    if result["status"] == "success":
        data_source.save_task(result["task"])
    return result
