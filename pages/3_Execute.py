from components.sidebar import render_sidebar

render_sidebar()

import pandas as pd
import streamlit as st

from services.validation_service import ValidationService
from utils.styles import load_css


load_css()

if "connected" not in st.session_state:
    st.session_state.connected = False
if not st.session_state.get("boot_complete", False):
    st.stop()

if "execute_step" not in st.session_state:
    st.session_state.execute_step = 1
if "selected_tables" not in st.session_state:
    st.session_state.selected_tables = []
if "execute_mode" not in st.session_state:
    st.session_state.execute_mode = "Complete ruleset"
if "execute_schedule" not in st.session_state:
    st.session_state.execute_schedule = "Run now"


def next_step():
    st.session_state.execute_step = min(3, st.session_state.execute_step + 1)


def prev_step():
    st.session_state.execute_step = max(1, st.session_state.execute_step - 1)


def reset_workflow():
    st.session_state.execute_step = 1
    st.session_state.selected_tables = []
    st.session_state.execute_mode = "Complete ruleset"
    st.session_state.execute_schedule = "Run now"


st.markdown(
    """
    <div class="dg-page-header">
        <div class="dg-page-eyebrow">Run Validations</div>
        <div class="dg-page-title">Choose the scope, then let the rules speak.</div>
        <div class="dg-page-desc">A three-step validation run: select the database surface, choose the ruleset posture, and confirm the evidence to write.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

step_cols = st.columns(3, gap="medium")
step_defs = [
    ("01", "Select scope", "Connection, schema, and table surface"),
    ("02", "Choose rules", "Ruleset, timing, and execution posture"),
    ("03", "Confirm", "Review before the engine writes history"),
]
for index, (number, title, meta) in enumerate(step_defs, start=1):
    with step_cols[index - 1]:
        state = "active" if st.session_state.execute_step == index else "done" if st.session_state.execute_step > index else ""
        st.markdown(
            f"""
            <div class="dg-step {state}">
                <div class="dg-step-index">{number}</div>
                <div class="dg-step-title">{title}</div>
                <div class="dg-step-meta">{meta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


if st.session_state.execute_step == 1:
    st.markdown('<div class="dg-section-label">Scope</div>', unsafe_allow_html=True)

    all_tables = ValidationService.get_db_tables()
    if not all_tables:
        st.warning("No tables were found in the connected database.")
        st.stop()

    table_df = pd.DataFrame({"Table": all_tables, "Include": False})
    if st.session_state.selected_tables:
        table_df.loc[table_df["Table"].isin(st.session_state.selected_tables), "Include"] = True

    st.markdown(
        """
        <div class="dg-card compact">
            <div class="dg-card-title">Selection</div>
            <div class="dg-card-copy">Choose the tables that belong in this validation run. The ledger below is intentionally plain: scope first, noise never.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    edited_df = st.data_editor(
        table_df,
        column_config={
            "Include": st.column_config.CheckboxColumn("Include", default=False),
            "Table": st.column_config.TextColumn("SQL table", disabled=True),
        },
        use_container_width=True,
        hide_index=True,
        key="table_selector",
    )

    selected_list = edited_df[edited_df["Include"]]["Table"].tolist()
    st.session_state.selected_tables = selected_list

    _, action_col, _ = st.columns([1, 1, 1])
    with action_col:
        if st.button("Continue", type="primary", use_container_width=True, disabled=not selected_list):
            next_step()
            st.rerun()

    if not selected_list:
        st.caption("Select at least one table to continue.")

elif st.session_state.execute_step == 2:
    st.markdown('<div class="dg-section-label">Ruleset posture</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="dg-row state-neutral">
            <div class="dg-row-title">{len(st.session_state.selected_tables)} tables selected</div>
            <div class="dg-row-meta">{', '.join(st.session_state.selected_tables)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.session_state.execute_mode = st.radio(
            "Ruleset",
            ["Complete ruleset", "Quick scan", "Active rules only"],
            horizontal=True,
            help="Complete ruleset runs every available validation rule for the selected scope.",
        )
        st.session_state.execute_schedule = st.radio(
            "Schedule",
            ["Run now", "Schedule for later"],
            horizontal=True,
        )
        fast_fail = st.toggle("Stop each table on first blocking failure", value=False)
        sample_run = st.toggle("Sample first 10,000 rows only", value=False)

    st.session_state.execute_fast_fail = fast_fail
    st.session_state.execute_sample_run = sample_run

    c1, _, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("Back", use_container_width=True):
            prev_step()
            st.rerun()
    with c3:
        if st.button("Review run", type="primary", use_container_width=True):
            next_step()
            st.rerun()

elif st.session_state.execute_step == 3:
    st.markdown('<div class="dg-section-label">Review</div>', unsafe_allow_html=True)

    left, right = st.columns([1.1, 1], gap="large")
    with left:
        st.markdown(
            f"""
            <div class="dg-metric hero">
                <div class="dg-metric-label">Validation scope</div>
                <div class="dg-metric-value">{len(st.session_state.selected_tables)}</div>
                <div class="dg-metric-sub">tables will be checked by the SQL validation engine</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        review_rows = [
            ("Ruleset", st.session_state.execute_mode),
            ("Schedule", st.session_state.execute_schedule),
            ("Fast fail", "On" if st.session_state.get("execute_fast_fail") else "Off"),
            ("Sample run", "On" if st.session_state.get("execute_sample_run") else "Off"),
        ]
        for label, value in review_rows:
            st.markdown(
                f"""
                <div class="dg-row state-neutral">
                    <div class="dg-row-title">{label}: {value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    c1, _, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("Back to rules", use_container_width=True):
            prev_step()
            st.rerun()
    with c3:
        if st.button("Run validations", type="primary", use_container_width=True):
            with st.spinner("Running validations... this may take a moment."):
                result = ValidationService.run_all_validations(table_names=st.session_state.selected_tables)

            if result.get("success"):
                status = result.get("status", "COMPLETED")
                total_errors = result.get("total_errors", 0)
                st.markdown(
                    f"""
                    <div class="dg-row {'state-pass' if total_errors == 0 else 'state-fail'}">
                        <div class="dg-row-title">Validation run {status.lower()}</div>
                        <div class="dg-row-meta">{total_errors:,} failures recorded. Open Results & History for the run ledger.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Open Results & History", use_container_width=True):
                    st.switch_page("pages/4_History.py")
            else:
                st.error(f"Execution failed: {result.get('error', 'Unknown error')}")

st.sidebar.markdown("---")
if st.sidebar.button("Reset workflow", use_container_width=True):
    reset_workflow()
    st.rerun()
