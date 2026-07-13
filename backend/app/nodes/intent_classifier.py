from app.state import AgentState
from pydantic import Field, BaseModel
from typing import Literal
from app.core.get_llm import get_llm


class IntentClassifier(BaseModel):
    intent: Literal["migration", "analyze_dependencies", "refactor_syntax", "chat"] = (
        Field(
            description=(
                "Classify the structural intent of the codebase instruction: "
                "'migration' if the user gives a general or broad command to migrate, upgrade, or port a file or project; "
                "'analyze_dependencies' if they specifically want to check packages, libraries, or version compatibility; "
                "'refactor_syntax' if they provide a specific code snippet or function to rewrite to a newer version; "
                "'chat' for greetings, small talk, or general non-technical conversation."
            )
        )
    )


llm = get_llm()
str_output = llm.with_structured_output(schema=IntentClassifier)


async def intent_classifier(state: AgentState) -> str:
    messages = state["messages"]
    result = await str_output.ainvoke(messages)

    return {"next_node": result.intent}
