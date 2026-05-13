from __future__ import annotations

from statistics import mean
from typing import Any, Dict, List

from .data_access import clean_record, find_one, load_table
from .state import WarrantyState


def _split_causes(text: str) -> List[str]:
    return [item.strip() for item in str(text).split(";") if item.strip()]


def _keyword_score(text: str, keywords: str) -> int:
    haystack = text.lower()
    return sum(1 for k in str(keywords).split(";") if k.strip().lower() in haystack)


def claim_intake_node(state: WarrantyState) -> WarrantyState:
    """Load a claim either by selected_claim_id or use fields already supplied in state."""
    if state.get("claim_id"):
        return state

    selected_claim_id = state.get("selected_claim_id")
    if not selected_claim_id:
        raise ValueError("Provide selected_claim_id or direct claim fields.")

    claims = load_table("warranty_claims.csv")
    row = find_one(claims, claim_id=selected_claim_id)
    if not row:
        raise ValueError(f"Claim ID not found in sample dataset: {selected_claim_id}")

    updated: WarrantyState = dict(state)
    updated.update(clean_record(row))
    return updated


def system_classifier_node(state: WarrantyState) -> WarrantyState:
    """Classify the claim into vehicle system, subsystem, design owner, and supplier."""
    part_master = load_table("part_master.csv")
    part = find_one(part_master, noun_code=state["noun_code"])

    fault_codes = load_table("fault_codes.csv")
    fault = find_one(fault_codes, fault_code=state["fault_code"])

    updated: WarrantyState = dict(state)

    if part:
        updated.update(
            {
                "vehicle_system": part["vehicle_system"],
                "subsystem": part["subsystem"],
                "supplier": part["supplier"],
                "design_owner": part["design_owner"],
                "criticality": part["criticality"],
            }
        )
    elif fault:
        updated.update(
            {
                "vehicle_system": fault["system"],
                "subsystem": fault["subsystem"],
                "supplier": "Unknown",
                "design_owner": "Unknown",
                "criticality": "Unknown",
            }
        )
    else:
        updated.update(
            {
                "vehicle_system": "Unknown",
                "subsystem": "Unknown",
                "supplier": "Unknown",
                "design_owner": "Unknown",
                "criticality": "Unknown",
            }
        )

    return updated


def fault_code_interpreter_node(state: WarrantyState) -> WarrantyState:
    """Translate fault code into simple engineering meaning."""
    fault_codes = load_table("fault_codes.csv")
    fault = find_one(fault_codes, fault_code=state["fault_code"])

    updated: WarrantyState = dict(state)

    if fault:
        updated["fault_code_meaning"] = fault["fault_meaning"]
        updated["likely_causes"] = _split_causes(fault["likely_causes"])
        updated["severity"] = fault["severity"]
    else:
        updated["fault_code_meaning"] = "Fault code not found in local sample knowledge base."
        updated["likely_causes"] = []
        updated["severity"] = "Unknown"

    return updated


def historical_pattern_node(state: WarrantyState) -> WarrantyState:
    """Detect similar claim patterns based on model, year, noun code, and fault code."""
    claims = load_table("warranty_claims.csv")

    peer_claims = claims[
        (claims["vehicle_model"].astype(str) == str(state["vehicle_model"]))
        & (claims["model_year"].astype(str) == str(state["model_year"]))
        & (claims["noun_code"].astype(str) == str(state["noun_code"]))
    ]

    same_fault = peer_claims[peer_claims["fault_code"].astype(str) == str(state["fault_code"])]

    if same_fault.empty:
        same_fault = peer_claims

    mileage_values = [float(x) for x in same_fault["mileage"].tolist()]
    repair_values = [float(x) for x in same_fault["repair_cost_usd"].tolist()]
    repeat_vins = (
        same_fault["vin"].value_counts()[same_fault["vin"].value_counts() > 1].to_dict()
        if "vin" in same_fault
        else {}
    )

    pattern = {
        "similar_claim_count": int(len(same_fault)),
        "average_failure_mileage": round(mean(mileage_values), 0) if mileage_values else None,
        "min_failure_mileage": int(min(mileage_values)) if mileage_values else None,
        "max_failure_mileage": int(max(mileage_values)) if mileage_values else None,
        "average_repair_cost_usd": round(mean(repair_values), 2) if repair_values else None,
        "repeat_vins": repeat_vins,
        "trend_signal": "High" if len(same_fault) >= 4 else "Medium" if len(same_fault) >= 2 else "Low",
        "peer_claim_ids": same_fault["claim_id"].astype(str).tolist(),
    }

    updated: WarrantyState = dict(state)
    updated["historical_patterns"] = pattern
    return updated


def engineering_context_node(state: WarrantyState) -> WarrantyState:
    """Retrieve simple structured context from service interval and root-cause KB CSVs."""
    service = load_table("service_intervals.csv")
    interval = find_one(
        service,
        vehicle_make=state["vehicle_make"],
        vehicle_model=state["vehicle_model"],
        model_year=state["model_year"],
        noun_code=state["noun_code"],
    )

    kb = load_table("root_cause_knowledge_base.csv")
    rows = kb[
        (kb["part_name"].astype(str).str.lower() == str(state["part_name"]).lower())
        | (kb["subsystem"].astype(str).str.lower() == str(state.get("subsystem", "")).lower())
    ]

    context: List[Dict[str, Any]] = []

    if interval:
        context.append(
            {
                "source": "service_intervals.csv",
                "type": "Service Interval",
                "evidence": (
                    f"OEM interval for {interval['part_name']} is "
                    f"{int(interval['oem_service_interval_miles']):,} miles. "
                    f"Recommended action: {interval['recommended_action']}."
                ),
                "data": clean_record(interval),
            }
        )

    claim_text = " ".join(
        [
            str(state.get("complaint", "")),
            str(state.get("cause", "")),
            str(state.get("correction", "")),
            str(state.get("technician_comment", "")),
        ]
    )

    for _, row in rows.iterrows():
        score = _keyword_score(claim_text, row["evidence_keywords"])
        if score > 0 or str(row["part_name"]).lower() == str(state["part_name"]).lower():
            context.append(
                {
                    "source": "root_cause_knowledge_base.csv",
                    "type": "Engineering Knowledge",
                    "evidence": (
                        f"Known failure mode: {row['failure_mode']}. "
                        f"Suspected root causes: {row['suspected_root_causes']}. "
                        f"Recommended tests: {row['recommended_tests']}."
                    ),
                    "keyword_match_score": score,
                    "data": clean_record(row.to_dict()),
                }
            )

    updated: WarrantyState = dict(state)
    updated["engineering_context"] = context
    return updated


def root_cause_node(state: WarrantyState) -> WarrantyState:
    """Generate ranked root-cause hypotheses based on evidence."""
    text = " ".join(
        [
            str(state.get("complaint", "")),
            str(state.get("cause", "")),
            str(state.get("correction", "")),
            str(state.get("technician_comment", "")),
        ]
    ).lower()

    hypotheses = []

    for context in state.get("engineering_context", []):
        data = context.get("data", {})
        if context.get("type") == "Engineering Knowledge":
            score = context.get("keyword_match_score", 0)
            confidence = "High" if score >= 3 else "Medium" if score >= 1 else "Low"
            hypotheses.append(
                {
                    "hypothesis": data.get("failure_mode", "Known failure mode"),
                    "suspected_root_causes": data.get("suspected_root_causes", ""),
                    "supporting_evidence": context.get("evidence", ""),
                    "recommended_tests": data.get("recommended_tests", ""),
                    "confidence": confidence,
                }
            )

    if not hypotheses:
        likely_causes = state.get("likely_causes", [])
        hypotheses.append(
            {
                "hypothesis": likely_causes[0] if likely_causes else "Further diagnosis required",
                "suspected_root_causes": "; ".join(likely_causes),
                "supporting_evidence": "Generated from fault code meaning and technician comments.",
                "recommended_tests": "Validate fault code, component condition, wiring, and operating context.",
                "confidence": "Low",
            }
        )

    # Add a service gap hypothesis if failure occurs much earlier than service interval.
    pattern = state.get("historical_patterns", {})
    avg_mileage = pattern.get("average_failure_mileage")
    service_context = next((c for c in state.get("engineering_context", []) if c.get("type") == "Service Interval"), None)
    if service_context and avg_mileage:
        interval = int(service_context["data"]["oem_service_interval_miles"])
        if avg_mileage < interval * 0.75:
            hypotheses.append(
                {
                    "hypothesis": "Service interval gap / preventive maintenance opportunity",
                    "suspected_root_causes": (
                        f"Failures are appearing around {int(avg_mileage):,} miles, "
                        f"well before the OEM interval of {interval:,} miles."
                    ),
                    "supporting_evidence": "Historical claims mileage is materially lower than service interval.",
                    "recommended_tests": "Validate sample size, duty cycle, supplier lot, and maintenance history before campaign launch.",
                    "confidence": "High" if pattern.get("similar_claim_count", 0) >= 4 else "Medium",
                }
            )

    updated: WarrantyState = dict(state)
    updated["root_cause_hypotheses"] = hypotheses
    return updated


def preventive_intelligence_node(state: WarrantyState) -> WarrantyState:
    """Calculate preventive inspection recommendation and estimated saving."""
    pattern = state.get("historical_patterns", {})
    avg_mileage = pattern.get("average_failure_mileage")
    avg_repair_cost = pattern.get("average_repair_cost_usd") or state.get("repair_cost_usd")

    service_context = next((c for c in state.get("engineering_context", []) if c.get("type") == "Service Interval"), None)

    if not service_context or not avg_mileage:
        recommendation = {
            "status": "Not enough data",
            "message": "Service interval or historical pattern is missing.",
        }
    else:
        interval = int(service_context["data"]["oem_service_interval_miles"])
        inspection_cost = float(service_context["data"]["inspection_cost_usd"])
        recommended_action = service_context["data"]["recommended_action"]

        recommended_inspection = max(5000, int((avg_mileage * 0.8) // 5000) * 5000)
        gap_miles = int(interval - avg_mileage)
        estimated_prevention_saving = round(float(avg_repair_cost) - inspection_cost, 2)

        if avg_mileage < interval:
            status = "Action recommended"
            rationale = (
                f"Actual failures are appearing around {int(avg_mileage):,} miles, "
                f"while the current service interval is {interval:,} miles."
            )
        else:
            status = "Monitor"
            rationale = "Failures are not clearly earlier than the service interval."

        recommendation = {
            "status": status,
            "rationale": rationale,
            "recommended_action": recommended_action,
            "recommended_inspection_mileage": recommended_inspection,
            "current_service_interval_miles": interval,
            "average_failure_mileage": int(avg_mileage),
            "risk_gap_miles": gap_miles,
            "inspection_cost_usd": inspection_cost,
            "average_repair_cost_usd": avg_repair_cost,
            "estimated_prevention_saving_per_vehicle_usd": estimated_prevention_saving,
            "confidence": "High" if pattern.get("similar_claim_count", 0) >= 4 else "Medium",
        }

    updated: WarrantyState = dict(state)
    updated["preventive_recommendation"] = recommendation
    return updated


def human_review_node(state: WarrantyState) -> WarrantyState:
    """Human approval point. Auto-approve by default for easy demo runs."""
    updated: WarrantyState = dict(state)

    if state.get("auto_approve", True):
        updated["approval_status"] = "Auto-approved for demo"
        return updated

    if state.get("human_decision"):
        updated["approval_status"] = state["human_decision"]
        return updated

    from langgraph.types import interrupt

    decision = interrupt(
        {
            "question": "Approve the preventive recommendation?",
            "claim_id": state.get("claim_id"),
            "recommendation": state.get("preventive_recommendation"),
            "options": ["Approve", "Ask for more evidence", "Reject", "Escalate to engineering"],
        }
    )
    updated["approval_status"] = str(decision)
    return updated


def report_node(state: WarrantyState) -> WarrantyState:
    """Create the final report in markdown format."""
    pattern = state.get("historical_patterns", {})
    rec = state.get("preventive_recommendation", {})
    hypotheses = state.get("root_cause_hypotheses", [])

    hypothesis_lines = []
    for idx, item in enumerate(hypotheses, start=1):
        hypothesis_lines.append(
            f"{idx}. **{item.get('hypothesis', 'Hypothesis')}** "
            f"({item.get('confidence', 'Unknown')} confidence)\n"
            f"   - Root cause view: {item.get('suspected_root_causes', '')}\n"
            f"   - Evidence: {item.get('supporting_evidence', '')}\n"
            f"   - Recommended tests: {item.get('recommended_tests', '')}"
        )

    report = f"""# Warranty Investigation Report

## 1. Claim Summary
- Claim ID: {state.get('claim_id')}
- VIN: {state.get('vin')}
- Vehicle: {state.get('model_year')} {state.get('vehicle_make')} {state.get('vehicle_model')}
- Mileage: {int(state.get('mileage', 0)):,} miles
- Application: {state.get('application')}
- Geography: {state.get('geography')}
- Complaint: {state.get('complaint')}
- Technician Comment: {state.get('technician_comment')}

## 2. Vehicle System Navigation
- Vehicle System: {state.get('vehicle_system')}
- Sub-system: {state.get('subsystem')}
- Noun Code: {state.get('noun_code')}
- Part: {state.get('part_name')}
- Supplier: {state.get('supplier')}
- Design Owner: {state.get('design_owner')}
- Criticality: {state.get('criticality')}

## 3. Fault Code Interpretation
- Fault Code: {state.get('fault_code')}
- Meaning: {state.get('fault_code_meaning')}
- Likely Causes: {', '.join(state.get('likely_causes', []))}
- Severity: {state.get('severity')}

## 4. Historical Pattern
- Similar Claim Count: {pattern.get('similar_claim_count')}
- Average Failure Mileage: {int(pattern.get('average_failure_mileage') or 0):,} miles
- Failure Mileage Range: {pattern.get('min_failure_mileage')} to {pattern.get('max_failure_mileage')} miles
- Average Repair Cost: ${pattern.get('average_repair_cost_usd')}
- Repeat VINs: {pattern.get('repeat_vins')}
- Trend Signal: {pattern.get('trend_signal')}
- Peer Claims: {', '.join(pattern.get('peer_claim_ids', []))}

## 5. Root Cause Hypotheses
{chr(10).join(hypothesis_lines)}

## 6. Preventive Intelligence Recommendation
- Status: {rec.get('status')}
- Rationale: {rec.get('rationale', rec.get('message', ''))}
- Recommended Action: {rec.get('recommended_action')}
- Recommended Inspection Mileage: {rec.get('recommended_inspection_mileage')} miles
- Current Service Interval: {rec.get('current_service_interval_miles')} miles
- Risk Gap: {rec.get('risk_gap_miles')} miles
- Inspection Cost: ${rec.get('inspection_cost_usd')}
- Average Repair Cost: ${rec.get('average_repair_cost_usd')}
- Estimated Prevention Saving per Vehicle: ${rec.get('estimated_prevention_saving_per_vehicle_usd')}
- Confidence: {rec.get('confidence')}

## 7. Approval Status
{state.get('approval_status', 'Pending')}

## 8. Recommended Next Action
Validate this recommendation with engineering, supplier quality, service operations, and a statistically larger claim population before launching a field campaign.
"""

    updated: WarrantyState = dict(state)
    updated["final_report"] = report
    return updated
