from components.sidebar import render_sidebar

render_sidebar()

import streamlit as st

from services.validation_service import ValidationService
from utils.styles import load_css


load_css()

if "connected" not in st.session_state:
    st.session_state.connected = False
if not st.session_state.get("boot_complete", False):
    st.stop()

db_name = st.session_state.get("db_selected_database", "Current database")
server_name = st.session_state.get("db_selected_server", "SQL Server")

st.markdown(
    """
    <div class="dg-page-header">
        <div class="dg-page-eyebrow">Welcome</div>
        <div class="dg-page-title">A quieter way to validate SQL Server data.</div>
        <div class="dg-page-desc">DataGuard runs rule-based checks, records failures, and keeps validation activity traceable from run to log.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

metrics = ValidationService.get_metrics()
rules = metrics.get("rules", 0)
errors = metrics.get("errors", 0)
records = metrics.get("records_scanned", 0)

hero_col, side_col = st.columns([1.45, 1], gap="large")

with hero_col:
    st.markdown(
        f"""
        <div class="dg-metric hero">
            <div class="dg-metric-label">Current validation room</div>
            <div class="dg-metric-value">{db_name}</div>
            <div class="dg-metric-sub">{server_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with side_col:
    st.markdown(
        """
        <div class="dg-card">
            <div class="dg-card-title">Next step</div>
            <div class="dg-card-copy">Choose a scope, confirm the ruleset, then let DataGuard write the evidence into run history and operational logs.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Begin validations", type="primary", use_container_width=True):
        st.switch_page("pages/3_Execute.py")

st.markdown('<div class="dg-section-label">At rest</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3, gap="medium")
with c1:
    st.markdown(
        f"""
        <div class="dg-metric">
            <div class="dg-metric-label">Active rule codes</div>
            <div class="dg-metric-value">{rules:,}</div>
            <div class="dg-metric-sub">available to the engine</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""
        <div class="dg-metric">
            <div class="dg-metric-label">Records scanned</div>
            <div class="dg-metric-value">{records:,}</div>
            <div class="dg-metric-sub">from recent validation history</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c3:
    state = "state-pass" if errors == 0 else "state-fail"
    st.markdown(
        f"""
        <div class="dg-row {state}" style="min-height:122px;">
            <div class="dg-card-title">Known failures</div>
            <div class="dg-metric-value" style="font-size:2.15rem;">{errors:,}</div>
            <div class="dg-row-meta">Open Results & History to inspect rule failures per table.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<div class="dg-section-label">Path</div>', unsafe_allow_html=True)

p1, p2, p3 = st.columns(3, gap="medium")
for col, number, title, copy in [
    (p1, "01", "Run", "Select tables and rulesets with only the needed options."),
    (p2, "02", "Inspect", "Read validation runs, grouped failures, and quality trends."),
    (p3, "03", "Trace", "Use structured logs to follow a validation journey end to end."),
]:
    with col:
        st.markdown(
            f"""
            <div class="dg-card">
                <div class="dg-step-index">{number}</div>
                <div class="dg-step-title">{title}</div>
                <div class="dg-card-copy" style="margin-top:10px;">{copy}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<div class="dg-section-label">Useful rooms</div>', unsafe_allow_html=True)

a1, a2 = st.columns(2, gap="medium")
with a1:
    st.markdown(
        """
        <div class="dg-card compact">
            <div class="dg-card-title">Health Dashboard</div>
            <div class="dg-card-copy">A single view of validation health, coverage, failures, and trends.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("View dashboard", use_container_width=True):
        st.switch_page("pages/2_Dashboard.py")

with a2:
    st.markdown(
        """
        <div class="dg-card compact">
            <div class="dg-card-title">Operational Logs</div>
            <div class="dg-card-copy">A live ledger for validation events, severity filters, and structured drill-down.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open logs", use_container_width=True):
        st.switch_page("pages/6_Logs.py")
