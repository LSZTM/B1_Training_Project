import time

import streamlit as st

from components.sidebar import render_sidebar
from utils.db import (
    discover_server_connection,
    get_available_drivers,
    list_databases,
    requires_sql_auth,
    switch_database,
    test_connection,
)
from utils.styles import load_css


st.set_page_config(
    page_title="DataGuard - Validation Console",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()

defaults = {
    "boot_complete": False,
    "connected": False,
    "redirected": False,
    "db_setup_mode": False,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


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
              <div class="dg-loader-card">
                <div class="dg-loader-title">Data<span>Guard</span></div>
                <div class="dg-card-copy">Preparing a quiet workspace for SQL Server validation.</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        progress = st.progress(0)
        status = st.empty()
        steps = [
            ("Reading validation rules", 24),
            ("Preparing database connection", 48),
            ("Opening observability surfaces", 72),
            ("Settling the workspace", 100),
        ]

        for label, percent in steps:
            status.markdown(f'<p class="dg-loader-step">{label}</p>', unsafe_allow_html=True)
            progress.progress(percent)
            time.sleep(0.32)

        result = test_connection()
        st.session_state.connected = result.get("success", False)
        time.sleep(0.18)

    loader.empty()
    st.session_state.boot_complete = True
    st.query_params["init"] = "done"
    st.rerun()


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
        <div class="dg-page-header">
            <div class="dg-page-eyebrow">First connection</div>
            <div class="dg-page-title">Choose the database to keep in view.</div>
            <div class="dg-page-desc">DataGuard validates SQL Server data through rules, run history, and structured operational logs.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown("### Server")
        c1, c2 = st.columns(2)
        with c1:
            server_input = st.text_input(
                "Server address",
                value=st.session_state.get("db_selected_server", "localhost\\SQLEXPRESS"),
                placeholder="localhost\\SQLEXPRESS",
            )
        with c2:
            available_drivers = get_available_drivers()
            driver_input = st.selectbox(
                "ODBC driver",
                options=available_drivers if available_drivers else ["{ODBC Driver 17 for SQL Server}", "{SQL Server}"],
            )

        remote_requires_sql_auth = requires_sql_auth(server_input)
        auth_mode = st.radio(
            "Authentication",
            ["Windows Authentication (Trusted)", "SQL Server Authentication (Username/Password)"],
            index=1 if remote_requires_sql_auth else 0,
            horizontal=True,
            help="Ngrok TCP endpoints require SQL Server Authentication; Windows Authentication only works for local/domain-reachable SQL Server instances.",
        )

        username_input = None
        password_input = None
        if remote_requires_sql_auth and "Windows Authentication" in auth_mode:
            st.warning("Ngrok TCP endpoints require SQL Server Authentication. Use the SQL login configured on the SQL Server host.")

        if "SQL Server" in auth_mode:
            c3, c4 = st.columns(2)
            with c3:
                username_input = st.text_input("Username", placeholder="sa")
            with c4:
                password_input = st.text_input("Password", type="password")

        st.markdown('<div class="dg-section-label">Database</div>', unsafe_allow_html=True)

        databases = []
        server_error = None
        try:
            if remote_requires_sql_auth and "Windows Authentication" in auth_mode:
                server_error = "Select SQL Server Authentication for ngrok TCP endpoints."
            elif "SQL Server" in auth_mode and (not username_input or not password_input):
                server_error = "Enter both username and password to list databases."
            else:
                master_conn_str = discover_server_connection(
                    server=server_input,
                    driver=driver_input,
                    username=username_input,
                    password=password_input,
                )
                databases = list_databases(server_conn_str=master_conn_str)
        except ConnectionError as exc:
            server_error = str(exc)

        if server_error:
            st.error(f"Could not reach server: {server_error}")
            st.caption("Check that SQL Server is running and the address is correct.")
        elif not databases:
            st.warning("Connected to the server, but no user databases were found.")
        else:
            st.markdown(f'<span class="dg-badge success">{len(databases)} databases found</span>', unsafe_allow_html=True)
            selected_db = st.selectbox(
                "Choose a database",
                options=databases,
                index=databases.index(st.session_state.get("db_selected_database", databases[0]))
                if st.session_state.get("db_selected_database") in databases
                else 0,
            )

            _, btn_col, _ = st.columns([2, 2, 2])
            with btn_col:
                if st.button("Open DataGuard", type="primary", use_container_width=True):
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
                    except ConnectionError as exc:
                        st.error(f"Failed: {exc}")

    st.stop()


render_sidebar()

if not st.session_state.redirected:
    st.session_state.redirected = True
    st.switch_page("pages/1_Welcome.py")
