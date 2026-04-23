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
        <div class="dg-page-eyebrow">Health Dashboard</div>
        <div class="dg-page-title">Last validation health, held still.</div>
        <div class="dg-page-desc">A sparse view of coverage, failure rate, and rule pressure across the connected SQL Server database.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

metrics = ValidationService.get_metrics()
records = metrics.get("records_scanned", 0)
errors = metrics.get("errors", 0)
rules = metrics.get("rules", 0)
minutes = metrics.get("minutes_ago", 0)
error_rate = min(100.0, errors / max(records, 1) * 100)
integrity_score = max(0.0, 100.0 - error_rate)

hero_col, detail_col = st.columns([1.35, 1], gap="large")
with hero_col:
    st.markdown(
        f"""
        <div class="dg-metric hero">
            <div class="dg-metric-label">Last 24h validation health</div>
            <div class="dg-metric-value">{integrity_score:.1f}%</div>
            <div class="dg-metric-sub">{errors:,} failures across {records:,} scanned records</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with detail_col:
    rows = [
        ("Active rules", f"{rules:,}", "state-neutral", "Rules available to the validation engine"),
        ("Failure rate", f"{error_rate:.2f}%", "state-pass" if error_rate < 1 else "state-warn" if error_rate < 5 else "state-fail", "Share of scanned records with errors"),
        ("Last run age", f"{minutes}m", "state-neutral", "Minutes since latest validation history entry"),
    ]
    for label, value, state, meta in rows:
        st.markdown(
            f"""
            <div class="dg-row {state}">
                <div class="dg-row-title">{label}: {value}</div>
                <div class="dg-row-meta">{meta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<div class="dg-section-label">Validation shape</div>', unsafe_allow_html=True)

chart_l, chart_r = st.columns(2, gap="large")

with chart_l:
    st.markdown("### Rule failures per table")
    table_summary = ValidationService.get_error_summary_by_table()
    if not table_summary.empty:
        fig_bar = px.bar(
            table_summary,
            x="table_name",
            y="error_count",
            labels={"table_name": "Table", "error_count": "Rule failures"},
        )
        fig_bar.update_traces(marker_color=JAPANDI_COLORS["terracotta"])
        apply_japandi_plotly_theme(fig_bar, accent=JAPANDI_COLORS["terracotta"])
        fig_bar.update_layout(xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown('<div class="dg-empty">No table-level failures are present in the current database.</div>', unsafe_allow_html=True)

with chart_r:
    st.markdown("### Pass/fail quality trend")
    trend_df = ValidationService.get_error_trend(days=14)
    if not trend_df.empty:
        trend_df = trend_df.copy()
        trend_df["run_timestamp"] = pd.to_datetime(trend_df["run_timestamp"])
        fig_area = px.area(
            trend_df,
            x="run_timestamp",
            y="error_rate",
            labels={"run_timestamp": "Run time", "error_rate": "Failure rate %"},
        )
        fig_area.update_traces(line_color=JAPANDI_COLORS["ochre"], fillcolor="rgba(195,154,87,0.14)")
        apply_japandi_plotly_theme(fig_area, accent=JAPANDI_COLORS["ochre"])
        fig_area.update_layout(xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_area, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown('<div class="dg-empty">Awaiting enough validation history to draw a trend.</div>', unsafe_allow_html=True)

st.markdown('<div class="dg-section-label">Needs attention</div>', unsafe_allow_html=True)

recent_errors = ValidationService.get_recent_errors(5)
if not recent_errors.empty:
    for _, row in recent_errors.iterrows():
        st.markdown(
            f"""
            <div class="dg-row state-fail">
                <div class="dg-row-title">{row['table_name']}.{row['failed_field']} failed {row['error_code']}</div>
                <div class="dg-row-meta">Record {row['record_identifier']} needs validation review</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        """
        <div class="dg-row state-pass">
            <div class="dg-row-title">No recent rule failures detected</div>
            <div class="dg-row-meta">A clean validation result should feel this quiet.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

_, action_col, _ = st.columns([1, 1, 1])
with action_col:
    if st.button("Run validation refresh", type="primary", use_container_width=True):
        with st.spinner("Running validations... this may take a moment."):
            ValidationService.run_all_validations()
        st.rerun()
