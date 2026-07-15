from langchain_core.messages import AIMessage

from app.state import AgentState


async def assessment_summary_node(state: AgentState):

    assessment = state["compatibility_assessment"]

    summary = f"""
Repository analysis completed successfully.

Framework:
- {state["framework"]["name"]} {state["framework"]["version"]}

Latest Stable:
- {state["latest_versions"]}

Assessment:
- Migration Required: {"Yes" if assessment["migration_required"] else "No"}
- Update Only: {"Yes" if assessment["update_only"] else "No"}
- Severity: {assessment["severity"]}
- Breaking Changes: {"Yes" if assessment["breaking_changes"] else "No"}
- Runtime Upgrade Required: {"Yes" if assessment["runtime_upgrade_required"] else "No"}
- Estimated Complexity: {assessment["estimated_complexity"]}

Summary:
{assessment["summary"]}

Would you like me to continue with the migration?

Reply with:
- yes
- no
"""

    return {
        "messages": [AIMessage(content=summary)],
        "pending_action": "select_target_version",
    }
