from components.sidebar import render_sidebar
render_sidebar()

import streamlit as st
import pandas as pd
from services.rule import Rule
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
        <div class="dg-page-eyebrow">Rule Management</div>
        <div class="dg-page-title">Rule Manager</div>
        <div class="dg-page-desc">Define, inspect, and maintain the validation ruleset applied to incoming data.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Add New Rule
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("+ Add New Rule", expanded=False):

    schema_df = pd.DataFrame()
    schema_dict = {}

    implementation_map = ValidationService.get_rule_implementation_map()
    c1, c2 = st.columns(2, gap="medium")

    with c1:
        contexts = ValidationService.get_db_tables()  # Returns list
        new_context = st.selectbox("Context (Table)", options=contexts or [])

        if new_context:
            schema_df = ValidationService.get_table_schema(new_context)
            if not schema_df.empty:
                # Create dictionary for type lookup: column_name -> data_type
                schema_dict = dict(zip(schema_df['COLUMN_NAME'], schema_df['DATA_TYPE']))
            
            columns = ValidationService.get_table_columns(new_context)  # Returns list
        else:
            columns = []

        new_column = st.selectbox("Column", options=columns or [])


    with c2:
        rule_types = sorted(ValidationService.RULE_SIGNAL_MAP.keys())

        new_rule = st.selectbox("Rule Type", rule_types)
        if not implementation_map.get(new_rule, True):
            st.markdown(
                '<span class="dg-badge warning">Not yet implemented</span>',
                unsafe_allow_html=True,
            )
            st.warning(
                "This rule is currently marked NOT_IMPLEMENTED in the database and cannot be saved."
            )

    # ── Full-Width Suggestions ────────────────────────────────────────────────
    if new_context and new_column:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### Auto-Suggested Rules")
            suggestions = ValidationService.suggest_rules(new_context, new_column)
            column_ctx = ValidationService.get_column_context(new_context, new_column)

            category_badge = {
                "typed": ("success", "Typed column — high confidence suggestions"),
                "sparse": ("warning", f"Sparse column — {int(column_ctx.get('null_rate', 0) * 100)}% NULL"),
                "mixed": ("warning", "Mixed content detected"),
                "free_text": ("neutral", "Free text column — hygiene rules only"),
                "opaque": ("error", "Opaque column — manual review recommended"),
            }
            badge_style, badge_label = category_badge.get(
                column_ctx.get("category", "opaque"),
                ("neutral", "Column profile unavailable"),
            )
            
            b_col1, b_col2 = st.columns([1, 3])
            with b_col1:
                st.markdown(f'<span class="dg-badge {badge_style}">{badge_label}</span>', unsafe_allow_html=True)
            with b_col2:
                if column_ctx.get("warning"):
                    st.caption(f"⚠️ {column_ctx['warning']}")

            if column_ctx.get("category") in {"mixed", "opaque"}:
                with st.expander("Data fingerprint", expanded=False):
                    for pattern, rate in sorted(
                        column_ctx.get("fingerprint", {}).items(),
                        key=lambda item: item[1],
                        reverse=True,
                    ):
                        if rate > 0.05:
                            st.progress(rate, text=f"{pattern}: {rate:.0%}")

            if suggestions:
                st.markdown('<div class="dg-section-label">Smart Suggestions</div>', unsafe_allow_html=True)
                
                # Process suggestions in triplets for full-width grid
                for i in range(0, len(suggestions), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i + j < len(suggestions):
                            with cols[j]:
                                suggestion = suggestions[i + j]
                                with st.container(border=True):
                                    st.markdown(
                                        f"<div style='font-size: 0.85rem; font-weight: 600; color: var(--text-primary); margin-bottom: 2px;'>{suggestion['rule_code']}</div>"
                                        f"<div style='font-size: 0.75rem; color: var(--accent); margin-bottom: 8px;'>Confidence {suggestion['confidence']:.2f} · {suggestion.get('category', 'general')}</div>"
                                        f"<div style='font-size: 0.75rem; color: var(--text-muted); line-height: 1.3; height: 3.2em; overflow: hidden; margin-bottom: 12px;'>{suggestion['rationale']}</div>",
                                        unsafe_allow_html=True
                                    )
                                    
                                    sub_c1, sub_c2 = st.columns([1, 1])
                                    with sub_c1:
                                        st.caption(f"`{suggestion['rule_params'] or 'no params'}`")
                                    with sub_c2:
                                        if st.button("Add", key=f"add_suggest_{i+j}", use_container_width=True, type="primary"):
                                            if not implementation_map.get(suggestion["rule_code"], True):
                                                st.warning(f"Not implemented")
                                                st.stop()
                                            
                                            auto_error_code = f"A_{suggestion['rule_code'].upper()[:45]}"
                                            suggested_rule = Rule.from_signal_map(
                                                table=new_context,
                                                column=new_column,
                                                rule_code=suggestion["rule_code"],
                                                rule_signal_map=ValidationService.RULE_SIGNAL_MAP,
                                                implementation_map=implementation_map,
                                                rule_params=suggestion["rule_params"],
                                                allow_null=suggestion["rule_code"] != "NOT_NULL",
                                                is_active=True,
                                                error_code=auto_error_code,
                                                comparison_column=None,
                                            )
                                            if ValidationService.add_validation_rule(suggested_rule):
                                                st.success("Added")
                                                st.rerun()
                                            else:
                                                st.error("Failed")
            else:
                st.caption("No high-confidence suggestions found for this column.")

    # ---------------------------------------------------
    #  Dynamic parameter inputs
    # ---------------------------------------------------

    params = ""
    comparison_column = None
    operator = "="
    allow_null = False
    error_code = "E000"

    st.markdown("### Parameters")

    if new_rule == "NumberInRange":
        col1, col2 = st.columns(2)
        with col1:
            min_val = st.number_input("Minimum Value", value=0.0)
        with col2:
            max_val = st.number_input("Maximum Value", value=100.0)
        params = f"min={min_val},max={max_val}"

    elif new_rule == "HasLength":
        max_len = st.number_input("Maximum Length", min_value=1, value=50, step=1)
        params = f"max={max_len}"

    elif new_rule == "IsDate":
        fmt = st.selectbox("Date Format", ["YYYY-MM-DD", "DD-MM-YYYY", "MM/DD/YYYY", "YYYY/MM/DD"])
        params = f"format={fmt}"

    elif new_rule == "ColumnComparison":
        if not new_context or not new_column:
            st.warning("Please select a table and column first.")
        else:
            # Define compatible type groups
            numeric_types = {
                "int", "bigint", "smallint", "tinyint",
                "decimal", "numeric", "float", "real",
                "money", "smallmoney"
            }
            
            date_types = {"date", "datetime", "datetime2", "smalldatetime", "timestamp"}
            string_types = {"varchar", "nvarchar", "char", "nchar", "text", "ntext"}
            
            # Get the data type of the selected column
            selected_type = schema_dict.get(new_column, "").lower()
            
            # Determine compatible columns based on type
            compatible_columns = []
            type_category = "unknown"
            
            if selected_type in numeric_types:
                compatible_columns = [
                    col for col, dtype in schema_dict.items()
                    if dtype.lower() in numeric_types and col != new_column
                ]
                type_category = "numeric"
                
            elif selected_type in date_types:
                compatible_columns = [
                    col for col, dtype in schema_dict.items()
                    if dtype.lower() in date_types and col != new_column
                ]
                type_category = "date"
                
            elif selected_type in string_types:
                compatible_columns = [
                    col for col, dtype in schema_dict.items()
                    if dtype.lower() in string_types and col != new_column
                ]
                type_category = "string"
            
            if compatible_columns:
                comparison_column = st.selectbox(
                    "Compare With Column",
                    compatible_columns,
                    help=f"Only columns of compatible type ({type_category}) are shown"
                )
                
                # Operators vary by type
                if type_category == "string":
                    operator_options = ["=", "!="]
                else:
                    operator_options = [">", "<", ">=", "<=", "=", "!="]
                
                operator = st.selectbox("Operator", operator_options)
                
                # Build params string
                params = f"operator={operator},compare_to={comparison_column}"
                
                st.info(f"Rule: {new_column} {operator} {comparison_column}")
            else:
                st.warning(f"No compatible columns found for {type_category} comparison.")

    # ---------------------------------------------------
    # Common rule parameters
    # ---------------------------------------------------
    
    st.markdown("### Rule Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        allow_null = st.checkbox("Allow NULL values", value=False, 
                                 help="If checked, NULL values will pass validation")
    with col2:
        # Automatically generate error code based on rule and column
        generated_prefix = "M" 
        clean_rule = new_rule.upper().replace("_", "")[:15]
        clean_col = new_column.upper().replace("_", "")[:15]
        error_code = f"{generated_prefix}_{clean_rule}_{clean_col}"
        
        st.info(f"Generated Error Code: `{error_code}`")

    # ---------------------------------------------------
    # Preview
    # ---------------------------------------------------

    st.markdown("### Rule Preview")
    
    preview_lines = [
        f"Context     : {new_context or '(not selected)'}",
        f"Column      : {new_column or '(not selected)'}",
        f"Rule        : {new_rule}",
        f"Params      : {params or '(none)'}",
        f"Allow NULL  : {allow_null}",
        f"Error Code  : {error_code}",
    ]
    
    if comparison_column:
        preview_lines.append(f"Compare With: {comparison_column}")
    
    st.code("\n".join(preview_lines))

    st.markdown("<br>", unsafe_allow_html=True)

    _, save_col, _ = st.columns([3, 2, 3])

    with save_col:
        if st.button("Save Rule", type="primary", use_container_width=True):

            if not new_context or not new_column:
                st.warning("Select table and column.")
                st.stop()

            if new_rule == "ColumnComparison" and not comparison_column:
                st.warning("Select a column to compare with.")
                st.stop()

            if not implementation_map.get(new_rule, True):
                st.warning(f"Rule {new_rule} is not yet implemented and cannot be saved.")
                st.stop()

            try:
                rule = Rule.from_signal_map(
                    table=new_context,
                    column=new_column,
                    rule_code=new_rule,
                    rule_signal_map=ValidationService.RULE_SIGNAL_MAP,
                    implementation_map=implementation_map,
                    rule_params=params,
                    allow_null=allow_null,
                    is_active=True,
                    error_code=error_code,
                    comparison_column=comparison_column,
                )
                success = ValidationService.add_validation_rule(
                    rule
                )

                if success:
                    st.success(f"✅ Rule added · {new_context}.{new_column} → {new_rule}")
                    st.rerun()
                else:
                    st.error("Failed to save rule - database error occurred")

            except Exception as exc:
                st.error(f"Failed to save rule — {str(exc)}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Active Ruleset (Read‑Only)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Active Ruleset</div>', unsafe_allow_html=True)

try:
    rules_df = ValidationService.get_validation_rules()  # Returns DataFrame

    if not rules_df.empty:
        rules_df = rules_df.copy()
        rules_df["is_implemented"] = rules_df["rule_code"].map(implementation_map).fillna(True)
        rules_df["implementation_status"] = rules_df["is_implemented"].map(
            lambda val: "Implemented" if bool(val) else "Not yet implemented"
        )
        total_rules = len(rules_df)
        total_contexts = rules_df["table_name"].nunique() if "table_name" in rules_df.columns else 0

        st.markdown(
            f"""
            <div style="display:flex;gap:10px;margin-bottom:16px;">
                <span class="dg-badge neutral">{total_rules} rules</span>
                <span class="dg-badge neutral">{total_contexts} tables</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Display rules in a static table
        st.dataframe(
            rules_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "table_name": "Table",
                "column_name": "Column",
                "rule_code": "Rule",
                "rule_params": "Parameters",
                "allow_null": st.column_config.CheckboxColumn("Allow NULL"),
                "is_active": st.column_config.CheckboxColumn("Active"),
                "error_code": "Error Code",
                "comparison_column": "Compare With",
                "implementation_status": "Implementation",
            }
        )

    else:
        st.markdown(
            """
            <div class="dg-card" style="text-align:center;padding:40px 24px;">
                <div style="font-size:1.4rem;margin-bottom:10px;        color:var(--text-muted);">⬡</div>
                <div style="font-family:var(--font-mono);font-size:0.78rem;color:var(--text-muted);">
                    No rules defined yet.<br>
                    Use <strong style="color:var(--text-secondary);">Add New Rule</strong> above to get started.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

except Exception as exc:
    st.markdown(
        f'<span class="dg-badge error">Could not load ruleset — {str(exc)}</span>',
        unsafe_allow_html=True,
    )
