import streamlit as st


def render_sidebar():
    with st.sidebar:

        # ── Brand ─────────────────────────────────────────────────────────────
        st.markdown(
            """
            <div class="dg-brand">
                <div class="dg-brand-logo">Data<span>Guard</span></div>
                <div class="dg-brand-tag">Validation Console</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Connection status ─────────────────────────────────────────────────
        connected = st.session_state.get("connected", False)
        status_class = "verified" if connected else "locked"
        status_text  = "Connected" if connected else "Disconnected"
        db_label     = "QUERY_PRACTICE" if connected else "No database link"

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

        # ── Navigation ────────────────────────────────────────────────────────
        st.markdown('<div class="dg-nav-label">Navigation</div>', unsafe_allow_html=True)

        pages = [
            ("Overview",    "pages/1_Overview.py"),
            ("Run Validation","pages/2_Runs.py"),
            ("Error Explorer","pages/3_Errors.py"),
            ("Validation Rules","pages/4_Rules.py"),
        ]

        current = st.query_params.get("page", "")
        for label, path in pages:
            active = "active" if path in current else ""
            # Use native buttons — styling handled by CSS
            if st.button(label, use_container_width=True, key=f"nav_{path}"):
                st.switch_page(path)

        # ── Rule Registry ─────────────────────────────────────────────────────
        try:
            from services.validation_service import ValidationService
            rules_df = ValidationService.get_error_codes()
            rule_count    = len(rules_df) if not rules_df.empty else 0
            context_count = (
                rules_df["context"].nunique()
                if not rules_df.empty and "context" in rules_df.columns
                else 0
            )
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

        # ── System controls ───────────────────────────────────────────────────
        st.markdown('<div class="dg-nav-label">System</div>', unsafe_allow_html=True)

        if st.button("↺  Refresh App", use_container_width=True):
            st.rerun()

        if st.button("🔌  Reconnect DB", use_container_width=True):
            st.session_state.boot_complete = False
            st.rerun()