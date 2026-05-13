import pandas as pd
import streamlit as st

from warranty_agent.data_access import DATA_DIR, OUTPUTS_DIR
from warranty_agent.graph import create_graph


st.set_page_config(page_title="Agentic Warranty Intelligence", layout="wide")

st.title("Agentic Warranty Investigation & Preventive Intelligence")
st.caption("LangGraph demo using sample warranty claims, fault codes, service intervals, and root-cause knowledge base.")

claims = pd.read_csv(DATA_DIR / "warranty_claims.csv")
claim_ids = claims["claim_id"].tolist()

left, right = st.columns([1, 2])

with left:
    selected_claim_id = st.selectbox("Select sample claim", claim_ids, index=0)
    approval = st.selectbox(
        "Human approval decision",
        ["Approve", "Ask for more evidence", "Reject", "Escalate to engineering"],
        index=0,
    )
    run_button = st.button("Run LangGraph Investigation", type="primary")

    st.subheader("Sample Claim Data")
    st.dataframe(claims[claims["claim_id"] == selected_claim_id].T, use_container_width=True)

with right:
    if run_button:
        graph = create_graph()
        state = {
            "selected_claim_id": selected_claim_id,
            "auto_approve": True,
            "human_decision": approval,
        }
        result = graph.invoke(state, config={"configurable": {"thread_id": f"streamlit-{selected_claim_id}"}})
        st.success("Investigation completed.")
        st.markdown(result["final_report"])

        output_path = OUTPUTS_DIR / f"{selected_claim_id}_streamlit_report.md"
        output_path.write_text(result["final_report"], encoding="utf-8")

        st.download_button(
            "Download Markdown Report",
            data=result["final_report"],
            file_name=f"{selected_claim_id}_warranty_report.md",
            mime="text/markdown",
        )
    else:
        st.info("Select a claim and run the investigation.")
