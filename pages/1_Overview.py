from components.sidebar import render_sidebar
render_sidebar()

import streamlit as st
import pandas as pd
import altair as alt
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


def run_validations():
    with st.spinner("Executing validation rules…"):
        result = ValidationService.run_all_validations()
        if result.get("success"):
            errors  = result.get("total_errors", 0)
            records = result.get("records_scanned", 0)
            st.success(f"Complete · {errors:,} errors across {records:,} records")
        else:
            st.error(result.get("error", "Validation failed"))
    st.rerun()


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="dg-page-header">
        <div class="dg-page-eyebrow">Executive Dashboard</div>
        <div class="dg-page-title">System Overview</div>
        <div class="dg-page-desc">Real-time health metrics and validation activity across all contexts.</div>
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

# ─────────────────────────────────────────────────────────────────────────────
# ROW 1 — System Health
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">System Health</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1: metric_card(str(rules),           "Active Rules",   "",         "validation rules loaded")
with c2: metric_card(f"{errors:,}",        "Total Errors",   error_var,  "across all tables")
with c3: metric_card(f"{minutes}m ago",    "Last Run",       "",         "most recent execution")
with c4: metric_card(f"{error_rate:.1f}%", "Error Rate",     rate_var,   "errors / records")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 2 — Volume + Overall Status
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Volume & Status</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2, gap="medium")
with c1: metric_card(f"{records:,}", "Records Scanned", "", "total rows evaluated")
with c2: metric_card(health,         "System Health",   health_var, f"error rate {error_rate:.2f}%")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 3 — Quick Actions
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Quick Actions</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 1, 2], gap="medium")
with c1:
    if st.button("▶  Run Validations", type="primary", use_container_width=True):
        run_validations()
with c2:
    if st.button("↺  Refresh Data", use_container_width=True):
        st.rerun()
with c3:
    st.markdown(
        f"""
        <div class="dg-card" style="padding:14px 18px;margin:0;">
            <span class="dg-badge {health_var}">{health}</span>
            <span style="font-size:0.8rem;color:var(--text-muted);margin-left:10px;">
                {rules} rules active · last scan {minutes}m ago
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 4 — Insights
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Insights</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2, gap="medium")

with c1:
    st.markdown(
        '<div class="dg-card-title" style="margin-bottom:12px;">Errors by Table</div>',
        unsafe_allow_html=True,
    )
    table_summary = ValidationService.get_error_summary_by_table()
    if not table_summary.empty:
        chart = alt.Chart(table_summary).mark_bar(
            cornerRadiusTopLeft=4,
            cornerRadiusTopRight=4,
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='#6366f1', offset=0),
                       alt.GradientStop(color='#818cf8', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X('table_name:N', title='Table', sort='-y', axis=alt.Axis(labelAngle=-45, labelColor='#94a3b8', titleColor='#475569')),
            y=alt.Y('error_count:Q', title='Errors', axis=alt.Axis(labelColor='#94a3b8', titleColor='#475569')),
            tooltip=['table_name', 'error_count', 'affected_records']
        ).configure_view(
            strokeOpacity=0
        ).properties(height=240)
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.markdown(
            '<div class="dg-badge success">No error data available</div>',
            unsafe_allow_html=True,
        )

with c2:
    st.markdown(
        '<div class="dg-card-title" style="margin-bottom:12px;">Error Rate Trend</div>',
        unsafe_allow_html=True,
    )
    trend_df = ValidationService.get_error_trend(days=14)

    trend_direction = "stable"
    trend_badge = "neutral"
    if len(trend_df) >= 3:
        last_three = trend_df.tail(3)["error_rate"].astype(float).tolist()
        if last_three[0] < last_three[1] < last_three[2]:
            trend_direction = "degrading"
            trend_badge = "error"
        elif last_three[0] > last_three[1] > last_three[2]:
            trend_direction = "improving"
            trend_badge = "success"

    st.markdown(
        f'<span class="dg-badge {trend_badge}" style="margin-bottom:10px;display:inline-block;">Trend: {trend_direction}</span>',
        unsafe_allow_html=True,
    )

    if trend_df.empty:
        st.caption("No run history available for trend window.")
    else:
        chart_df = trend_df.copy()
        chart_df["run_timestamp"] = pd.to_datetime(chart_df["run_timestamp"])
        
        line = alt.Chart(chart_df).mark_area(
            line={'color': '#6366f1', 'strokeWidth': 2},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='rgba(99, 102, 241, 0.2)', offset=0),
                       alt.GradientStop(color='rgba(99, 102, 241, 0)', offset=1)],
                x1=1, x2=1, y1=0, y2=1
            )
        ).encode(
            x=alt.X('run_timestamp:T', title='Time', axis=alt.Axis(labelColor='#94a3b8', titleColor='#475569')),
            y=alt.Y('error_rate:Q', title='Error Rate', axis=alt.Axis(labelColor='#94a3b8', titleColor='#475569', format='.1%')),
            tooltip=['run_timestamp', alt.Tooltip('error_rate', format='.2%')]
        ).configure_view(
            strokeOpacity=0
        ).properties(height=240)
        
        st.altair_chart(line, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 5 — Latest Errors
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Latest Errors</div>', unsafe_allow_html=True)

recent_errors = ValidationService.get_recent_errors(10)
if not recent_errors.empty:
    st.dataframe(recent_errors, use_container_width=True, hide_index=True)
else:
    st.markdown(
        '<div class="dg-badge success" style="font-size:0.8rem;padding:8px 14px;">✓ No validation errors found</div>',
        unsafe_allow_html=True,
    )
