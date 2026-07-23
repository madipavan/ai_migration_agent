from pathlib import Path

from app.state import AgentState

from langchain_core.messages import AIMessage

from app.utils.dependency_helpers import collect_dependency_files


def migration_planner_node(state: AgentState):
    print("starting migration plan")

    repo_root = state.get("repo_root")

    if not repo_root:
        return {
            "messages": [
                AIMessage(content="Cannot migrate: repo_root is missing from state.")
            ]
        }
    print("--------before--------")
    repo_root = Path(state["repo_root"])
    analysis = state.get("repo_analysis") or {}
    declared = list(analysis.get("dependency_files") or [])
    print(repo_root)
    print(analysis)
    print(declared)
    print("--------after--------")
    original = collect_dependency_files(state)
    print(original)
