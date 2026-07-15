from app.agents.compatibility_assessment_agent import (
    CompatibilityAssessmentAgent,
)
from app.core.get_llm import get_llm
from app.state import AgentState


async def compatibility_assessment_node(state: AgentState):

    llm = get_llm()

    print("Starting compatibility assessment...")

    assessment_agent = CompatibilityAssessmentAgent(llm)

    assessment = await assessment_agent.assess(
        framework=state["framework"],
        language=state["language"],
        runtime=state["runtime"],
        package_manager=state["package_manager"],
        build_tools=state["build_tools"],
        latest_versions=state["latest_versions"],
        dependencies=state["repo_dependencies"],
    )

    return {"compatibility_assessment": assessment}
