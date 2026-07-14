from langgraph.graph import StateGraph, START, END

from app.state import AgentState
from app.nodes.chat_node import chat_node

workflow = StateGraph(AgentState)

workflow.add_node("chat_node", chat_node)

workflow.add_edge(START, "chat_node")
workflow.add_edge("chat_node", END)

chat_graph = workflow.compile()
