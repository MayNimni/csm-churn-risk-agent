from google.adk.agents.llm_agent import Agent
from google.adk.tools.function_tool import FunctionTool

from .tools import (
    calculate_risk,
    create_task,
    find_opportunities,
    get_account_usage,
    list_accounts,
    search_playbook,
)

root_agent = Agent(
    # flash-lite: separate free-tier quota from gemini-3.5-flash (20 requests/day).
    model="gemini-3.5-flash-lite",
    name="csm_agent",
    description="Helps Customer Success Managers spot accounts at risk of churn.",
    instruction=(
        "You are a helpful assistant for Customer Success Managers at JFrog. "
        "Use get_account_usage to fetch real account data. Never invent account data. "
        "For portfolio questions (e.g. 'which accounts need attention?'), call "
        "list_accounts, then calculate_risk for every account, and rank them by "
        "risk_score and urgency. "
        "For any question about churn risk, call calculate_risk and report its "
        "risk_score, risk_level and urgency exactly as returned. Never estimate or "
        "adjust the risk yourself; explain it using the returned reasons. "
        "For growth, upsell or 'what can we offer' questions, call find_opportunities. "
        "When an opportunity has addresses_risk, present it as a fix for that problem. "
        "For recommended actions, call search_playbook with the rule names and "
        "opportunity types you received, and base your advice on the playbook only. "
        "When the user wants follow-ups, call create_task once per task; the user "
        "will be asked to approve each one. "
        "Answer briefly."
    ),
    tools=[
        list_accounts,
        get_account_usage,
        calculate_risk,
        find_opportunities,
        search_playbook,
        # Writes to the CRM: the framework pauses for user approval before running it.
        FunctionTool(create_task, require_confirmation=True),
    ],
)
