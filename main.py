import streamlit as st
import time
from utils.styles import load_css
from components.sidebar import render_sidebar
from utils.db import test_connection, list_databases, switch_database, discover_server_connection, get_available_drivers

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
    "db_setup_mode": False,
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
        result = test_connection()
        st.session_state.connected = result.get("success", False)
        time.sleep(0.25)

    loader.empty()
    st.session_state.boot_complete = True
    st.query_params["init"] = "done"
    st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# DATABASE SETUP / PICKER — shown when not connected or user requests change
# ──────────────────────────────────────────────────────────────────────────────
if not st.session_state.connected or st.session_state.get("db_setup_mode"):
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

    st.markdown(
        """
        <div style="display:flex;align-items:center;justify-content:center;padding-top:40px;">
          <div style="max-width:580px;width:100%;">
            <div style="text-align:center;margin-bottom:32px;">
                <div class="dg-page-title" style="font-size:1.8rem;margin-bottom:6px;">Data<span style="color:var(--accent);">Guard</span></div>
                <div class="dg-page-desc">Connect to a SQL Server instance and choose which database to validate.</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Connection Form ───────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("#### Server Connection")

        c1, c2 = st.columns(2)
        with c1:
            server_input = st.text_input(
                "Server Address",
                value=st.session_state.get("db_selected_server", "localhost\\SQLEXPRESS"),
                placeholder="e.g. localhost\\SQLEXPRESS or my-server.database.windows.net",
                help="Hostname or IP of your SQL Server instance.",
            )
        with c2:
            available_drivers = get_available_drivers()
            driver_input = st.selectbox(
                "ODBC Driver",
                options=available_drivers if available_drivers else ["{ODBC Driver 17 for SQL Server}", "{SQL Server}"],
                help="Select the ODBC driver installed on this machine.",
            )

        auth_mode = st.radio(
            "Authentication",
            ["Windows Authentication (Trusted)", "SQL Server Authentication (Username/Password)"],
            horizontal=True,
            help="Use Windows Auth for local development; SQL Auth for remote/cloud servers.",
        )

        username_input = None
        password_input = None
        if "SQL Server" in auth_mode:
            c3, c4 = st.columns(2)
            with c3:
                username_input = st.text_input("Username", placeholder="sa")
            with c4:
                password_input = st.text_input("Password", type="password")

        # ── Discover Databases ────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### Select Database")

        databases = []
        server_error = None

        try:
            master_conn_str = discover_server_connection(
                server=server_input,
                driver=driver_input,
                username=username_input,
                password=password_input,
            )
            databases = list_databases(server_conn_str=master_conn_str)
        except ConnectionError as e:
            server_error = str(e)

        if server_error:
            st.error(f"Could not reach server: {server_error}")
            st.caption("Check that your SQL Server is running and the address is correct.")
        elif not databases:
            st.warning("Connected to server, but no user databases found.")
        else:
            st.success(f"Found **{len(databases)}** databases on `{server_input}`")

            selected_db = st.selectbox(
                "Choose a database to validate",
                options=databases,
                index=databases.index(st.session_state.get("db_selected_database", databases[0]))
                    if st.session_state.get("db_selected_database") in databases else 0,
            )

            _, btn_col, _ = st.columns([2, 2, 2])
            with btn_col:
                if st.button("Connect & Launch", type="primary", use_container_width=True):
                    try:
                        switch_database(
                            database=selected_db,
                            server=server_input,
                            driver=driver_input,
                            username=username_input,
                            password=password_input,
                        )
                        st.session_state.connected = True
                        st.session_state.db_setup_mode = False
                        st.session_state.redirected = False
                        st.rerun()
                    except ConnectionError as e:
                        st.error(f"Failed: {e}")

    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# REDIRECT (once, no flash)
# ──────────────────────────────────────────────────────────────────────────────
if not st.session_state.redirected:
    st.session_state.redirected = True
    st.switch_page("pages/1_Overview.py")
