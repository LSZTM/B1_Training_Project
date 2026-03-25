import streamlit as st
import time
from utils.styles import load_css
from components.sidebar import render_sidebar
import test_connection

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataGuard — Validation Console",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load design system first (prevents FOUC)
load_css()

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE BOOTSTRAP
# ──────────────────────────────────────────────────────────────────────────────
defaults = {
    "boot_complete": False,
    "connected":     False,
    "redirected":    False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ──────────────────────────────────────────────────────────────────────────────
# BOOT SCREEN — hide chrome while loading
# ──────────────────────────────────────────────────────────────────────────────
if not st.session_state.boot_complete:
    st.markdown(
        """
        <style>
            header, [data-testid="stSidebar"], [data-testid="stSidebarNav"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    loader = st.empty()
    with loader.container():
        st.markdown(
            """
            <div class="dg-loader-wrap">
                <div class="dg-loader-title">Data<span>Guard</span></div>
                <div class="dg-spinner"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        progress = st.progress(0)
        status   = st.empty()

        steps = [
            ("Initialising rule engine",       20),
            ("Loading validation modules",     40),
            ("Preparing analytics engine",     60),
            ("Establishing database link",     80),
            ("Finalising services",           100),
        ]

        for label, pct in steps:
            status.markdown(
                f'<p class="dg-loader-step">— {label}</p>',
                unsafe_allow_html=True,
            )
            progress.progress(pct)
            time.sleep(0.42)

        # Database handshake
        result = test_connection.test_connection()
        st.session_state.connected = result.get("success", False)
        time.sleep(0.25)

    loader.empty()
    st.session_state.boot_complete = True
    st.query_params["init"] = "done"
    st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# CONNECTION FAILURE WALL
# ──────────────────────────────────────────────────────────────────────────────
if not st.session_state.connected:
    st.markdown(
        """
        <div style="display:flex;align-items:center;justify-content:center;min-height:60vh;">
          <div class="dg-card" style="max-width:480px;text-align:center;">
            <div style="font-size:1.6rem;margin-bottom:12px;">⬡</div>
            <div class="dg-page-title" style="margin-bottom:8px;">Connection Failed</div>
            <div class="dg-page-desc" style="margin-bottom:20px;">
              Unable to reach <code>QUERY_PRACTICE</code>.<br>
              Verify database availability and retry.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col = st.columns([1, 2, 1])[1]
    with col:
        if st.button("Retry Connection", type="primary", use_container_width=True):
            st.session_state.boot_complete = False
            st.rerun()

    st.stop()



# ──────────────────────────────────────────────────────────────────────────────
# REDIRECT (once, no flash)
# ──────────────────────────────────────────────────────────────────────────────
if not st.session_state.redirected:
    st.session_state.redirected = True
    st.switch_page("pages/1_Overview.py")