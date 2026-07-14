from pathlib import Path

from langchain_core.messages import AIMessage

from app.state import AgentState


from langgraph.types import interrupt


async def project_context_node(state):

    if state.get("repo_root"):
        return {}

    repo_root = interrupt("Please enter the project root path.")

    return {"repo_root": repo_root}
