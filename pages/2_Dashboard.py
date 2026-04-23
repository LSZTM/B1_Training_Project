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

# ── Helpers ───────────────────────────────────────────────────────────────────
def metric_card(value: str, label: str, variant: str = "", sub: str = ""):
    sub_html = f'<div class="dg-metric-sub">{sub}</div>' if sub else ""
    st.markdown(
        f"""
        <div class="dg-metric {variant}">
            <div class="dg-metric-label">{label}</div>
            <div class="dg-metric-value">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="dg-page-header">
        <div class="dg-page-eyebrow">Executive Intelligence</div>
        <div class="dg-page-title">Health Dashboard</div>
        <div class="dg-page-desc">High-level metrics and system-wide validation status.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Data retrieval ────────────────────────────────────────────────────────────
metrics    = ValidationService.get_metrics()
records    = metrics.get("records_scanned", 0)
errors     = metrics.get("errors", 0)
rules      = metrics.get("rules", 0)
minutes    = metrics.get("minutes_ago", 0)
error_rate = min(100.0, errors / max(records, 1) * 100)
integrity_score = 100.0 - error_rate

health       = "Healthy"  if error_rate < 1 else "Warning"  if error_rate < 5 else "Critical"
health_var   = "success"  if health == "Healthy" else "warning" if health == "Warning" else "error"
error_var    = "success"  if errors == 0 else "warning" if errors < 50 else "error"
rate_var     = "success"  if error_rate < 1 else "warning" if error_rate < 5 else "error"

# ── System Health ─────────────────────────────────────────────────────────────
st.header("Real-time Pulse", divider=True)

c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1: 
    st.metric("Loaded Rules", str(rules))
    st.caption("Active validation definitions")
with c2: 
    st.metric("Total Issues", f"{errors:,}")
    st.caption("Across database")
with c3: 
    st.metric("Last Check", f"{minutes}m ago")
    st.caption("Time since execution")
with c4: 
    st.metric("Integrity Score", f"{integrity_score:.1f}%")
    st.caption("Overall data quality")

st.markdown("<br>", unsafe_allow_html=True)

# ── Insights ──────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Deep Insights</div>', unsafe_allow_html=True)

col_chart_l, col_chart_r = st.columns(2, gap="large")

with col_chart_l:
    st.markdown("#### Failures by Context")
    table_summary = ValidationService.get_error_summary_by_table()
    if not table_summary.empty:
        # Use an interactive Plotly bar chart
        fig_bar = px.bar(
            table_summary, 
            x="table_name", 
            y="error_count",
            color_discrete_sequence=["#6366f1"],
            labels={"table_name": "Context", "error_count": "Failures"}
        )
        fig_bar.update_layout(
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis_title=None,
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
        st.caption("Distribution of detected errors across different tables.")
    else:
        st.markdown(
            """
            <div class="dg-card" style="height: 200px; display: flex; align-items: center; justify-content: center;">
                <span style="color: var(--success);">All contexts are healthy.</span>
            </div>
            """,
            unsafe_allow_html=True
        )

with col_chart_r:
    st.markdown("#### Quality Over Time")
    trend_df = ValidationService.get_error_trend(days=14)
    if not trend_df.empty:
        # Use an interactive Plotly area chart
        fig_area = px.area(
            trend_df,
            x="run_timestamp",
            y="error_rate",
            color_discrete_sequence=["#06b6d4"],
            labels={"run_timestamp": "Time", "error_rate": "Error Rate %"}
        )
        fig_area.update_layout(
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis_title=None,
        )
        st.plotly_chart(fig_area, use_container_width=True, config={"displayModeBar": False})
        st.caption("Error rate progression based on latest batch runs.")
    else:
        st.markdown(
            """
            <div class="dg-card" style="height: 200px; display: flex; align-items: center; justify-content: center;">
                <span style="color: var(--text-muted);">Awaiting baseline data.</span>
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Recent activity ───────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Critical Alerts</div>', unsafe_allow_html=True)

recent_errors = ValidationService.get_recent_errors(5)
if not recent_errors.empty:
    for _, row in recent_errors.iterrows():
        st.markdown(
            f"""
            <div class="dg-card" style="padding: 12px 18px; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid var(--danger);">
                <div>
                    <span style="font-weight: 600; color: var(--text-primary);">{row['table_name']}.{row['failed_field']}</span>
                    <span style="font-size: 0.75rem; color: var(--text-muted); margin-left: 10px;">ID: {row['record_identifier']}</span>
                </div>
                <div class="dg-badge error">{row['error_code']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    st.markdown(
        """
        <div class="dg-badge success" style="padding: 12px 20px;">
            System-wide pass. No critical failures detected in recent scans.
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Quick Actions ─────────────────────────────────────────────────────────────
_, btn_col, _ = st.columns([1, 1, 1])
with btn_col:
    if st.button("Recalculate Now", type="primary", use_container_width=True):
        ValidationService.run_all_validations()
        st.rerun()
