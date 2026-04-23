from components.sidebar import render_sidebar

render_sidebar()

import streamlit as st
import streamlit.components.v1 as components

from components.log_workspace import render_log_workspace_html
from services.logs_service import (
    DEFAULT_VISIBLE_SEVERITIES,
    LogsService,
    TIME_RANGE_OPTIONS,
    dataframe_records,
    normalize_severity,
    resolve_effective_severities,
    summarize_logs,
)
from utils.styles import load_css

load_css()

LOGS_DEFAULTS = {
    "logs_search_text": "",
    "logs_severity_mode": "explicit",
    "logs_explicit_severities": DEFAULT_VISIBLE_SEVERITIES.copy(),
    "logs_minimum_severity": "INFO",
    "logs_validation_id": "",
    "logs_rule_filter": "",
    "logs_statuses": [],
    "logs_time_range": "1h",
    "logs_live_mode": True,
    "logs_auto_scroll": True,
    "logs_show_only_failures": False,
    "logs_group_by": "flat",
    "logs_selected_log_id": None,
}
STATUS_OPTIONS = ["PASSED", "FAILED", "STARTED", "COMPLETED"]
SEVERITY_OPTIONS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
GROUP_OPTIONS = {
    "flat": "Flat live stream",
    "validation": "Group by validation ID",
    "severity": "Group by severity",
    "time": "Group by time bucket",
}


if "connected" not in st.session_state:
    st.session_state.connected = False
if not st.session_state.get("boot_complete", False):
    st.stop()


for key, value in LOGS_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_logs_filters():
    for key, value in LOGS_DEFAULTS.items():
        st.session_state[key] = value


def consume_logs_query_actions():
    params = st.query_params
    quick_keys = ["quick_validation_id", "quick_rule_id", "quick_severity", "quick_only_severity"]

    selected = params.get("selected_log_id")
    if selected:
        try:
            st.session_state.logs_selected_log_id = int(str(selected))
        except ValueError:
            st.session_state.logs_selected_log_id = None

    quick_validation_id = params.get("quick_validation_id")
    if quick_validation_id:
        st.session_state.logs_validation_id = str(quick_validation_id)

    quick_rule_id = params.get("quick_rule_id")
    if quick_rule_id:
        st.session_state.logs_rule_filter = str(quick_rule_id)

    quick_severity = params.get("quick_severity")
    if quick_severity:
        current = resolve_effective_severities(
            mode=st.session_state.logs_severity_mode,
            explicit_levels=st.session_state.logs_explicit_severities,
            minimum_level=st.session_state.logs_minimum_severity,
        )
        severity = normalize_severity(quick_severity)
        if severity not in current:
            current.append(severity)
        st.session_state.logs_severity_mode = "explicit"
        st.session_state.logs_explicit_severities = current

    quick_only_severity = params.get("quick_only_severity")
    if quick_only_severity:
        st.session_state.logs_severity_mode = "explicit"
        st.session_state.logs_explicit_severities = [normalize_severity(quick_only_severity)]

    for key in quick_keys:
        if key in params:
            params.pop(key)


def current_filters() -> dict:
    return {
        "limit": 800,
        "time_range_key": st.session_state.logs_time_range,
        "search_text": st.session_state.logs_search_text,
        "severity_mode": st.session_state.logs_severity_mode,
        "explicit_severities": st.session_state.logs_explicit_severities,
        "minimum_severity": st.session_state.logs_minimum_severity,
        "validation_id": st.session_state.logs_validation_id,
        "rule_filter": st.session_state.logs_rule_filter,
        "statuses": st.session_state.logs_statuses,
        "show_only_failures": st.session_state.logs_show_only_failures,
    }


def load_logs_frame():
    return LogsService.fetch_logs(**current_filters())


def render_summary_cards(summary: dict):
    columns = st.columns(8, gap="small")
    cards = [
        ("Total events", f"{summary['total_events']:,}", "", "current filtered view"),
        ("Live stream", summary["live_status"], "success" if summary["live_status"] == "LIVE" else "warning" if summary["live_status"] == "PAUSED" else "error", "session status"),
        ("Critical", f"{summary['critical_count']:,}", "error", "urgent attention"),
        ("Errors", f"{summary['error_count']:,}", "error", "failed executions"),
        ("Warnings", f"{summary['warning_count']:,}", "warning", "recoverable issues"),
        ("Running", f"{summary['running_validations']:,}", "", "in filtered set"),
        ("Failed runs", f"{summary['failed_validations']:,}", "warning" if summary["failed_validations"] else "success", "validation journeys"),
        ("Avg duration", f"{summary['avg_duration_ms']:,} ms", "", "filtered mean"),
    ]
    for column, (label, value, variant, subtext) in zip(columns, cards):
        with column:
            variant_class = f" {variant}" if variant else ""
            st.markdown(
                f"""
                <div class="dg-metric{variant_class}" style="min-height:112px;padding:16px;">
                    <div class="dg-metric-label">{label}</div>
                    <div class="dg-metric-value" style="font-size:1.45rem;">{value}</div>
                    <div class="dg-metric-sub">{subtext}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_summary_fragment():
    frame, metadata = load_logs_frame()
    connected = bool(st.session_state.connected) and bool(metadata["connected"])
    summary = summarize_logs(frame, live_mode=st.session_state.logs_live_mode, connected=connected)
    st.markdown('<div class="dg-section-label">Current View</div>', unsafe_allow_html=True)

    if summary["critical_count"] > 0:
        st.markdown(
            """
            <div class="dg-row state-critical" style="margin-bottom:16px;">
                <div class="dg-card-title">Critical activity detected</div>
                <div style="color:var(--text-primary);font-size:0.88rem;line-height:1.55;">
                    Critical events are present in the current filtered view. Select an event to inspect payloads and related validation history.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_summary_cards(summary)

    if metadata["error"] and not metadata["schema_ready"]:
        st.warning(
            "Structured logs are not installed yet. Run the SQL migration for validation logs before opening the live console."
        )
    elif metadata["error"] and not connected:
        st.error(f"Live log connection is disconnected: {metadata['error']}")


def render_workspace_fragment():
    frame, metadata = load_logs_frame()
    connected = bool(st.session_state.connected) and bool(metadata["connected"])
    summary = summarize_logs(frame, live_mode=st.session_state.logs_live_mode, connected=connected)

    if frame.empty:
        display_frame = frame
    else:
        ascending = st.session_state.logs_live_mode
        display_frame = frame.sort_values(by=["event_timestamp", "log_id"], ascending=[ascending, ascending]).copy()

    selected_id = st.session_state.logs_selected_log_id
    if selected_id is not None and not display_frame.empty and selected_id not in display_frame["log_id"].tolist():
        st.session_state.logs_selected_log_id = None
        selected_id = None
        if "selected_log_id" in st.query_params:
            st.query_params.pop("selected_log_id")

    records = dataframe_records(display_frame)

    st.markdown('<div class="dg-section-label">Workspace</div>', unsafe_allow_html=True)

    export_frame = display_frame.copy()
    if not export_frame.empty:
        export_frame["event_timestamp"] = export_frame["event_timestamp"].astype(str)
    csv = export_frame.to_csv(index=False).encode("utf-8")
    stream_status = summary["live_status"]
    export_col, spacer = st.columns([1, 4])
    with export_col:
        st.download_button(
            "Export current filtered logs",
            data=csv,
            file_name="validation_logs_filtered.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with spacer:
        st.caption(
            f"Showing {summary['total_events']:,} log events in {GROUP_OPTIONS[st.session_state.logs_group_by].lower()}."
        )

    html = render_log_workspace_html(
        records=records,
        selected_log_id=selected_id,
        group_mode=st.session_state.logs_group_by,
        live_mode=st.session_state.logs_live_mode,
        auto_scroll=st.session_state.logs_auto_scroll,
        connection_state=stream_status,
    )
    components.html(html, height=860, scrolling=False)


consume_logs_query_actions()

st.markdown(
    """
    <div class="dg-page-header">
        <div class="dg-page-eyebrow">Operational Observability</div>
        <div class="dg-page-title">A live ledger for validation events.</div>
        <div class="dg-page-desc">Monitor structured validation logs, isolate failures by severity or context, and drill into the event payload without losing the current filter.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

summary_fragment = st.fragment(run_every="5s" if st.session_state.logs_live_mode else None)(render_summary_fragment)
summary_fragment()

st.markdown('<div class="dg-section-label">Filters & Controls</div>', unsafe_allow_html=True)

row1 = st.columns([1.5, 1.2, 1.1, 1.1, 1.1], gap="small")
with row1[0]:
    st.text_input("Search", key="logs_search_text", placeholder="message, validation ID, rule, correlation ID")
with row1[1]:
    st.selectbox(
        "Severity mode",
        options=["explicit", "minimum"],
        format_func=lambda value: "Explicit levels" if value == "explicit" else "Minimum severity",
        key="logs_severity_mode",
    )
with row1[2]:
    st.multiselect(
        "Severity filter",
        options=SEVERITY_OPTIONS,
        key="logs_explicit_severities",
        disabled=st.session_state.logs_severity_mode != "explicit",
    )
with row1[3]:
    st.selectbox(
        "Minimum severity",
        options=["INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"],
        key="logs_minimum_severity",
        disabled=st.session_state.logs_severity_mode != "minimum",
    )
with row1[4]:
    st.selectbox(
        "Time range",
        options=list(TIME_RANGE_OPTIONS.keys()),
        format_func=lambda key: TIME_RANGE_OPTIONS[key]["label"],
        key="logs_time_range",
    )

row2 = st.columns([1.2, 1.2, 1.2, 1, 1, 1, 1.2], gap="small")
with row2[0]:
    st.text_input("Validation ID", key="logs_validation_id", placeholder="Filter a validation journey")
with row2[1]:
    st.text_input("Rule ID", key="logs_rule_filter", placeholder="Rule id or rule code")
with row2[2]:
    st.multiselect("Status", STATUS_OPTIONS, key="logs_statuses")
with row2[3]:
    st.toggle("Live mode", key="logs_live_mode")
with row2[4]:
    st.toggle("Auto-scroll", key="logs_auto_scroll")
with row2[5]:
    st.toggle("Only failures", key="logs_show_only_failures")
with row2[6]:
    st.selectbox(
        "Display mode",
        options=list(GROUP_OPTIONS.keys()),
        format_func=lambda key: GROUP_OPTIONS[key],
        key="logs_group_by",
    )

if st.session_state.logs_severity_mode == "minimum":
    st.caption(f"Showing {st.session_state.logs_minimum_severity} and above.")

action_cols = st.columns([1, 5], gap="small")
with action_cols[0]:
    if st.button("Clear filters", use_container_width=True):
        reset_logs_filters()
        st.rerun()

workspace_fragment = st.fragment(run_every="5s" if st.session_state.logs_live_mode else None)(render_workspace_fragment)
workspace_fragment()
