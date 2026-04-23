from components.sidebar import render_sidebar
render_sidebar()

import streamlit as st
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
        <div class="dg-page-eyebrow">Onboarding</div>
        <div class="dg-page-title">Welcome to DataGuard</div>
        <div class="dg-page-desc">The modern standard for enterprise data validation and quality operations.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Hero Section ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="dg-card" style="padding: 40px; background: linear-gradient(135deg, var(--bg-raised) 0%, var(--bg-elevated) 100%); border-color: var(--accent);">
        <h2 style="font-family: var(--font-display); color: var(--text-primary); margin-bottom: 16px;">Secure, Validate, and Monitor.</h2>
        <p style="font-size: 1.1rem; color: var(--text-secondary); line-height: 1.6; max-width: 800px;">
            DataGuard is a comprehensive validation platform designed to ensure the integrity of your SQL datasets. 
            Automate quality checks, detect anomalies in real-time, and maintain a high-fidelity data ecosystem 
            with professional-grade tooling.
        </p>
        <div style="margin-top: 32px; display: flex; gap: 16px;">
            <div class="dg-badge success" style="padding: 8px 16px; font-size: 0.8rem;">Production Ready</div>
            <div class="dg-badge info" style="padding: 8px 16px; font-size: 0.8rem;">SQL Server Native</div>
            <div class="dg-badge neutral" style="padding: 8px 16px; font-size: 0.8rem;">Real-time Logs</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Steps / Workflow ──────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Core Workflow</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4, gap="medium")

with c1:
    st.markdown(
        """
        <div class="dg-card" style="height: 100%; text-align: center; padding: 30px 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 20px; color: var(--accent);">01</div>
            <div class="dg-card-title">Connect & Discover</div>
            <p style="font-size: 0.82rem; color: var(--text-muted);">
                Link your SQL Server instance and let DataGuard profile your schema and detect data types.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        """
        <div class="dg-card" style="height: 100%; text-align: center; padding: 30px 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 20px; color: var(--accent);">02</div>
            <div class="dg-card-title">Define Rules</div>
            <p style="font-size: 0.82rem; color: var(--text-muted);">
                Use the Rule Manager to set constraints, from simple range checks to complex business logic.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        """
        <div class="dg-card" style="height: 100%; text-align: center; padding: 30px 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 20px; color: var(--accent);">03</div>
            <div class="dg-card-title">Execute Validation</div>
            <p style="font-size: 0.82rem; color: var(--text-muted);">
                Run validations on-demand or schedule them. DataGuard handles the heavy lifting directly in SQL.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        """
        <div class="dg-card" style="height: 100%; text-align: center; padding: 30px 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 20px; color: var(--accent);">04</div>
            <div class="dg-card-title">Analyze Results</div>
            <p style="font-size: 0.82rem; color: var(--text-muted);">
                Drill into failures, export logs, and monitor trends through the executive dashboard.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Call to Action ────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Get Started</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2, gap="medium")

with c1:
    with st.container(border=True):
        st.markdown("### System Health")
        st.write("View the high-level dashboard to see current error rates and active rule counts.")
        if st.button("Go to Dashboard", type="primary", use_container_width=True):
            st.switch_page("pages/2_Dashboard.py")

with c2:
    with st.container(border=True):
        st.markdown("### Run a Validation")
        st.write("Ready to check your data? Select your tables and run the engine now.")
        if st.button("Execute Now", use_container_width=True):
            st.switch_page("pages/3_Execute.py")

st.markdown("<br>", unsafe_allow_html=True)

# ── Help / Documentation Placeholder ──────────────────────────────────────────
with st.expander("How does the validation engine work?", expanded=False):
    st.markdown(
        """
        The DataGuard engine translates your high-level rules into optimized T-SQL queries. 
        These queries run directly on your database server to minimize network overhead. 
        Failures are recorded in the `error_log` table with specific identifiers, allowing 
        for precise remediation.
        """
    )

with st.expander("Who is this platform for?", expanded=False):
    st.markdown(
        """
        - **Data Engineers**: For enforcing schema integrity during ETL.
        - **Quality Analysts**: For identifying anomalies in business-critical datasets.
        - **Product Managers**: For monitoring the health of the live production environment.
        """
    )
