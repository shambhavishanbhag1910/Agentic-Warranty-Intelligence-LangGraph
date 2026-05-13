import argparse
from pathlib import Path

from langgraph.types import Command

from warranty_agent.data_access import OUTPUTS_DIR
from warranty_agent.graph import create_graph


def main():
    parser = argparse.ArgumentParser(description="Run LangGraph warranty investigation demo.")
    parser.add_argument("--claim-id", default="C-1001", help="Claim ID from data/warranty_claims.csv")
    parser.add_argument("--human", action="store_true", help="Pause for human approval using LangGraph interrupt.")
    parser.add_argument("--thread-id", default="demo-thread-1", help="LangGraph checkpoint thread ID.")
    parser.add_argument("--output", default=None, help="Optional markdown report path.")
    args = parser.parse_args()

    graph = create_graph()
    config = {"configurable": {"thread_id": args.thread_id}}

    initial_state = {
        "selected_claim_id": args.claim_id,
        "auto_approve": not args.human,
    }

    result = graph.invoke(initial_state, config=config)

    if "__interrupt__" in result:
        interrupt_value = result["__interrupt__"][0].value
        print("\nHuman review required:")
        print(interrupt_value)
        decision = input("\nEnter decision [Approve / Ask for more evidence / Reject / Escalate to engineering]: ")
        result = graph.invoke(Command(resume=decision), config=config)

    report = result["final_report"]

    output_path = Path(args.output) if args.output else OUTPUTS_DIR / f"{args.claim_id}_report.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print(report)
    print(f"\nSaved report to: {output_path}")


if __name__ == "__main__":
    main()
