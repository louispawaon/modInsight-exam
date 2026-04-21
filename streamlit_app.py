from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from receipt_intel.ui import get_config_snapshot, health_check, run_evaluation, run_ingest, run_query

st.set_page_config(page_title="Receipt Intelligence", page_icon="🧾", layout="wide")

EXAMPLE_QUERIES = [
    "How much did I spend in December 2023?",
    "Find all Whole Foods receipts",
    "Find all grocery receipts over $50 in December",
    "What's my average grocery bill?",
]


def _init_state() -> None:
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("latest_result", None)
    st.session_state.setdefault("status_banner", "")
    st.session_state.setdefault("query_text", "")


def _render_sidebar() -> None:
    st.sidebar.header("System")
    config = get_config_snapshot()
    health = health_check()

    st.sidebar.subheader("Config")
    st.sidebar.json(config)

    st.sidebar.subheader("Health")
    st.sidebar.write(f"Ollama: {'✅' if health['ollama_ok'] else '❌'}")
    st.sidebar.write(f"Qdrant path exists: {'✅' if health['qdrant_exists'] else '❌'}")
    st.sidebar.write(f"Manifest exists: {'✅' if health['manifest_exists'] else '❌'}")

    if st.sidebar.button("Ingest / Reindex", type="primary"):
        with st.spinner("Running ingestion and indexing..."):
            try:
                stats = run_ingest()
                st.session_state["status_banner"] = (
                    f"Ingest complete in {stats['elapsed_s']}s "
                    f"(manifest: {stats['manifest_path']})"
                )
            except Exception as exc:
                st.session_state["status_banner"] = f"Ingest failed: {exc}"


def _render_query_tab() -> None:
    st.subheader("Query")
    cols = st.columns(len(EXAMPLE_QUERIES))
    for idx, example in enumerate(EXAMPLE_QUERIES):
        if cols[idx].button(example, key=f"example_{idx}"):
            st.session_state["query_text"] = example

    query = st.text_input("Ask a question about receipts", key="query_text")

    if st.button("Run Query", type="primary") and query.strip():
        with st.spinner("Running query..."):
            try:
                normalized_query = query.strip()
                result = run_query(normalized_query)
                st.session_state["latest_result"] = result
                st.session_state["history"].append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "query": normalized_query,
                        "answer": result["answer"],
                    }
                )
            except Exception as exc:
                st.error(f"Query failed: {exc}")
                return

    result = st.session_state.get("latest_result")
    if not result:
        st.info("Run a query to see results.")
        return

    st.markdown("### Answer")
    # Use plain-text rendering to prevent markdown/LaTeX parsing of currency.
    st.text(result["answer"])
    st.caption(f"Answer mode: {result.get('answer_mode', 'deterministic')}")
    retrieval_meta = result.get("retrieval", {})
    st.caption(
        "Intent family: "
        f"{retrieval_meta.get('intent_family', 'unknown')} | "
        f"Evidence quality: {retrieval_meta.get('evidence_quality', 'unknown')}"
    )

    totals = result.get("totals", {})
    m1, m2, m3 = st.columns(3)
    m1.metric("Sum", f"${totals.get('sum', 0.0):.2f}")
    m2.metric("Avg", f"${totals.get('avg', 0.0):.2f}")
    m3.metric("Count", f"{int(totals.get('count', 0.0))}")

    st.markdown("### Evidence")
    evidence_rows = result.get("evidence_rows", [])
    if evidence_rows:
        st.dataframe(evidence_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No evidence rows returned.")

    with st.expander("Debug: Intent and Retrieval"):
        st.json(
            {
                "answer_mode": result.get("answer_mode", "deterministic"),
                "facts": result.get("facts", {}),
                "intent": result.get("intent", {}),
                "retrieval": result.get("retrieval", {}),
                "matched_receipts": result.get("matched_receipts", []),
                "matched_chunks": result.get("matched_chunks", []),
            }
        )

    with st.expander("Debug: Raw Result JSON"):
        st.code(json.dumps(result, indent=2), language="json")

    st.markdown("### Query History")
    if st.session_state["history"]:
        st.dataframe(st.session_state["history"], use_container_width=True, hide_index=True)
    else:
        st.caption("No history yet.")


def _render_eval_tab() -> None:
    st.subheader("Evaluation")
    st.caption("Runs scenario-driven checks and reports pass/fail by scenario.")
    if st.button("Run Coverage Smoke Pack"):
        with st.spinner("Running full coverage smoke scenarios..."):
            try:
                report = run_evaluation()
                st.session_state["eval_report"] = report
            except Exception as exc:
                st.error(f"Evaluation failed: {exc}")
                return
    if st.button("Run Evaluation", type="primary"):
        with st.spinner("Running evaluation scenarios..."):
            try:
                report = run_evaluation()
                st.session_state["eval_report"] = report
            except Exception as exc:
                st.error(f"Evaluation failed: {exc}")
                return

    report = st.session_state.get("eval_report")
    if not report:
        st.info("Run evaluation to see report.")
        return

    summary = report.get("summary", {})
    a, b, c = st.columns(3)
    a.metric("Total", summary.get("total", 0))
    b.metric("Passed", summary.get("passed", 0))
    c.metric("Failed", summary.get("failed", 0))

    st.dataframe(report.get("scenarios", []), use_container_width=True, hide_index=True)
    st.download_button(
        "Download eval report JSON",
        data=json.dumps(report, indent=2),
        file_name="eval_results_streamlit.json",
        mime="application/json",
    )


def main() -> None:
    _init_state()
    _render_sidebar()

    st.title("Receipt Intelligence UI")
    if st.session_state.get("status_banner"):
        st.info(st.session_state["status_banner"])

    tab_query, tab_eval = st.tabs(["Query", "Evaluation"])
    with tab_query:
        _render_query_tab()
    with tab_eval:
        _render_eval_tab()


if __name__ == "__main__":
    main()

