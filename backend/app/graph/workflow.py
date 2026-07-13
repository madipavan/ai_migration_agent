from langgraph.graph import StateGraph, START, END
from app.state import AgentState
from app.nodes.intent_classifier import intent_classifier
from app.nodes.chat_node import chat_node

workflow = StateGraph(AgentState)

# first thing is know user intent thn next
workflow.add_node("intent_classifier", intent_classifier)
workflow.add_node("chat_node", chat_node)

workflow.add_edge(START, "intent_classifier")
workflow.add_edge("intent_classifier", END)

workflow.add_conditional_edges(
    "intent_classifier",
    lambda state: state["next_node"],
    {
        # "migration": "migration_node",
        "analyze_dependencies": "dependency_node",
        # "refactor_syntax": "refactor_node",
        "chat": "chat_node",
    },
)

graph = workflow.compile()
