import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div class="dg-brand">
                <div class="dg-brand-logo">Data<span>Guard</span></div>
                <div class="dg-brand-tag">Validation Console</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        connected = st.session_state.get("connected", False)
        status_class = "verified" if connected else "locked"
        status_text = "Connected" if connected else "Disconnected"

        # Dynamic database label
        db_label = st.session_state.get("db_selected_database", "No database link")
        server_label = st.session_state.get("db_selected_server", "")
        if not connected:
            db_label = "No database link"

        st.markdown(
            f"""
            <div class="dg-status {status_class}">
                <div class="dg-status-dot"></div>
                <div>
                    <div style="font-weight:500;">{status_text}</div>
                    <div style="opacity:0.6;font-size:0.65rem;margin-top:1px;">{db_label}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if connected and server_label:
            st.caption(f"Server: `{server_label}`")

        st.markdown('<div class="dg-nav-label">Navigation</div>', unsafe_allow_html=True)

        pages = [
            ("Quick Start", "pages/1_Welcome.py"),
            ("Health Dashboard", "pages/2_Dashboard.py"),
            ("Run Validations", "pages/3_Execute.py"),
            ("Results & History", "pages/4_History.py"),
            ("Rule Manager", "pages/5_Rules.py"),
            ("Operational Logs", "pages/6_Logs.py"),
        ]

        for label, path in pages:
            if st.button(label, use_container_width=True, key=f"nav_{path}"):
                st.switch_page(path)

        try:
            from services.validation_service import ValidationService

            rule_values = ValidationService.get_error_codes()
            rule_count = len(rule_values) if rule_values else 0
            context_count = 0
        except Exception:
            rule_count, context_count = 0, 0

        st.markdown(
            f"""
            <div class="dg-registry">
                <div class="dg-registry-label">Rule Registry</div>
                <div class="dg-registry-stats">
                    <div>
                        <div class="dg-registry-stat-val">{rule_count}</div>
                        <div class="dg-registry-stat-key">Rules</div>
                    </div>
                    <div>
                        <div class="dg-registry-stat-val">{context_count}</div>
                        <div class="dg-registry-stat-key">Contexts</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="dg-nav-label">System</div>', unsafe_allow_html=True)

        if st.button("Change Database", use_container_width=True):
            st.session_state.db_setup_mode = True
            st.session_state.redirected = False
            st.switch_page("main.py")

        if st.button("Refresh App", use_container_width=True):
            st.rerun()

        if st.button("Reconnect DB", use_container_width=True):
            st.session_state.boot_complete = False
            st.rerun()
