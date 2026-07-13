from langgraph.graph.message import MessagesState, add_messages
from typing import TypedDict, Annotated


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next_node: str
    repo_root: str | None
    repo_analysis: dict
    dependency_context: str
    framework: dict
    language: dict
    runtime: dict
    package_manager: dict
    build_tools: dict
    repo_dependencies: dict
