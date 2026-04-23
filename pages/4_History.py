from components.sidebar import render_sidebar
render_sidebar()

import streamlit as st
import pandas as pd
import plotly.express as px
from services.validation_service import ValidationService
from utils.styles import load_css

load_css()

# ── Connection guard ──────────────────────────────────────────────────────────
if "connected" not in st.session_state:
    st.session_state.connected = False
if not st.session_state.get("boot_complete", False):
    st.stop()

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="dg-page-header">
        <div class="dg-page-eyebrow">Observability</div>
        <div class="dg-page-title">Results & History</div>
        <div class="dg-page-desc">Inspect past validation runs, drill into specific failures, and monitor data quality trends.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_runs, tab_explorer, tab_trends = st.tabs(["Run History", "Error Explorer", "Quality Trends"])

# ── TAB 1: Run History ────────────────────────────────────────────────────────
with tab_runs:
    st.markdown('<div class="dg-section-label">Validation Log</div>', unsafe_allow_html=True)
    
    runs = ValidationService.get_run_history(limit=50)
    if not runs.empty:
        st.dataframe(
            runs, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "run_id": "Run ID",
                "table_name": "Context",
                "column_name": "Field",
                "rule_code": "Rule",
                "total_records_scanned": "Scanned",
                "total_errors": "Errors",
                "status": "Status",
                "run_timestamp": "Timestamp"
            }
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Run Inspector
        st.markdown('<div class="dg-section-label">Run Inspector</div>', unsafe_allow_html=True)
        run_ids = runs["run_id"].tolist()
        selected_run_id = st.selectbox("Select a run to inspect details", options=run_ids, label_visibility="collapsed")
        
        if selected_run_id:
            with st.expander(f"Details for Run #{selected_run_id}", expanded=True):
                details = ValidationService.get_run_details(selected_run_id)
                if details:
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Status", details.get("status", "Unknown").upper())
                    c2.metric("Scanned", f"{details.get('records_scanned', 0):,}")
                    c3.metric("Errors", f"{details.get('total_errors', 0):,}")
                    c4.metric("Duration", f"{details.get('duration_ms', 0):,} ms")
                    
                    st.markdown("#### Rule Results Breakdown")
                    rule_results = ValidationService.get_rule_results(selected_run_id)
                    if not rule_results.empty:
                        st.dataframe(rule_results, use_container_width=True, hide_index=True)
                    else:
                        st.caption("No per-rule results available for this run.")
    else:
        st.info("No validation runs found. Go to 'Run Validations' to start your first check.")

# ── TAB 2: Error Explorer ─────────────────────────────────────────────────────
with tab_explorer:
    st.markdown('<div class="dg-section-label">Filter Errors</div>', unsafe_allow_html=True)
    
    tables = ValidationService.get_tables()
    code_ref = ValidationService.get_error_code_reference()
    
    f1, f2, f3 = st.columns(3)
    sel_table = f1.selectbox("Table", ["All"] + tables, key="history_table")
    
    cols = ValidationService.get_columns(None if sel_table == "All" else sel_table)
    sel_col = f2.selectbox("Column", ["All"] + cols, key="history_col")
    
    codes = code_ref["error_code"].tolist() if not code_ref.empty else []
    sel_code = f3.selectbox("Error Code", ["All"] + codes, key="history_code")
    
    errors = ValidationService.get_filtered_errors(
        table=None if sel_table == "All" else sel_table,
        column=None if sel_col == "All" else sel_col,
        error_code=None if sel_code == "All" else sel_code
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="dg-section-label">Identified Anomalies</div>', unsafe_allow_html=True)
    
    if not errors.empty:
        st.dataframe(errors, use_container_width=True, hide_index=True)
        
        csv = errors.to_csv(index=False).encode('utf-8')
        st.download_button("Download Filtered Results (CSV)", data=csv, file_name="validation_errors.csv", mime="text/csv")
    else:
        st.markdown(
            """
            <div class="dg-card" style="text-align: center; padding: 40px;">
                <h3 style="color: var(--success);">No errors found</h3>
                <p style="color: var(--text-muted);">Data is pristine for the current selection.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# ── TAB 3: Quality Trends ─────────────────────────────────────────────────────
with tab_trends:
    st.markdown('<div class="dg-section-label">Time-Series Analysis</div>', unsafe_allow_html=True)
    
    trend_df = ValidationService.get_error_trend(days=30)
    if not trend_df.empty:
        # Convert timestamp to something readable
        trend_df["run_timestamp"] = pd.to_datetime(trend_df["run_timestamp"])
        
        st.markdown("#### Global Error Rate Trend")
        fig_line = px.line(
            trend_df,
            x="run_timestamp",
            y="error_rate",
            color_discrete_sequence=["#6366f1"],
            labels={"run_timestamp": "Time", "error_rate": "Error Rate %"},
            markers=True
        )
        fig_line.update_layout(margin=dict(l=0, r=0, t=10, b=0), xaxis_title=None)
        st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
        
        st.markdown("#### Table Breakdown")
        table_impact = ValidationService.get_error_summary_by_table()
        if not table_impact.empty:
            fig_bar = px.bar(
                table_impact,
                x="table_name",
                y="error_count",
                color_discrete_sequence=["#06b6d4"],
                labels={"table_name": "Context", "error_count": "Failures"}
            )
            fig_bar.update_layout(margin=dict(l=0, r=0, t=10, b=0), xaxis_title=None)
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Insufficient data to generate trends. Run more validations to see patterns.")
