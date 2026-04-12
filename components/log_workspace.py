from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus

SEVERITY_CLASS = {
    "DEBUG": "debug",
    "INFO": "info",
    "WARNING": "warning",
    "ERROR": "error",
    "CRITICAL": "critical",
}
STATUS_CLASS = {
    "STARTED": "started",
    "PASSED": "passed",
    "FAILED": "failed",
    "COMPLETED": "completed",
}
SEVERITY_RANKS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _format_timestamp(value: Any) -> str:
    if not value:
        return "--"
    text = str(value).replace("T", " ")
    return text.replace("+00:00", " UTC")


def _pretty_json(value: Any) -> str:
    if value in (None, ""):
        return "{}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, sort_keys=True)
    text = str(value)
    try:
        return json.dumps(json.loads(text), indent=2, sort_keys=True)
    except Exception:
        return text


def _rule_identifier(record: dict[str, Any]) -> str:
    rule_id = record.get("rule_id")
    if rule_id not in (None, ""):
        return str(rule_id)
    return str(record.get("rule_code") or "--")


def _build_href(param_name: str, param_value: Any) -> str:
    return f"?init=done&{param_name}={quote_plus(str(param_value))}"


def _build_detail_section(title: str, value: Any, *, code: bool = False, collapsible: bool = False) -> str:
    if value in (None, ""):
        return ""
    body = f"<pre>{_escape(value)}</pre>" if code else f"<div class='dg-log-detail-value'>{_escape(value)}</div>"
    if collapsible:
        return (
            f"<details class='dg-log-detail-block'>"
            f"<summary>{_escape(title)}</summary>"
            f"{body}"
            f"</details>"
        )
    return (
        f"<div class='dg-log-detail-block'>"
        f"<div class='dg-log-detail-label'>{_escape(title)}</div>"
        f"{body}"
        f"</div>"
    )


def _row_html(record: dict[str, Any], selected_log_id: int | None) -> str:
    log_id = record.get("log_id")
    severity = str(record.get("severity") or "INFO").upper()
    status = str(record.get("validation_status") or "").upper()
    severity_class = SEVERITY_CLASS.get(severity, "info")
    status_class = STATUS_CLASS.get(status, "completed")
    validation_id = record.get("validation_id")
    rule_identifier = _rule_identifier(record)
    row_selected_class = " selected" if selected_log_id == log_id else ""

    chips = [
        f"<span class='dg-log-chip mono'>{_escape(_format_timestamp(record.get('event_timestamp')))}</span>",
        f"<a class='dg-log-chip severity {severity_class}' href='{_build_href('quick_severity', severity)}'>{_escape(severity)}</a>",
    ]
    if status:
        chips.append(f"<span class='dg-log-chip status {status_class}'>{_escape(status)}</span>")
    if validation_id:
        chips.append(f"<a class='dg-log-chip mono' href='{_build_href('quick_validation_id', validation_id)}'>{_escape(validation_id)}</a>")
    if rule_identifier and rule_identifier != "--":
        chips.append(f"<a class='dg-log-chip mono' href='{_build_href('quick_rule_id', rule_identifier)}'>{_escape(rule_identifier)}</a>")
    if record.get("source_module"):
        chips.append(f"<span class='dg-log-chip'>{_escape(record.get('source_module'))}</span>")
    if record.get("duration_ms") not in (None, ""):
        chips.append(f"<span class='dg-log-chip mono'>{_escape(record.get('duration_ms'))} ms</span>")

    return (
        f"<div class='dg-log-row{row_selected_class}' data-log-id='{_escape(log_id)}'>"
        f"  <a class='dg-log-row-main' href='{_build_href('selected_log_id', log_id)}'>"
        f"    <div class='dg-log-row-message'>{_escape(record.get('message') or '(no message)')}</div>"
        f"    <div class='dg-log-row-meta'>{''.join(chips)}</div>"
        f"  </a>"
        f"</div>"
    )


def _group_label(group_mode: str, record: dict[str, Any]) -> str:
    if group_mode == "validation":
        return str(record.get("validation_id") or "No validation id")
    if group_mode == "severity":
        return str(record.get("severity") or "INFO")
    if group_mode == "time":
        timestamp = record.get("event_timestamp")
        text = _format_timestamp(timestamp)
        return text[:16] if len(text) >= 16 else text
    return "Live stream"


def _group_records(records: list[dict[str, Any]], group_mode: str) -> list[dict[str, Any]]:
    if group_mode == "flat":
        return [{"label": "Live stream", "records": records, "worst_severity": _worst_severity(records)}]

    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        key = _group_label(group_mode, record)
        groups.setdefault(key, []).append(record)

    grouped = []
    for label, rows in groups.items():
        grouped.append({"label": label, "records": rows, "worst_severity": _worst_severity(rows)})

    grouped.sort(key=lambda item: (-SEVERITY_RANKS.get(item["worst_severity"], 0), item["label"]))
    return grouped


def _worst_severity(records: list[dict[str, Any]]) -> str:
    winner = "DEBUG"
    for record in records:
        severity = str(record.get("severity") or "INFO").upper()
        if SEVERITY_RANKS.get(severity, 0) > SEVERITY_RANKS.get(winner, 0):
            winner = severity
    return winner


def _detail_html(records: list[dict[str, Any]], selected_log_id: int | None) -> str:
    if not records:
        return (
            "<div class='dg-log-empty-detail'>"
            "<div class='dg-log-empty-title'>No logs match current filters</div>"
            "<div class='dg-log-empty-text'>Adjust the filters or widen the time range to inspect validation activity.</div>"
            "</div>"
        )

    selected = next((record for record in records if record.get("log_id") == selected_log_id), None)
    if not selected:
        selected = records[-1]

    index = next((idx for idx, record in enumerate(records) if record.get("log_id") == selected.get("log_id")), 0)
    previous_id = records[index - 1].get("log_id") if index > 0 else None
    next_id = records[index + 1].get("log_id") if index < len(records) - 1 else None

    related_html = ""
    validation_id = selected.get("validation_id")
    if validation_id:
        related = [record for record in records if record.get("validation_id") == validation_id and record.get("log_id") != selected.get("log_id")]
        if related:
            related_rows = []
            for record in related[:8]:
                related_rows.append(
                    f"<a class='dg-log-related-row' href='{_build_href('selected_log_id', record.get('log_id'))}'>"
                    f"  <span class='dg-log-related-time'>{_escape(_format_timestamp(record.get('event_timestamp')))}</span>"
                    f"  <span class='dg-log-related-message'>{_escape(record.get('message'))}</span>"
                    f"</a>"
                )
            related_html = (
                "<div class='dg-log-detail-block'>"
                "<div class='dg-log-detail-label'>Related events</div>"
                f"{''.join(related_rows)}"
                "</div>"
            )

    actions = [
        f"<button class='dg-log-action copy' data-copy-text='{_escape(_pretty_json(selected.get('payload_json')))}'>Copy JSON</button>",
    ]
    if selected.get("correlation_id"):
        actions.append(
            f"<button class='dg-log-action copy' data-copy-text='{_escape(selected.get('correlation_id'))}'>Copy correlation ID</button>"
        )
    if selected.get("validation_id"):
        actions.append(
            f"<a class='dg-log-action' href='{_build_href('quick_validation_id', selected.get('validation_id'))}'>Filter by validation ID</a>"
        )
    rule_identifier = _rule_identifier(selected)
    if rule_identifier and rule_identifier != "--":
        actions.append(f"<a class='dg-log-action' href='{_build_href('quick_rule_id', rule_identifier)}'>Filter by rule ID</a>")
    actions.append(
        f"<a class='dg-log-action' href='{_build_href('quick_only_severity', selected.get('severity') or 'INFO')}'>Show only this severity</a>"
    )

    navigation = []
    if previous_id is not None:
        navigation.append(f"<a class='dg-log-nav' href='{_build_href('selected_log_id', previous_id)}'>Previous</a>")
    if next_id is not None:
        navigation.append(f"<a class='dg-log-nav' href='{_build_href('selected_log_id', next_id)}'>Next</a>")

    detail_parts = [
        "<div class='dg-log-detail-header'>",
        f"<div class='dg-log-detail-title'>{_escape(selected.get('message') or '(no message)')}</div>",
        f"<div class='dg-log-detail-meta'>{_escape(_format_timestamp(selected.get('event_timestamp')))}</div>",
        "</div>",
        f"<div class='dg-log-detail-actions'>{''.join(actions)}</div>",
        "<div class='dg-log-detail-grid'>",
        _build_detail_section("Severity", selected.get("severity")),
        _build_detail_section("Validation status", selected.get("validation_status")),
        _build_detail_section("Validation ID", selected.get("validation_id")),
        _build_detail_section("Correlation ID", selected.get("correlation_id")),
        _build_detail_section("Rule ID", _rule_identifier(selected)),
        _build_detail_section("Entity ID", selected.get("entity_id") or selected.get("record_id")),
        _build_detail_section("Source module", selected.get("source_module")),
        _build_detail_section("Duration", f"{selected.get('duration_ms')} ms" if selected.get("duration_ms") not in (None, "") else None),
        "</div>",
        _build_detail_section("Input summary", _pretty_json(selected.get("input_summary")), code=True),
        _build_detail_section("Output summary", _pretty_json(selected.get("output_summary")), code=True),
        _build_detail_section("Structured JSON payload", _pretty_json(selected.get("payload_json")), code=True),
        _build_detail_section("Exception type", selected.get("exception_type")),
        _build_detail_section("Stack trace", selected.get("stack_trace"), code=True, collapsible=True),
        related_html,
        f"<div class='dg-log-detail-footer'>{''.join(navigation)}</div>",
    ]
    return "".join(part for part in detail_parts if part)


def render_log_workspace_html(
    *,
    records: list[dict[str, Any]],
    selected_log_id: int | None,
    group_mode: str,
    live_mode: bool,
    auto_scroll: bool,
    connection_state: str,
) -> str:
    grouped = _group_records(records, group_mode)
    stream_parts = []
    for group in grouped:
        group_class = SEVERITY_CLASS.get(group["worst_severity"], "info")
        stream_parts.append(
            "<details class='dg-log-group' open>"
            f"<summary><span>{_escape(group['label'])}</span>"
            f"<span class='dg-log-group-meta'>"
            f"<span class='dg-log-chip severity {group_class}'>{_escape(group['worst_severity'])}</span>"
            f"<span class='dg-log-chip mono'>{len(group['records'])} events</span>"
            "</span></summary>"
            f"{''.join(_row_html(record, selected_log_id) for record in group['records'])}"
            "</details>"
        )

    log_ids = [record.get("log_id") for record in records if record.get("log_id") is not None]
    state_key = f"dataguard-log-workspace-{group_mode}"
    selected = next((record for record in records if record.get("log_id") == selected_log_id), None)
    selected_log_id = selected.get("log_id") if selected else selected_log_id

    return f"""
    <style>
        .dg-log-shell {{
            display: grid;
            grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.95fr);
            gap: 18px;
            min-height: 780px;
            font-family: var(--font-body, sans-serif);
        }}
        .dg-log-pane {{
            background: var(--bg-raised, #0e1018);
            border: 1px solid var(--border-subtle, #1a1e2e);
            border-radius: 18px;
            overflow: hidden;
        }}
        .dg-log-pane-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            padding: 14px 16px;
            border-bottom: 1px solid var(--border-subtle, #1a1e2e);
            background: linear-gradient(180deg, rgba(79,111,255,0.08), rgba(79,111,255,0.01));
        }}
        .dg-log-pane-title {{
            color: var(--text-primary, #eaedf5);
            font-weight: 600;
            font-size: 0.96rem;
        }}
        .dg-log-pane-sub {{
            color: var(--text-secondary, #8b91aa);
            font-family: var(--font-mono, monospace);
            font-size: 0.72rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}
        .dg-log-status-row {{
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }}
        .dg-log-jump {{
            display: none;
            border: 1px solid rgba(79,111,255,0.34);
            background: rgba(79,111,255,0.12);
            color: #e6ebff;
            border-radius: 999px;
            padding: 6px 10px;
            cursor: pointer;
            font-size: 0.74rem;
            text-decoration: none;
        }}
        .dg-log-jump.visible {{
            display: inline-flex;
        }}
        .dg-log-stream {{
            height: 720px;
            overflow-y: auto;
            padding: 12px;
            background:
                radial-gradient(circle at top right, rgba(224,64,96,0.08), transparent 22%),
                radial-gradient(circle at bottom left, rgba(79,111,255,0.06), transparent 20%);
        }}
        .dg-log-group {{
            margin-bottom: 14px;
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 14px;
            background: rgba(255,255,255,0.02);
        }}
        .dg-log-group summary {{
            list-style: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            cursor: pointer;
            padding: 12px 14px;
            color: var(--text-primary, #eaedf5);
            font-weight: 600;
        }}
        .dg-log-group summary::-webkit-details-marker {{
            display: none;
        }}
        .dg-log-group-meta {{
            display: flex;
            gap: 8px;
            align-items: center;
            flex-wrap: wrap;
        }}
        .dg-log-row {{
            border-top: 1px solid rgba(255,255,255,0.04);
            transition: transform 0.18s ease, background 0.18s ease, border-color 0.18s ease;
        }}
        .dg-log-row.is-new {{
            animation: dg-log-flash 1.2s ease;
        }}
        .dg-log-row:hover {{
            background: rgba(255,255,255,0.03);
        }}
        .dg-log-row.selected {{
            background: rgba(79,111,255,0.08);
            border-left: 3px solid #4f6fff;
        }}
        .dg-log-row-main {{
            display: block;
            padding: 12px 14px;
            text-decoration: none;
            color: inherit;
        }}
        .dg-log-row-message {{
            color: var(--text-primary, #eaedf5);
            font-size: 0.9rem;
            line-height: 1.45;
            margin-bottom: 8px;
        }}
        .dg-log-row-meta {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .dg-log-chip {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 9px;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.08);
            color: var(--text-secondary, #8b91aa);
            font-size: 0.68rem;
            text-decoration: none;
            background: rgba(255,255,255,0.02);
        }}
        .dg-log-chip.mono {{
            font-family: var(--font-mono, monospace);
        }}
        .dg-log-chip.severity.debug {{
            color: #9ca3af;
            border-color: rgba(156,163,175,0.24);
            background: rgba(156,163,175,0.12);
        }}
        .dg-log-chip.severity.info {{
            color: #7dd3fc;
            border-color: rgba(56,189,248,0.24);
            background: rgba(56,189,248,0.12);
        }}
        .dg-log-chip.severity.warning {{
            color: #facc15;
            border-color: rgba(250,204,21,0.28);
            background: rgba(250,204,21,0.12);
        }}
        .dg-log-chip.severity.error {{
            color: #fb7185;
            border-color: rgba(251,113,133,0.28);
            background: rgba(251,113,133,0.12);
        }}
        .dg-log-chip.severity.critical {{
            color: #f5d0fe;
            border-color: rgba(217,70,239,0.34);
            background: rgba(190,24,93,0.24);
            box-shadow: 0 0 0 1px rgba(190,24,93,0.2) inset;
        }}
        .dg-log-chip.status.started {{
            color: #fde68a;
            background: rgba(234,179,8,0.12);
        }}
        .dg-log-chip.status.passed,
        .dg-log-chip.status.completed {{
            color: #86efac;
            background: rgba(34,197,94,0.12);
        }}
        .dg-log-chip.status.failed {{
            color: #fca5a5;
            background: rgba(239,68,68,0.12);
        }}
        .dg-log-detail {{
            height: 100%;
            display: flex;
            flex-direction: column;
        }}
        .dg-log-detail-scroll {{
            padding: 16px;
            height: 720px;
            overflow-y: auto;
        }}
        .dg-log-detail-header {{
            margin-bottom: 14px;
        }}
        .dg-log-detail-title {{
            color: var(--text-primary, #eaedf5);
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.45;
        }}
        .dg-log-detail-meta {{
            color: var(--text-secondary, #8b91aa);
            font-family: var(--font-mono, monospace);
            font-size: 0.74rem;
            margin-top: 8px;
        }}
        .dg-log-detail-actions {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 16px;
        }}
        .dg-log-action,
        .dg-log-nav {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            padding: 8px 12px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            color: var(--text-primary, #eaedf5);
            background: rgba(255,255,255,0.03);
            cursor: pointer;
            font-size: 0.74rem;
        }}
        .dg-log-action.copy {{
            appearance: none;
        }}
        .dg-log-detail-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin-bottom: 14px;
        }}
        .dg-log-detail-block {{
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 14px;
            padding: 12px;
            margin-bottom: 12px;
        }}
        .dg-log-detail-label {{
            color: var(--text-secondary, #8b91aa);
            font-family: var(--font-mono, monospace);
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 8px;
        }}
        .dg-log-detail-value {{
            color: var(--text-primary, #eaedf5);
            font-size: 0.9rem;
            word-break: break-word;
        }}
        .dg-log-detail-block pre {{
            margin: 0;
            white-space: pre-wrap;
            word-break: break-word;
            font-size: 0.77rem;
            line-height: 1.55;
            color: #dbe6ff;
            font-family: var(--font-mono, monospace);
        }}
        .dg-log-related-row {{
            display: grid;
            grid-template-columns: 128px 1fr;
            gap: 10px;
            padding: 8px 0;
            color: inherit;
            text-decoration: none;
            border-top: 1px solid rgba(255,255,255,0.03);
        }}
        .dg-log-related-time {{
            font-family: var(--font-mono, monospace);
            font-size: 0.68rem;
            color: var(--text-secondary, #8b91aa);
        }}
        .dg-log-related-message {{
            color: var(--text-primary, #eaedf5);
            font-size: 0.82rem;
        }}
        .dg-log-detail-footer {{
            display: flex;
            gap: 10px;
            justify-content: flex-end;
            margin-top: 12px;
        }}
        .dg-log-empty-title {{
            color: var(--text-primary, #eaedf5);
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .dg-log-empty-text {{
            color: var(--text-secondary, #8b91aa);
            line-height: 1.55;
        }}
        @keyframes dg-log-flash {{
            0% {{ background: rgba(79,111,255,0.18); }}
            100% {{ background: transparent; }}
        }}
        @media (max-width: 1100px) {{
            .dg-log-shell {{
                grid-template-columns: 1fr;
            }}
            .dg-log-stream,
            .dg-log-detail-scroll {{
                height: auto;
                max-height: 520px;
            }}
            .dg-log-detail-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
    <div class="dg-log-shell" data-log-workspace="true" data-state-key="{_escape(state_key)}" data-log-ids="{_escape(json.dumps(log_ids))}" data-live="{str(live_mode).lower()}" data-auto-scroll="{str(auto_scroll).lower()}">
        <section class="dg-log-pane">
            <div class="dg-log-pane-header">
                <div>
                    <div class="dg-log-pane-title">Live log stream</div>
                    <div class="dg-log-pane-sub">Status: {_escape(connection_state)}</div>
                </div>
                <div class="dg-log-status-row">
                    <span class="dg-log-chip mono">{len(records)} events</span>
                    <button class="dg-log-jump" type="button">Jump to latest</button>
                </div>
            </div>
            <div class="dg-log-stream">
                {''.join(stream_parts) if stream_parts else "<div class='dg-log-empty-text'>No logs match current filters.</div>"}
            </div>
        </section>
        <section class="dg-log-pane dg-log-detail">
            <div class="dg-log-pane-header">
                <div>
                    <div class="dg-log-pane-title">Event details</div>
                    <div class="dg-log-pane-sub">Structured drill-down</div>
                </div>
                <div class="dg-log-status-row">
                    <span class="dg-log-chip mono">{_escape(selected_log_id or '--')}</span>
                </div>
            </div>
            <div class="dg-log-detail-scroll">
                {_detail_html(records, selected_log_id)}
            </div>
        </section>
    </div>
    <script>
        (() => {{
            const root = document.querySelector("[data-log-workspace='true']");
            if (!root) return;

            const stream = root.querySelector(".dg-log-stream");
            const jumpButton = root.querySelector(".dg-log-jump");
            const stateKey = root.dataset.stateKey;
            const rowIds = JSON.parse(root.dataset.logIds || "[]");
            const liveMode = root.dataset.live === "true";
            const autoScrollEnabled = root.dataset.autoScroll === "true";

            let stored = {{}};
            try {{
                stored = JSON.parse(localStorage.getItem(stateKey) || "{{}}");
            }} catch (error) {{
                stored = {{}};
            }}

            const previousIds = Array.isArray(stored.rowIds) ? stored.rowIds : [];
            const newIds = rowIds.filter((id) => !previousIds.includes(id));

            root.querySelectorAll(".dg-log-row").forEach((row) => {{
                const rowId = Number(row.dataset.logId);
                if (newIds.includes(rowId)) {{
                    row.classList.add("is-new");
                }}
            }});

            const persist = () => {{
                if (!stream) return;
                const nextState = {{
                    rowIds,
                    scrollTop: stream.scrollTop,
                    autoPaused: stored.autoPaused === true,
                    pendingCount: stored.pendingCount || 0,
                }};
                localStorage.setItem(stateKey, JSON.stringify(nextState));
            }};

            const updateJumpButton = () => {{
                if (!jumpButton || !stream) return;
                const pendingCount = stored.pendingCount || 0;
                if (pendingCount > 0 || stored.autoPaused === true) {{
                    jumpButton.classList.add("visible");
                    jumpButton.textContent = pendingCount > 0 ? `${{pendingCount}} new logs` : "Jump to latest";
                }} else {{
                    jumpButton.classList.remove("visible");
                    jumpButton.textContent = "Jump to latest";
                }}
            }};

            if (stream) {{
                if (typeof stored.scrollTop === "number" && stored.autoPaused === true) {{
                    stream.scrollTop = stored.scrollTop;
                }} else if (liveMode && autoScrollEnabled) {{
                    stream.scrollTop = stream.scrollHeight;
                    stored.pendingCount = 0;
                    stored.autoPaused = false;
                }}

                if (stored.autoPaused === true && newIds.length > 0) {{
                    stored.pendingCount = (stored.pendingCount || 0) + newIds.length;
                }}

                stream.addEventListener("scroll", () => {{
                    const distanceFromBottom = stream.scrollHeight - stream.scrollTop - stream.clientHeight;
                    stored.autoPaused = distanceFromBottom > 28;
                    if (!stored.autoPaused) {{
                        stored.pendingCount = 0;
                    }}
                    persist();
                    updateJumpButton();
                }});
            }}

            if (jumpButton && stream) {{
                jumpButton.addEventListener("click", () => {{
                    stream.scrollTop = stream.scrollHeight;
                    stored.autoPaused = false;
                    stored.pendingCount = 0;
                    persist();
                    updateJumpButton();
                }});
            }}

            root.querySelectorAll("[data-copy-text]").forEach((button) => {{
                button.addEventListener("click", async () => {{
                    const copyText = button.getAttribute("data-copy-text") || "";
                    try {{
                        await navigator.clipboard.writeText(copyText);
                        const originalText = button.textContent;
                        button.textContent = "Copied";
                        setTimeout(() => {{
                            button.textContent = originalText;
                        }}, 1200);
                    }} catch (error) {{
                        button.textContent = "Copy failed";
                    }}
                }});
            }});

            persist();
            updateJumpButton();
        }})();
    </script>
    """
