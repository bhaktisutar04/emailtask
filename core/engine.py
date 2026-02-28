from langgraph.graph import StateGraph, END
from core.state import WorkflowState
from core.nodes import (
    summarize_node, 
    extract_tasks_node, 
    send_email_node
)

def build_workflow():
    """
    Builds the core project management workflow.
    summarize -> extract_tasks -> send_email -> END
    """
    builder = StateGraph(WorkflowState)

    # Register Nodes
    builder.add_node("summarize", summarize_node)
    builder.add_node("extract_tasks", extract_tasks_node)
    builder.add_node("send_email", send_email_node)

    # Define Linear Execution
    builder.set_entry_point("summarize")
    builder.add_edge("summarize", "extract_tasks")
    builder.add_edge("extract_tasks", "send_email")
    builder.add_edge("send_email", END)

    return builder.compile()
