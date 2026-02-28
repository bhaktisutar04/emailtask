from typing import TypedDict, List, Optional

class TaskInfo(TypedDict):
    person: str
    raw_task: str
    formal_task: str
    deadline: str
    priority: str
    confidence: float

class WorkflowState(TypedDict):
    """
    Production-grade state for Enterprise Workflow.
    """
    input_data: str              # Original messy input
    summary: Optional[str]       # Meeting core topics
    assigned_tasks: List[TaskInfo] # Structured task objects
    raw_llm_output: Optional[str] # Debugging raw output
    parsed_json: Optional[str]    # Pure JSON string for audit
    email_status: Optional[str]  # Final dispatch status
    sent_to: List[str]          # Successful recipients
    failed_to: List[str]        # Failed recipients
    history: List[str]          # Node traversal log
    errors: List[str]           # Traceback / error log
    timestamp: str              # Operation timestamp
