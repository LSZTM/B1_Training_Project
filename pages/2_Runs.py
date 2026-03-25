from components.sidebar import render_sidebar
render_sidebar()

import streamlit as st
from services.validation_service import ValidationService
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
        <div class="dg-page-eyebrow">Validation Engine</div>
        <div class="dg-page-title">Validation Runs</div>
        <div class="dg-page-desc">Execute the ruleset, inspect run history, and drill into per-run error details.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Run Controls
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Run Controls</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3, gap="medium")

with c1:
    if st.button("▶  Run All Validations", type="primary", use_container_width=True):
        with st.spinner("Executing validation rules…"):
            result = ValidationService.run_all_validations()

        if result.get("success"):
            total_errors = result.get("total_errors", 0)
            duration_ms  = result.get("duration_ms", 0)
            st.success(f"Complete · {total_errors:,} errors · {duration_ms:,} ms")
            st.balloons()
        else:
            st.error(f"Failed · {result.get('error', 'Unknown error')}")

        st.rerun()

with c2:
    st.button("⊞  Selected Tables", use_container_width=True)

with c3:
    st.button("⏰  Schedule Run", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Run History
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Run History</div>', unsafe_allow_html=True)

runs = ValidationService.get_run_history()

if not runs.empty:
    st.dataframe(runs, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    run_ids = runs["run_id"].tolist() if "run_id" in runs.columns else []
    if run_ids:
        st.markdown('<div class="dg-section-label">Run Inspector</div>', unsafe_allow_html=True)

        selected_id = st.selectbox(
            "Select run to inspect",
            options=run_ids,
            label_visibility="collapsed",
        )

        with st.expander(f"Run #{selected_id} — Detail View", expanded=False):
            try:
                details = ValidationService.get_run_details(selected_id)
                if details:
                    status  = details.get("status", "unknown")
                    errors  = details.get("total_errors", 0)
                    records = details.get("records_scanned", 0)
                    elapsed = details.get("duration_ms", 0)
                    badge_var = "success" if status == "success" else "error"

                    st.markdown(
                        f"""
                        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px;">
                            <span class="dg-badge {badge_var}">{status.upper()}</span>
                            <span class="dg-badge neutral">{errors:,} errors</span>
                            <span class="dg-badge neutral">{records:,} records</span>
                            <span class="dg-badge neutral">{elapsed:,} ms</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.json(details)
                else:
                    st.info("No detail payload returned for this run.")
            except Exception as exc:
                st.markdown(
                    f'<span class="dg-badge warning">Could not load details — {exc}</span>',
                    unsafe_allow_html=True,
                )
else:
    st.markdown(
        """
        <div class="dg-card" style="text-align:center;padding:40px 24px;">
            <div style="font-size:1.4rem;margin-bottom:10px;color:var(--text-muted);">⬡</div>
            <div style="font-family:var(--font-mono);font-size:0.78rem;color:var(--text-muted);">
                No runs recorded yet.<br>
                Execute <strong style="color:var(--text-secondary);">Run All Validations</strong> to populate history.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )