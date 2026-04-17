from components.sidebar import render_sidebar
render_sidebar()

import streamlit as st
import pandas as pd
from services.validation_service import ValidationService
from utils.styles import load_css

load_css()

# ── Connection guard ──────────────────────────────────────────────────────────
if "connected" not in st.session_state:
    st.session_state.connected = False
if not st.session_state.get("boot_complete", False):
    st.stop()


# ── Helpers ───────────────────────────────────────────────────────────────────
def metric_card(value: str, label: str, variant: str = "", sub: str = ""):
    sub_html = f'<div class="dg-metric-sub">{sub}</div>' if sub else ""
    st.markdown(
        f"""
        <div class="dg-metric {variant}">
            <div class="dg-metric-label">{label}</div>
            <div class="dg-metric-value">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def run_validations():
    with st.spinner("Executing validation rules…"):
        result = ValidationService.run_all_validations()
        if result.get("success"):
            errors  = result.get("total_errors", 0)
            records = result.get("records_scanned", 0)
            st.success(f"Complete · {errors:,} errors across {records:,} records")
        else:
            st.error(result.get("error", "Validation failed"))
    st.rerun()


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="dg-page-header">
        <div class="dg-page-eyebrow">Executive Dashboard</div>
        <div class="dg-page-title">System Overview</div>
        <div class="dg-page-desc">Real-time health metrics and validation activity across all contexts.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Data retrieval ────────────────────────────────────────────────────────────
metrics    = ValidationService.get_metrics()
records    = metrics.get("records_scanned", 0)
errors     = metrics.get("errors", 0)
rules      = metrics.get("rules", 0)
minutes    = metrics.get("minutes_ago", 0)
error_rate = min(100.0, errors / max(records, 1) * 100)

health       = "Healthy"  if error_rate < 1 else "Warning"  if error_rate < 5 else "Critical"
health_var   = "success"  if health == "Healthy" else "warning" if health == "Warning" else "error"
error_var    = "success"  if errors == 0 else "warning" if errors < 50 else "error"
rate_var     = "success"  if error_rate < 1 else "warning" if error_rate < 5 else "error"

# ─────────────────────────────────────────────────────────────────────────────
# ROW 1 — System Health
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">System Health</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1: metric_card(str(rules),           "Active Rules",   "",         "validation rules loaded")
with c2: metric_card(f"{errors:,}",        "Total Errors",   error_var,  "across all tables")
with c3: metric_card(f"{minutes}m ago",    "Last Run",       "",         "most recent execution")
with c4: metric_card(f"{error_rate:.1f}%", "Error Rate",     rate_var,   "errors / records")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 2 — Volume + Overall Status
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Volume & Status</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2, gap="medium")
with c1: metric_card(f"{records:,}", "Records Scanned", "", "total rows evaluated")
with c2: metric_card(health,         "System Health",   health_var, f"error rate {error_rate:.2f}%")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 3 — Quick Actions
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Quick Actions</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 1, 2], gap="medium")
with c1:
    if st.button("▶  Run Validations", type="primary", use_container_width=True):
        run_validations()
with c2:
    if st.button("↺  Refresh Data", use_container_width=True):
        st.rerun()
with c3:
    st.markdown(
        f"""
        <div class="dg-card" style="padding:14px 18px;margin:0;">
            <span class="dg-badge {health_var}">{health}</span>
            <span style="font-size:0.8rem;color:var(--text-muted);margin-left:10px;">
                {rules} rules active · last scan {minutes}m ago
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 4 — Insights
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Insights</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2, gap="medium")

# ── LEFT: Errors by Table (horizontal bar breakdown) ─────────────────────────
with c1:
    table_summary = ValidationService.get_error_summary_by_table()
    if not table_summary.empty:
        max_errors = int(table_summary["error_count"].max()) if not table_summary.empty else 1
        total_errors_all = int(table_summary["error_count"].sum())

        rows_html = ""
        for _, row in table_summary.iterrows():
            tname = row["table_name"]
            ecount = int(row["error_count"])
            affected = int(row["affected_records"])
            pct = round(ecount / max(total_errors_all, 1) * 100, 1)
            bar_w = max(4, round(ecount / max(max_errors, 1) * 100))

            # Color intensity based on proportion
            if pct > 50:
                bar_color = "var(--danger)"
                bar_bg = "var(--danger-dim)"
            elif pct > 25:
                bar_color = "var(--warning)"
                bar_bg = "var(--warning-dim)"
            else:
                bar_color = "var(--accent)"
                bar_bg = "var(--accent-dim)"

            rows_html += f"""
            <div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--border-subtle);">
                <div style="min-width:140px;font-size:0.78rem;color:var(--text-secondary);font-family:var(--font-mono);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{tname}">{tname}</div>
                <div style="flex:1;height:22px;background:{bar_bg};border-radius:4px;overflow:hidden;position:relative;">
                    <div style="width:{bar_w}%;height:100%;background:{bar_color};border-radius:4px;transition:width 0.5s ease;"></div>
                </div>
                <div style="min-width:45px;text-align:right;font-family:var(--font-display);font-weight:700;font-size:0.9rem;color:var(--text-primary);">{ecount:,}</div>
                <div style="min-width:55px;text-align:right;font-size:0.68rem;color:var(--text-muted);font-family:var(--font-mono);">{pct}%</div>
            </div>
            """

        st.markdown(
            f"""
            <div class="dg-card" style="padding:20px 22px;">
                <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px;">
                    <div class="dg-card-title" style="margin:0;">Errors by Table</div>
                    <div style="font-family:var(--font-mono);font-size:0.65rem;color:var(--text-muted);">{total_errors_all:,} total across {len(table_summary)} tables</div>
                </div>
                {rows_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="dg-card" style="padding:20px 22px;">
                <div class="dg-card-title" style="margin-bottom:12px;">Errors by Table</div>
                <div style="display:flex;align-items:center;justify-content:center;min-height:120px;">
                    <span class="dg-badge success" style="font-size:0.82rem;padding:10px 18px;">✓ No errors recorded</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── RIGHT: Error Rate Timeline ───────────────────────────────────────────────
with c2:
    trend_df = ValidationService.get_error_trend(days=14)

    trend_direction = "stable"
    trend_badge = "neutral"
    trend_icon = "→"
    if len(trend_df) >= 3:
        last_three = trend_df.tail(3)["error_rate"].astype(float).tolist()
        if last_three[0] < last_three[1] < last_three[2]:
            trend_direction = "degrading"
            trend_badge = "error"
            trend_icon = "↗"
        elif last_three[0] > last_three[1] > last_three[2]:
            trend_direction = "improving"
            trend_badge = "success"
            trend_icon = "↘"

    if not trend_df.empty:
        latest_rate = float(trend_df.iloc[-1]["error_rate"]) * 100
        peak_rate = float(trend_df["error_rate"].max()) * 100
        avg_rate = float(trend_df["error_rate"].mean()) * 100
        run_count = len(trend_df)

        # Build sparkline dots
        rates = trend_df["error_rate"].astype(float).tolist()
        max_r = max(rates) if rates else 1
        dots_html = ""
        for i, r in enumerate(rates):
            h = max(4, round((r / max(max_r, 0.001)) * 44))
            ts = pd.to_datetime(trend_df.iloc[i]["run_timestamp"]).strftime("%b %d %H:%M")
            rate_pct = round(r * 100, 2)

            if r * 100 > 5:
                dot_color = "var(--danger)"
            elif r * 100 > 1:
                dot_color = "var(--warning)"
            else:
                dot_color = "var(--success)"

            dots_html += f"""<div title="{ts}: {rate_pct}%" style="display:flex;flex-direction:column;justify-content:flex-end;align-items:center;flex:1;height:48px;cursor:default;">
                <div style="width:100%;max-width:18px;height:{h}px;background:{dot_color};border-radius:3px;transition:height 0.3s ease;opacity:0.85;"></div>
            </div>"""

        # Timeline labels (first and last)
        first_ts = pd.to_datetime(trend_df.iloc[0]["run_timestamp"]).strftime("%b %d")
        last_ts = pd.to_datetime(trend_df.iloc[-1]["run_timestamp"]).strftime("%b %d")

        st.markdown(
            f"""
            <div class="dg-card" style="padding:20px 22px;">
                <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:16px;">
                    <div class="dg-card-title" style="margin:0;">Validation Trend</div>
                    <span class="dg-badge {trend_badge}">{trend_icon} {trend_direction}</span>
                </div>
                <div style="display:flex;gap:16px;margin-bottom:18px;">
                    <div style="flex:1;padding:10px 14px;background:var(--bg-elevated);border-radius:var(--radius-md);border:1px solid var(--border-subtle);">
                        <div style="font-family:var(--font-mono);font-size:0.58rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px;">Latest</div>
                        <div style="font-family:var(--font-display);font-weight:700;font-size:1.2rem;color:{'var(--danger)' if latest_rate > 5 else 'var(--warning)' if latest_rate > 1 else 'var(--success)'};">{latest_rate:.1f}%</div>
                    </div>
                    <div style="flex:1;padding:10px 14px;background:var(--bg-elevated);border-radius:var(--radius-md);border:1px solid var(--border-subtle);">
                        <div style="font-family:var(--font-mono);font-size:0.58rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px;">Peak</div>
                        <div style="font-family:var(--font-display);font-weight:700;font-size:1.2rem;color:var(--text-primary);">{peak_rate:.1f}%</div>
                    </div>
                    <div style="flex:1;padding:10px 14px;background:var(--bg-elevated);border-radius:var(--radius-md);border:1px solid var(--border-subtle);">
                        <div style="font-family:var(--font-mono);font-size:0.58rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px;">Avg</div>
                        <div style="font-family:var(--font-display);font-weight:700;font-size:1.2rem;color:var(--text-primary);">{avg_rate:.1f}%</div>
                    </div>
                </div>
                <div style="display:flex;gap:2px;align-items:flex-end;padding:0 2px;margin-bottom:6px;">
                    {dots_html}
                </div>
                <div style="display:flex;justify-content:space-between;font-family:var(--font-mono);font-size:0.6rem;color:var(--text-muted);">
                    <span>{first_ts}</span>
                    <span style="color:var(--text-disabled);">{run_count} runs</span>
                    <span>{last_ts}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="dg-card" style="padding:20px 22px;">
                <div class="dg-card-title" style="margin-bottom:12px;">Validation Trend</div>
                <div style="display:flex;align-items:center;justify-content:center;min-height:120px;">
                    <span style="font-size:0.82rem;color:var(--text-muted);">No run history available</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 5 — Latest Errors
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="dg-section-label">Latest Errors</div>', unsafe_allow_html=True)

recent_errors = ValidationService.get_recent_errors(10)
if not recent_errors.empty:
    st.dataframe(recent_errors, use_container_width=True, hide_index=True)
else:
    st.markdown(
        '<div class="dg-badge success" style="font-size:0.8rem;padding:8px 14px;">✓ No validation errors found</div>',
        unsafe_allow_html=True,
    )

