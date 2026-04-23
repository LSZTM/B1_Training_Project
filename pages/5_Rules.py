from components.sidebar import render_sidebar

render_sidebar()

import pandas as pd
import streamlit as st

from services.rule import Rule
from services.validation_service import ValidationService
from utils.styles import load_css


load_css()

if "connected" not in st.session_state:
    st.session_state.connected = False
if not st.session_state.get("boot_complete", False):
    st.stop()

st.markdown(
    """
    <div class="dg-page-header">
        <div class="dg-page-eyebrow">Rule Manager</div>
        <div class="dg-page-title">Write the rules like notes in a careful ledger.</div>
        <div class="dg-page-desc">Create, inspect, and maintain validation rules with clear scope, parameters, and failure codes.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

implementation_map = ValidationService.get_rule_implementation_map()

st.markdown('<div class="dg-section-label">Rule creation</div>', unsafe_allow_html=True)

with st.expander("Add or suggest a rule", expanded=False):
    schema_df = pd.DataFrame()
    schema_dict = {}

    left, right = st.columns([1, 1], gap="large")

    with left:
        contexts = ValidationService.get_db_tables()
        new_context = st.selectbox("Table", options=contexts or [])

        if new_context:
            schema_df = ValidationService.get_table_schema(new_context)
            if not schema_df.empty:
                schema_dict = dict(zip(schema_df["COLUMN_NAME"], schema_df["DATA_TYPE"]))
            columns = ValidationService.get_table_columns(new_context)
        else:
            columns = []

        new_column = st.selectbox("Column", options=columns or [])

        if new_context and new_column:
            st.markdown('<div class="dg-section-label">Suggestions</div>', unsafe_allow_html=True)
            suggestions = ValidationService.suggest_rules(new_context, new_column)
            column_ctx = ValidationService.get_column_context(new_context, new_column)
            category = column_ctx.get("category", "opaque")
            variant = "success" if category == "typed" else "warning" if category in {"sparse", "mixed"} else "neutral"
            st.markdown(f'<span class="dg-badge {variant}">{category}</span>', unsafe_allow_html=True)

            if column_ctx.get("warning"):
                st.warning(column_ctx["warning"])

            if suggestions:
                for idx, suggestion in enumerate(suggestions[:5]):
                    st.markdown(
                        f"""
                        <div class="dg-row state-neutral">
                            <div class="dg-row-title">{suggestion['rule_code']} - confidence {suggestion['confidence']:.2f}</div>
                            <div class="dg-row-meta">{suggestion['rule_params'] or '(no params)'} | {suggestion['rationale']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button("Add suggestion", key=f"add_suggest_{idx}", use_container_width=True):
                        if not implementation_map.get(suggestion["rule_code"], True):
                            st.warning(f"{suggestion['rule_code']} is not implemented yet.")
                            st.stop()
                        suggested_rule = Rule.from_signal_map(
                            table=new_context,
                            column=new_column,
                            rule_code=suggestion["rule_code"],
                            rule_signal_map=ValidationService.RULE_SIGNAL_MAP,
                            implementation_map=implementation_map,
                            rule_params=suggestion["rule_params"],
                            allow_null=suggestion["rule_code"] != "NOT_NULL",
                            is_active=True,
                            error_code=f"AUTO_{suggestion['rule_code'].upper()[:20]}",
                            comparison_column=None,
                        )
                        if ValidationService.add_validation_rule(suggested_rule):
                            st.success(f"Added suggested rule: {suggestion['rule_code']}")
                            st.rerun()
                        else:
                            st.error("Failed to add suggested rule.")
            else:
                st.caption("No high-confidence suggestions found for this column.")

    with right:
        rule_types = sorted(ValidationService.RULE_SIGNAL_MAP.keys())
        new_rule = st.selectbox("Rule type", rule_types)
        if not implementation_map.get(new_rule, True):
            st.markdown('<span class="dg-badge warning">Not implemented</span>', unsafe_allow_html=True)

        params = ""
        comparison_column = None
        allow_null = False
        error_code = "E000"

        st.markdown('<div class="dg-section-label">Parameters</div>', unsafe_allow_html=True)

        if new_rule == "NumberInRange":
            p1, p2 = st.columns(2)
            min_val = p1.number_input("Minimum value", value=0.0)
            max_val = p2.number_input("Maximum value", value=100.0)
            params = f"min={min_val},max={max_val}"
        elif new_rule == "HasLength":
            max_len = st.number_input("Maximum length", min_value=1, value=50, step=1)
            params = f"max={max_len}"
        elif new_rule == "IsDate":
            fmt = st.selectbox("Date format", ["YYYY-MM-DD", "DD-MM-YYYY", "MM/DD/YYYY", "YYYY/MM/DD"])
            params = f"format={fmt}"
        elif new_rule == "ColumnComparison":
            if new_context and new_column:
                numeric_types = {"int", "bigint", "smallint", "tinyint", "decimal", "numeric", "float", "real", "money", "smallmoney"}
                date_types = {"date", "datetime", "datetime2", "smalldatetime", "timestamp"}
                string_types = {"varchar", "nvarchar", "char", "nchar", "text", "ntext"}
                selected_type = schema_dict.get(new_column, "").lower()
                type_groups = [
                    (numeric_types, [">", "<", ">=", "<=", "=", "!="]),
                    (date_types, [">", "<", ">=", "<=", "=", "!="]),
                    (string_types, ["=", "!="]),
                ]
                compatible_columns = []
                operator_options = ["=", "!="]
                for group, operators in type_groups:
                    if selected_type in group:
                        compatible_columns = [col for col, dtype in schema_dict.items() if dtype.lower() in group and col != new_column]
                        operator_options = operators
                        break
                if compatible_columns:
                    comparison_column = st.selectbox("Compare with column", compatible_columns)
                    operator = st.selectbox("Operator", operator_options)
                    params = f"operator={operator},compare_to={comparison_column}"
                else:
                    st.warning("No compatible comparison column found.")
            else:
                st.caption("Select a table and column before configuring comparison.")

        allow_null = st.checkbox("Allow NULL values", value=False)
        error_code = st.text_input("Failure code", value=error_code)

        preview_lines = [
            f"table       : {new_context or '(not selected)'}",
            f"column      : {new_column or '(not selected)'}",
            f"rule        : {new_rule}",
            f"params      : {params or '(none)'}",
            f"allow_null  : {allow_null}",
            f"error_code  : {error_code}",
        ]
        if comparison_column:
            preview_lines.append(f"compare_to  : {comparison_column}")
        st.code("\n".join(preview_lines))

        if st.button("Save rule", type="primary", use_container_width=True):
            if not new_context or not new_column:
                st.warning("Select a table and column.")
                st.stop()
            if new_rule == "ColumnComparison" and not comparison_column:
                st.warning("Select a comparison column.")
                st.stop()
            if not implementation_map.get(new_rule, True):
                st.warning(f"Rule {new_rule} is not implemented yet.")
                st.stop()

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
            if ValidationService.add_validation_rule(rule):
                st.success(f"Rule saved: {new_context}.{new_column} -> {new_rule}")
                st.rerun()
            else:
                st.error("Failed to save rule.")

st.markdown('<div class="dg-section-label">Active ruleset</div>', unsafe_allow_html=True)

try:
    rules_df = ValidationService.get_validation_rules()
    if not rules_df.empty:
        rules_df = rules_df.copy()
        rules_df["is_implemented"] = rules_df["rule_code"].map(implementation_map).fillna(True)
        rules_df["implementation_status"] = rules_df["is_implemented"].map(lambda val: "Implemented" if bool(val) else "Not implemented")

        total_rules = len(rules_df)
        total_contexts = rules_df["table_name"].nunique() if "table_name" in rules_df.columns else 0
        c1, c2 = st.columns(2, gap="small")
        with c1:
            st.markdown(
                f"""
                <div class="dg-metric">
                    <div class="dg-metric-label">Rules</div>
                    <div class="dg-metric-value">{total_rules:,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="dg-metric">
                    <div class="dg-metric-label">Tables in scope</div>
                    <div class="dg-metric-value">{total_contexts:,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

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
                "error_code": "Failure code",
                "comparison_column": "Compare with",
                "implementation_status": "Implementation",
            },
        )
    else:
        st.markdown('<div class="dg-empty">No rules are defined yet. Add the first rule above.</div>', unsafe_allow_html=True)
except Exception as exc:
    st.error(f"Could not load ruleset: {exc}")
