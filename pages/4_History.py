from components.sidebar import render_sidebar

render_sidebar()

import pandas as pd
import plotly.express as px
import streamlit as st

from services.validation_service import ValidationService
from utils.styles import JAPANDI_COLORS, apply_japandi_plotly_theme, load_css


load_css()

if "connected" not in st.session_state:
    st.session_state.connected = False
if not st.session_state.get("boot_complete", False):
    st.stop()

st.markdown(
    """
    <div class="dg-page-header">
        <div class="dg-page-eyebrow">Results & History</div>
        <div class="dg-page-title">Read the record of what the rules found.</div>
        <div class="dg-page-desc">Validation run history, grouped rule failures, and pass/fail trends for the connected SQL Server database.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_runs, tab_explorer, tab_trends = st.tabs(["Run Log", "Error Explorer", "Quality Trends"])

with tab_runs:
    st.markdown('<div class="dg-section-label">Data validation runs</div>', unsafe_allow_html=True)

    runs = ValidationService.get_run_history(limit=50)
    if not runs.empty:
        st.dataframe(
            runs,
            use_container_width=True,
            hide_index=True,
            column_config={
                "run_id": "Run ID",
                "table_name": "Table",
                "column_name": "Column",
                "rule_code": "Rule",
                "total_records_scanned": "Scanned",
                "total_errors": "Failures",
                "status": "Status",
                "run_timestamp": "Timestamp",
            },
        )

        st.markdown('<div class="dg-section-label">Run inspector</div>', unsafe_allow_html=True)
        run_ids = runs["run_id"].tolist()
        selected_run_id = st.selectbox("Select a run", options=run_ids, label_visibility="collapsed")

        if selected_run_id:
            details = ValidationService.get_run_details(selected_run_id)
            if details:
                c1, c2, c3, c4 = st.columns(4, gap="small")
                for col, label, value in [
                    (c1, "Status", str(details.get("status", "Unknown")).upper()),
                    (c2, "Scanned", f"{details.get('records_scanned', 0):,}"),
                    (c3, "Failures", f"{details.get('total_errors', 0):,}"),
                    (c4, "Duration", f"{details.get('duration_ms', 0):,} ms"),
                ]:
                    with col:
                        st.markdown(
                            f"""
                            <div class="dg-metric">
                                <div class="dg-metric-label">{label}</div>
                                <div class="dg-metric-value" style="font-size:1.6rem;">{value}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                st.markdown("### Rule result ledger")
                rule_results = ValidationService.get_rule_results(selected_run_id)
                if not rule_results.empty:
                    st.dataframe(rule_results, use_container_width=True, hide_index=True)
                else:
                    st.markdown('<div class="dg-empty">No per-rule results were stored for this run.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="dg-empty">No validation runs found. Run a validation to begin the ledger.</div>', unsafe_allow_html=True)

with tab_explorer:
    st.markdown('<div class="dg-section-label">Rule failures per table</div>', unsafe_allow_html=True)

    tables = ValidationService.get_tables()
    code_ref = ValidationService.get_error_code_reference()

    f1, f2, f3 = st.columns(3)
    sel_table = f1.selectbox("Table", ["All"] + tables, key="history_table")
    cols = ValidationService.get_columns(None if sel_table == "All" else sel_table)
    sel_col = f2.selectbox("Column", ["All"] + cols, key="history_col")
    codes = code_ref["error_code"].tolist() if not code_ref.empty else []
    sel_code = f3.selectbox("Rule failure code", ["All"] + codes, key="history_code")

    errors = ValidationService.get_filtered_errors(
        table=None if sel_table == "All" else sel_table,
        column=None if sel_col == "All" else sel_col,
        error_code=None if sel_code == "All" else sel_code,
    )

    if not errors.empty:
        grouped = errors.groupby(["table_name", "failed_field", "error_code"], dropna=False).size().reset_index(name="count")
        for _, row in grouped.head(12).iterrows():
            st.markdown(
                f"""
                <div class="dg-row state-fail">
                    <div class="dg-row-title">{row['table_name']}.{row['failed_field']} - {row['error_code']}</div>
                    <div class="dg-row-meta">{row['count']:,} impacted records in the current filter</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### Failure ledger")
        st.dataframe(errors, use_container_width=True, hide_index=True)
        csv = errors.to_csv(index=False).encode("utf-8")
        st.download_button("Export filtered failures", data=csv, file_name="validation_errors.csv", mime="text/csv")
    else:
        st.markdown(
            '<div class="dg-empty">No rule failures match the current filters. The absence is part of the signal.</div>',
            unsafe_allow_html=True,
        )

with tab_trends:
    st.markdown('<div class="dg-section-label">Pass/fail quality trend</div>', unsafe_allow_html=True)

    trend_df = ValidationService.get_error_trend(days=30)
    if not trend_df.empty:
        trend_df = trend_df.copy()
        trend_df["run_timestamp"] = pd.to_datetime(trend_df["run_timestamp"])

        fig_line = px.line(
            trend_df,
            x="run_timestamp",
            y="error_rate",
            labels={"run_timestamp": "Run time", "error_rate": "Failure rate %"},
            markers=True,
        )
        apply_japandi_plotly_theme(fig_line, accent=JAPANDI_COLORS["gold"])
        fig_line.update_layout(xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="dg-section-label">Rule volatility by table</div>', unsafe_allow_html=True)
        table_impact = ValidationService.get_error_summary_by_table()
        if not table_impact.empty:
            fig_bar = px.bar(
                table_impact,
                x="table_name",
                y="error_count",
                labels={"table_name": "Table", "error_count": "Rule failures"},
            )
            fig_bar.update_traces(marker_color=JAPANDI_COLORS["terracotta"])
            apply_japandi_plotly_theme(fig_bar, accent=JAPANDI_COLORS["terracotta"])
            fig_bar.update_layout(xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown('<div class="dg-empty">Run more validations to establish a quality trend.</div>', unsafe_allow_html=True)
