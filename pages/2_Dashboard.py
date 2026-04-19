from components.sidebar import render_sidebar
render_sidebar()

import streamlit as st
import pandas as pd
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

health       = "Healthy"  if error_rate < 1 else "Warning"  if error_rate < 5 else "Critical"
health_var   = "success"  if health == "Healthy" else "warning" if health == "Warning" else "error"
error_var    = "success"  if errors == 0 else "warning" if errors < 50 else "error"
rate_var     = "success"  if error_rate < 1 else "warning" if error_rate < 5 else "error"

# ── System Health ─────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Real-time Pulse</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1: metric_card(str(rules),           "Loaded Rules",   "",         "active validation definitions")
with c2: metric_card(f"{errors:,}",        "Total Issues",   error_var,  "across database")
with c3: metric_card(f"{minutes}m ago",    "Last Heartbeat",       "",         "engine execution time")
with c4: metric_card(f"{error_rate:.1f}%", "Integrity Score",     rate_var,   "pass/fail ratio")

st.markdown("<br>", unsafe_allow_html=True)

# ── Insights ──────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Deep Insights</div>', unsafe_allow_html=True)

col_chart_l, col_chart_r = st.columns(2, gap="large")

with col_chart_l:
    st.markdown("#### Failures by Context")
    table_summary = ValidationService.get_error_summary_by_table()
    if not table_summary.empty:
        # Use a more visually appealing bar chart
        st.bar_chart(table_summary.set_index("table_name")["error_count"], color="#6366f1")
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
        st.area_chart(trend_df.set_index("run_timestamp")["error_rate"], color="#06b6d4")
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
            ✓ System-wide pass. No critical failures detected in recent scans.
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
