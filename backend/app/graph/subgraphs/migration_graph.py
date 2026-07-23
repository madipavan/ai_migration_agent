from langgraph.graph import START, StateGraph, END


from app.nodes.project_context_node import project_context_node
from app.nodes.assessment_summary_node import assessment_summary_node
from app.nodes.compatibility_assessment_node import compatibility_assessment_node
from app.nodes.migrate_dependecy_file_node import migrate_dependecy_file_node
from app.nodes.migration_node import migration_node
from app.nodes.migration_planner_node import migration_planner_node
from app.nodes.dependency_node import dependency_node
from app.state import AgentState

migration_workflow = StateGraph(AgentState)
migration_workflow.add_node("project_context_node", project_context_node)
migration_workflow.add_node(
    "compatibility_assessment_node", compatibility_assessment_node
)
migration_workflow.add_node("assessment_summary_node", assessment_summary_node)
migration_workflow.add_node("migrate_dependecy_file_node", migrate_dependecy_file_node)
migration_workflow.add_node("migration_planner_node", migration_planner_node)
migration_workflow.add_node("migration_node", migration_node)
migration_workflow.add_node("dependency_node", dependency_node)

migration_workflow.add_edge(START, "project_context_node")
migration_workflow.add_edge("project_context_node", "dependency_node")
migration_workflow.add_edge("dependency_node", "compatibility_assessment_node")
migration_workflow.add_edge("compatibility_assessment_node", "migration_planner_node")


migration_graph = migration_workflow.compile()
