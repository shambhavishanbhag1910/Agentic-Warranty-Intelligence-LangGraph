from warranty_agent.nodes import (
    claim_intake_node,
    engineering_context_node,
    fault_code_interpreter_node,
    historical_pattern_node,
    preventive_intelligence_node,
    report_node,
    root_cause_node,
    system_classifier_node,
)


def test_node_workflow_without_langgraph():
    state = {"selected_claim_id": "C-1001", "auto_approve": True}
    for node in [
        claim_intake_node,
        system_classifier_node,
        fault_code_interpreter_node,
        historical_pattern_node,
        engineering_context_node,
        root_cause_node,
        preventive_intelligence_node,
    ]:
        state = node(state)

    state["approval_status"] = "Auto-approved for test"
    state = report_node(state)

    assert state["vehicle_system"] == "Engine"
    assert state["subsystem"] == "Ignition System"
    assert state["preventive_recommendation"]["status"] == "Action recommended"
    assert "Warranty Investigation Report" in state["final_report"]
