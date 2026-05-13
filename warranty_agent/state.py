from typing import Any, Dict, List, Optional, TypedDict


class WarrantyState(TypedDict, total=False):
    selected_claim_id: str
    auto_approve: bool
    human_decision: str

    claim_id: str
    vin: str
    claim_date: str
    vehicle_make: str
    vehicle_model: str
    model_year: int
    mileage: int
    application: str
    geography: str
    fault_code: str
    noun_code: str
    part_name: str
    complaint: str
    cause: str
    correction: str
    repair_cost_usd: float
    technician_comment: str

    vehicle_system: str
    subsystem: str
    supplier: str
    design_owner: str
    criticality: str

    fault_code_meaning: str
    likely_causes: List[str]
    severity: str

    historical_patterns: Dict[str, Any]
    engineering_context: List[Dict[str, Any]]
    root_cause_hypotheses: List[Dict[str, Any]]
    preventive_recommendation: Dict[str, Any]

    approval_status: str
    final_report: str
