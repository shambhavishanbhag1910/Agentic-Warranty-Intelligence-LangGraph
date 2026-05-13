from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .nodes import (
    claim_intake_node,
    engineering_context_node,
    fault_code_interpreter_node,
    historical_pattern_node,
    human_review_node,
    preventive_intelligence_node,
    report_node,
    root_cause_node,
    system_classifier_node,
)
from .state import WarrantyState


def create_graph(checkpointer=None):
    """Create and compile the LangGraph warranty investigation workflow."""
    builder = StateGraph(WarrantyState)

    builder.add_node("claim_intake", claim_intake_node)
    builder.add_node("system_classifier", system_classifier_node)
    builder.add_node("fault_code_interpreter", fault_code_interpreter_node)
    builder.add_node("historical_pattern", historical_pattern_node)
    builder.add_node("engineering_context", engineering_context_node)
    builder.add_node("root_cause", root_cause_node)
    builder.add_node("preventive_intelligence", preventive_intelligence_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("report", report_node)

    builder.set_entry_point("claim_intake")
    builder.add_edge("claim_intake", "system_classifier")
    builder.add_edge("system_classifier", "fault_code_interpreter")
    builder.add_edge("fault_code_interpreter", "historical_pattern")
    builder.add_edge("historical_pattern", "engineering_context")
    builder.add_edge("engineering_context", "root_cause")
    builder.add_edge("root_cause", "preventive_intelligence")
    builder.add_edge("preventive_intelligence", "human_review")
    builder.add_edge("human_review", "report")
    builder.add_edge("report", END)

    return builder.compile(checkpointer=checkpointer or MemorySaver())
