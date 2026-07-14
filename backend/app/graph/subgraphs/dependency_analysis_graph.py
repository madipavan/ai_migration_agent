from langgraph.graph import START, END, StateGraph

from app.nodes.assessment_summary_node import assessment_summary_node
from app.nodes.compatibility_assessment_node import compatibility_assessment_node
from app.nodes.dependency_node import dependency_node
from app.nodes.project_context_node import project_context_node
from app.state import AgentState

workflow = StateGraph(AgentState)
workflow.add_node("dependency_node", dependency_node)
workflow.add_node("project_context_node", project_context_node)
workflow.add_node("compatibility_assessment_node", compatibility_assessment_node)
workflow.add_node("assessment_summary_node", assessment_summary_node)
workflow.add_edge(START, "project_context_node")
workflow.add_edge("project_context_node", "dependency_node")
workflow.add_edge("dependency_node", "compatibility_assessment_node")
workflow.add_edge("compatibility_assessment_node", "assessment_summary_node")
workflow.add_edge("assessment_summary_node", END)
dependency_analysis_graph = workflow.compile()
