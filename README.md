# LangGraph Predictive Warranty Agent

An end-to-end LangGraph project for warranty claim investigation, vehicle system mapping, fault-code interpretation, root-cause hypothesis generation, and preventive maintenance intelligence.

## Business Use Case

OEM warranty teams receive large claim volumes. Engineers manually review complaints, technician comments, fault codes, noun codes, service intervals, and historical patterns. This project demonstrates how a stateful LangGraph workflow can convert claim data into a structured investigation report.

## What This Project Does

For a selected warranty claim, the workflow:

1. Loads claim details from sample warranty data.
2. Maps the failure to vehicle system, subsystem, noun code, part, supplier, and design owner.
3. Interprets the fault code in simple engineering language.
4. Finds similar historical claims and average failure mileage.
5. Retrieves service interval and engineering root-cause context.
6. Generates root-cause hypotheses with confidence.
7. Compares actual failure mileage with OEM service interval.
8. Recommends proactive inspection mileage and estimated cost saving.
9. Supports a human approval node.
10. Creates a markdown investigation report.

## Architecture

```text
Claim Intake
   ↓
System Classifier
   ↓
Fault Code Interpreter
   ↓
Historical Pattern Analyzer
   ↓
Engineering Context Retriever
   ↓
Root Cause Analyzer
   ↓
Preventive Intelligence Engine
   ↓
Human Review
   ↓
Final Report Generator
```

## Sample Datasets Included

| File | Purpose |
|---|---|
| data/warranty_claims.csv | Sample claim records with complaint, fault code, noun code, mileage, cost, comments |
| data/fault_codes.csv | Fault-code meaning and likely causes |
| data/service_intervals.csv | OEM service interval and inspection cost |
| data/part_master.csv | Noun code to system, subsystem, supplier, design owner |
| data/root_cause_knowledge_base.csv | Failure modes, evidence keywords, recommended tests |

## Setup

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Mac/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run CLI Demo

```bash
python main.py --claim-id C-1001
```

Run with human interrupt approval:

```bash
python main.py --claim-id C-1001 --human
```

Try other claim IDs:

```bash
python main.py --claim-id C-1006
python main.py --claim-id C-1009
python main.py --claim-id C-1011
python main.py --claim-id C-1013
```

## Run Streamlit UI

```bash
streamlit run streamlit_app.py
```

## Example Output

For claim `C-1001`, the system should identify:

- Vehicle system: Engine
- Subsystem: Ignition System
- Part: Spark Plug
- Fault code: P0302, Cylinder 2 misfire
- Average failure mileage: around 31,640 miles
- OEM service interval: 60,000 miles
- Preventive recommendation: inspect around 25,000 miles
- Estimated prevention saving: average repair cost minus inspection cost

## Resume Bullet

Built an Agentic Warranty Investigation System using LangGraph to automate claim intake, vehicle system mapping, fault-code interpretation, historical failure pattern detection, root-cause hypothesis generation, human review, and preventive maintenance recommendations using structured sample warranty data.

## Suggested Extensions

- Add LLM-based reasoning using OpenAI, Gemini, or Claude.
- Add vector database retrieval using FAISS or Chroma.
- Add PDF service manual ingestion.
- Add RAGAS evaluation for retrieval quality.
- Add FastAPI endpoint for enterprise integration.
- Add database storage using PostgreSQL.
- Deploy on AWS EC2, Render, or Azure App Service.
