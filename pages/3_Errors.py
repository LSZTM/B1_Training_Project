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
        <div class="dg-page-eyebrow">Error Analysis</div>
        <div class="dg-page-title">Error Explorer</div>
        <div class="dg-page-desc">Investigate validation failures and isolate data quality issues across tables and columns.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Filters
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Filters</div>', unsafe_allow_html=True)

tables  = ValidationService.get_tables()
code_reference = ValidationService.get_error_code_reference()
codes = code_reference["error_code"].tolist() if not code_reference.empty else ValidationService.get_error_codes()
code_label_map = {
    row["error_code"]: f"{row['error_code']} — {row['description']}"
    for _, row in code_reference.fillna("").iterrows()
    if row.get("description")
}

c1, c2, c3 = st.columns(3, gap="medium")

selected_table = c1.selectbox("Table", ["All"] + tables)

columns = (
    ValidationService.get_columns(selected_table)
    if selected_table != "All"
    else ValidationService.get_columns()
)

selected_column = c2.selectbox("Column",     ["All"] + columns)
selected_code_label = c3.selectbox(
    "Error Code",
    ["All"] + [code_label_map.get(code, code) for code in codes],
)
label_to_code = {code_label_map.get(code, code): code for code in codes}
selected_code = label_to_code.get(selected_code_label, selected_code_label)

_, apply_col, _ = st.columns([3, 1, 3])
with apply_col:
    st.button("Apply Filters", type="primary", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATA RETRIEVAL
# ─────────────────────────────────────────────────────────────────────────────
errors = ValidationService.get_filtered_errors(
    table      =None if selected_table  == "All" else selected_table,
    column     =None if selected_column == "All" else selected_column,
    error_code =None if selected_code   == "All" else selected_code,
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Summary Metrics
# ─────────────────────────────────────────────────────────────────────────────
if not errors.empty:
    st.markdown('<div class="dg-section-label">Summary</div>', unsafe_allow_html=True)

    total_errors     = len(errors)
    tables_impacted  = errors["table_name"].nunique()   if "table_name"   in errors.columns else 0
    columns_impacted = errors["failed_field"].nunique() if "failed_field" in errors.columns else 0

    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.markdown(
            f"""
            <div class="dg-metric error">
                <div class="dg-metric-label">Total Errors</div>
                <div class="dg-metric-value">{total_errors:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="dg-metric warning">
                <div class="dg-metric-label">Tables Impacted</div>
                <div class="dg-metric-value">{tables_impacted}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="dg-metric warning">
                <div class="dg-metric-label">Columns Impacted</div>
                <div class="dg-metric-value">{columns_impacted}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Error Grid
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Validation Failures</div>', unsafe_allow_html=True)

if not errors.empty:
    st.dataframe(errors, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    _, dl_col, _ = st.columns([2, 2, 2])
    with dl_col:
        csv = errors.to_csv(index=False).encode("utf-8")
        st.download_button(
            "↓  Export Errors (CSV)",
            data=csv,
            file_name="validation_errors.csv",
            mime="text/csv",
            use_container_width=True,
        )
else:
    st.markdown(
        """
        <div class="dg-card" style="text-align:center;padding:40px 24px;">
            <div style="font-size:1.4rem;margin-bottom:10px;color:var(--text-muted);">⬡</div>
            <div style="font-family:var(--font-mono);font-size:0.78rem;color:var(--text-muted);">
                No validation failures detected for the current filter selection.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
