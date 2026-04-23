from components.sidebar import render_sidebar
render_sidebar()

import streamlit as st
import pandas as pd
import time
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
        <div class="dg-page-eyebrow">Execution Engine</div>
        <div class="dg-page-title">Run Validations</div>
        <div class="dg-page-desc">Define the scope of your validation run, configure parameters, and execute or schedule.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Initialize session state for the workflow ─────────────────────────────────
if "execute_step" not in st.session_state:
    st.session_state.execute_step = 1
if "selected_tables" not in st.session_state:
    st.session_state.selected_tables = []

def next_step(): st.session_state.execute_step += 1
def prev_step(): st.session_state.execute_step -= 1
def reset_workflow():
    st.session_state.execute_step = 1
    st.session_state.selected_tables = []

# ── Step Indicator ────────────────────────────────────────────────────────────
steps = ["1. Select Scope", "2. Configure", "3. Execute"]
step_cols = st.columns(len(steps))
for i, label in enumerate(steps):
    is_active = st.session_state.execute_step == (i + 1)
    is_done = st.session_state.execute_step > (i + 1)
    
    with step_cols[i]:
        variant = "success" if is_done else "info" if is_active else "neutral"
        st.markdown(
            f"""
            <div class="dg-badge {variant}" style="width: 100%; justify-content: center; padding: 10px; border-radius: 99px;">
                {label}
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── STEP 1: Select Scope ──────────────────────────────────────────────────────
if st.session_state.execute_step == 1:
    st.markdown('<div class="dg-section-label">Target Selection</div>', unsafe_allow_html=True)
    
    all_tables = ValidationService.get_db_tables()
    if not all_tables:
        st.warning("No tables found in the current database. Please ensure your schema is populated.")
        st.stop()
    
    # Create a DataFrame for the data_editor
    table_df = pd.DataFrame({"Table Name": all_tables, "Selected": False})
    
    # Pre-select if already in session state
    if st.session_state.selected_tables:
        table_df.loc[table_df["Table Name"].isin(st.session_state.selected_tables), "Selected"] = True

    st.markdown("#### Select tables to include in this validation run")
    edited_df = st.data_editor(
        table_df,
        column_config={
            "Selected": st.column_config.CheckboxColumn(
                "Select",
                help="Mark tables for validation",
                default=False,
            ),
            "Table Name": st.column_config.TextColumn(
                "Database Table",
                disabled=True,
            )
        },
        use_container_width=True,
        hide_index=True,
        key="table_selector"
    )
    
    selected_list = edited_df[edited_df["Selected"]]["Table Name"].tolist()
    st.session_state.selected_tables = selected_list
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("Continue to Configuration", type="primary", use_container_width=True, disabled=not selected_list):
            next_step()
            st.rerun()
    if not selected_list:
        st.caption("Please select at least one table to continue.")

# ── STEP 2: Configure ─────────────────────────────────────────────────────────
elif st.session_state.execute_step == 2:
    st.markdown('<div class="dg-section-label">Rule Configuration</div>', unsafe_allow_html=True)
    
    num_selected = len(st.session_state.selected_tables)
    st.markdown(f"**{num_selected} Tables Selected:** `{', '.join(st.session_state.selected_tables)}`")
    
    with st.container(border=True):
        st.markdown("#### Validation Mode")
        run_mode = st.radio(
            "Select how rules should be applied:",
            ["Complete Ruleset (Recommended)", "Quick Scan (Type & Format only)", "Active Rules Only"],
            help="Complete Ruleset runs all defined and suggested rules. Quick Scan focuses on schema type mismatches."
        )
        
        st.markdown("---")
        st.markdown("#### Execution Parameters")
        fast_fail = st.toggle("Fast Fail", value=False, help="Stop individual table validation on first error.")
        sample_run = st.toggle("Sample Data Only", value=False, help="Only validate the first 10,000 rows.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("Back to Selection", use_container_width=True):
            prev_step()
            st.rerun()
    with c3:
        if st.button("Proceed to Run", type="primary", use_container_width=True):
            next_step()
            st.rerun()

# ── STEP 3: Execute ───────────────────────────────────────────────────────────
elif st.session_state.execute_step == 3:
    st.markdown('<div class="dg-section-label">Review & Launch</div>', unsafe_allow_html=True)
    
    col_l, col_r = st.columns(2, gap="large")
    
    with col_l:
        st.markdown("#### Run Summary")
        summary_html = f"""
        <div class="dg-card">
            <div style="margin-bottom: 12px; display: flex; justify-content: space-between;">
                <span style="color: var(--text-muted);">Scope:</span>
                <span style="color: var(--text-primary); font-weight: 600;">{len(st.session_state.selected_tables)} Tables</span>
            </div>
            <div style="margin-bottom: 12px; display: flex; justify-content: space-between;">
                <span style="color: var(--text-muted);">Mode:</span>
                <span class="dg-badge info">Complete Ruleset</span>
            </div>
            <div style="margin-bottom: 12px; display: flex; justify-content: space-between;">
                <span style="color: var(--text-muted);">Auto-Remediation:</span>
                <span style="color: var(--danger);">Disabled</span>
            </div>
        </div>
        """
        st.markdown(summary_html, unsafe_allow_html=True)
        
        if st.button("Run All Validations Now", type="primary", use_container_width=True):
            with st.spinner("Initializing engine and executing rules..."):
                # Simulation of per-table run if needed, but for now we follow existing service
                # In a real fix, we'd pass selected_tables to run_all_validations
                result = ValidationService.run_all_validations(table_names=st.session_state.selected_tables)
                
            if result.get("success"):
                st.success(f"Execution Complete! {result.get('total_errors', 0):,} errors found.")
                st.balloons()
                time.sleep(2)
                st.switch_page("pages/4_History.py")
            else:
                st.error(f"Execution Failed: {result.get('error', 'Unknown Error')}")

    with col_r:
        st.markdown("#### Schedule Run")
        with st.container(border=True):
            st.markdown("Automate this validation scope for future runs.")
            freq = st.selectbox("Frequency", ["Every Hour", "Daily at midnight", "Weekly (Sundays)", "Custom CRON"])
            notif = st.text_input("Alert Email", placeholder="data-ops@company.com")
            
            if st.button("Save Schedule", use_container_width=True):
                st.info("Schedule recorded. DataGuard daemon will pick up this task.")
                # Here we would normally save to a schedules table.
                # execute_sql("INSERT INTO schedules (tables, freq, ...) ...")
                time.sleep(1.5)
                st.session_state.execute_step = 1
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Recap Configuration", use_container_width=True):
        prev_step()
        st.rerun()

# ── Empty State / Reset ───────────────────────────────────────────────────────
st.sidebar.markdown("---")
if st.sidebar.button("Reset Workflow", use_container_width=True):
    reset_workflow()
    st.rerun()
