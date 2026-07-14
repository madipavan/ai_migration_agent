from langgraph.graph import StateGraph, START, END
from app.nodes.project_context_node import project_context_node
from app.nodes.compatibility_assessment_node import compatibility_assessment_node
from app.nodes.assessment_summary_node import assessment_summary_node
from app.state import AgentState
from app.nodes.intent_classifier import intent_classifier
from app.graph.subgraphs.chat_graph import chat_graph
from app.graph.subgraphs.dependency_analysis_graph import dependency_analysis_graph
from langgraph.checkpoint.memory import InMemorySaver

workflow = StateGraph(AgentState)

# first thing is know user intent thn next
workflow.add_node("intent_classifier", intent_classifier)
workflow.add_node("chat_graph", chat_graph)
workflow.add_node("dependency_analysis_graph", dependency_analysis_graph)


workflow.add_edge(START, "intent_classifier")

workflow.add_conditional_edges(
    "intent_classifier",
    lambda state: state["next_node"],
    {
        # "migration": "migration_node",
        "analyze_dependencies": "dependency_analysis_graph",
        # "refactor_syntax": "refactor_node",
        "chat": "chat_graph",
    },
)

checkpoint = InMemorySaver()

graph = workflow.compile(checkpointer=checkpoint)
