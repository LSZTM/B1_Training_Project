import streamlit as st


JAPANDI_COLORS = {
    "bg_base": "#1a1815",
    "bg_alt": "#191714",
    "surface": "#211e19",
    "surface_raised": "#29251f",
    "surface_soft": "#302b24",
    "border": "#40382e",
    "border_soft": "#332d25",
    "text": "#e8e0d4",
    "muted": "#a79b8b",
    "faint": "#756a5d",
    "gold": "#c8a96e",
    "sage": "#8fa982",
    "terracotta": "#c57962",
    "ochre": "#c39a57",
    "debug": "#8d887f",
}


def apply_japandi_plotly_theme(fig, *, accent: str | None = None):
    """Apply the shared DataGuard Japandi chart treatment."""
    color = accent or JAPANDI_COLORS["gold"]
    fig.update_traces(
        marker=dict(color=color),
        line=dict(color=color, width=2),
        selector=dict(type="scatter"),
    )
    fig.update_layout(
        paper_bgcolor=JAPANDI_COLORS["bg_base"],
        plot_bgcolor=JAPANDI_COLORS["surface"],
        font=dict(family="Courier New, Consolas, monospace", color=JAPANDI_COLORS["muted"], size=12),
        margin=dict(l=0, r=0, t=18, b=0),
        colorway=[color, JAPANDI_COLORS["sage"], JAPANDI_COLORS["terracotta"], JAPANDI_COLORS["ochre"]],
        xaxis=dict(
            gridcolor=JAPANDI_COLORS["border_soft"],
            zerolinecolor=JAPANDI_COLORS["border_soft"],
            linecolor=JAPANDI_COLORS["border"],
            tickfont=dict(color=JAPANDI_COLORS["faint"]),
            title_font=dict(color=JAPANDI_COLORS["muted"]),
        ),
        yaxis=dict(
            gridcolor=JAPANDI_COLORS["border_soft"],
            zerolinecolor=JAPANDI_COLORS["border_soft"],
            linecolor=JAPANDI_COLORS["border"],
            tickfont=dict(color=JAPANDI_COLORS["faint"]),
            title_font=dict(color=JAPANDI_COLORS["muted"]),
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=JAPANDI_COLORS["muted"]),
        ),
    )
    return fig


def load_css():
    """
    DataGuard Japandi Dark design system.

    Named component patterns:
    QuietMetricPanel: .dg-metric
    LedgerTable: .dg-ledger / Streamlit dataframe overrides
    SparseCard: .dg-card
    SemanticBorderRow: .dg-row.state-*
    WizardStep: .dg-step
    LogLedgerPane: .dg-log-* in components/log_workspace.py
    """
    st.markdown(
        """
        <style>
        :root {
            --bg-base: #1a1815;
            --bg-alt: #191714;
            --bg-raised: #211e19;
            --bg-elevated: #29251f;
            --bg-soft: #302b24;
            --bg-hover: #383126;

            --border-subtle: #332d25;
            --border-default: #40382e;
            --border-strong: #5b4d3d;

            --text-primary: #e8e0d4;
            --text-secondary: #c9bdad;
            --text-muted: #a79b8b;
            --text-faint: #756a5d;

            --accent: #c8a96e;
            --accent-soft: rgba(200, 169, 110, 0.14);

            --success: #8fa982;
            --success-soft: rgba(143, 169, 130, 0.12);
            --warning: #c39a57;
            --warning-soft: rgba(195, 154, 87, 0.12);
            --danger: #c57962;
            --danger-soft: rgba(197, 121, 98, 0.13);
            --critical: #d08a7f;
            --critical-soft: rgba(208, 138, 127, 0.16);
            --debug: #8d887f;
            --debug-soft: rgba(141, 136, 127, 0.11);

            --font-display: Georgia, 'Times New Roman', serif;
            --font-body: Georgia, 'Times New Roman', serif;
            --font-mono: 'Courier New', Consolas, monospace;

            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --transition: 300ms ease-in-out;
        }

        html, body, [class*="css"], .stApp {
            font-family: var(--font-body);
        }

        .stApp {
            background: var(--bg-base);
            color: var(--text-secondary);
        }

        header {
            background: transparent !important;
        }

        .main .block-container {
            padding: 42px 48px 70px !important;
            max-width: 1260px !important;
        }

        [data-testid="stSidebar"] {
            background: var(--bg-alt) !important;
            border-right: 1px solid var(--border-subtle) !important;
        }

        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        [data-testid="stSidebar"] .block-container {
            padding: 0 !important;
        }

        .dg-brand {
            padding: 30px 22px 24px;
            border-bottom: 1px solid var(--border-subtle);
        }

        .dg-brand-logo {
            font-family: var(--font-display);
            font-size: 1.28rem;
            color: var(--text-primary);
            letter-spacing: 0.01em;
        }

        .dg-brand-logo span {
            color: var(--accent);
        }

        .dg-brand-tag,
        .dg-nav-label,
        .dg-page-eyebrow,
        .dg-section-label,
        .dg-card-title,
        .dg-metric-label,
        .dg-metric-sub,
        .dg-status,
        .dg-badge,
        .dg-kicker,
        .dg-mono,
        .dg-step-index,
        .dg-step-meta {
            font-family: var(--font-mono);
        }

        .dg-brand-tag {
            font-size: 0.62rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--text-faint);
            margin-top: 5px;
        }

        .dg-nav-label {
            font-size: 0.62rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--text-faint);
            padding: 22px 22px 7px;
        }

        .dg-status {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 14px 16px;
            padding: 12px 14px;
            border: 1px solid var(--border-default);
            border-left-width: 2px;
            border-radius: var(--radius-md);
            background: var(--bg-raised);
            color: var(--text-muted);
            font-size: 0.72rem;
        }

        .dg-status.verified {
            border-left-color: var(--success);
        }

        .dg-status.locked {
            border-left-color: var(--danger);
        }

        .dg-status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--text-faint);
            flex-shrink: 0;
        }

        .dg-status.verified .dg-status-dot { background: var(--success); }
        .dg-status.locked .dg-status-dot { background: var(--danger); }

        .dg-registry {
            margin: 12px 16px;
            padding: 14px;
            border-radius: var(--radius-md);
            background: var(--bg-raised);
            border: 1px solid var(--border-subtle);
        }

        .dg-registry-label {
            font-family: var(--font-mono);
            font-size: 0.6rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: var(--text-faint);
            margin-bottom: 12px;
        }

        .dg-registry-stats {
            display: flex;
            gap: 24px;
        }

        .dg-registry-stat-val {
            font-family: var(--font-display);
            font-size: 1.45rem;
            color: var(--text-primary);
            line-height: 1;
        }

        .dg-registry-stat-key {
            font-family: var(--font-mono);
            font-size: 0.64rem;
            color: var(--text-faint);
            margin-top: 5px;
        }

        .dg-page-header {
            position: relative;
            padding-left: 22px;
            margin-bottom: 38px;
            max-width: 880px;
        }

        .dg-page-header::before {
            content: '';
            position: absolute;
            left: 0;
            top: 4px;
            bottom: 6px;
            width: 1px;
            background: rgba(200, 169, 110, 0.6);
        }

        .dg-page-eyebrow {
            font-size: 0.64rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--accent);
            margin-bottom: 10px;
        }

        .dg-page-title {
            font-family: var(--font-display);
            font-size: clamp(2rem, 4vw, 3.45rem);
            color: var(--text-primary);
            letter-spacing: -0.035em;
            line-height: 1.04;
        }

        .dg-page-desc {
            color: var(--text-muted);
            margin-top: 12px;
            font-size: 1rem;
            line-height: 1.65;
            max-width: 720px;
        }

        .dg-section-label {
            display: flex;
            align-items: center;
            gap: 14px;
            color: var(--text-faint);
            font-size: 0.64rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            margin: 28px 0 14px;
        }

        .dg-section-label::after {
            content: '';
            height: 1px;
            flex: 1;
            background: var(--border-subtle);
        }

        .dg-card,
        .dg-metric,
        .dg-step,
        .dg-row,
        div[data-testid="stForm"],
        div[data-testid="stExpander"] {
            background: var(--bg-raised);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
        }

        .dg-card {
            padding: 24px;
            margin-bottom: 16px;
        }

        .dg-card.compact {
            padding: 16px 18px;
        }

        .dg-card-title {
            font-size: 0.66rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--text-faint);
            margin-bottom: 12px;
        }

        .dg-card-copy {
            color: var(--text-muted);
            line-height: 1.68;
            font-size: 0.96rem;
        }

        .dg-metric {
            padding: 22px 24px;
            min-height: 122px;
            transition: background var(--transition), border-color var(--transition);
        }

        .dg-metric:hover,
        .dg-card:hover,
        .dg-row:hover {
            background: var(--bg-elevated);
            border-color: var(--border-default);
        }

        .dg-metric.hero {
            border-left: 1px solid rgba(200, 169, 110, 0.65);
            min-height: 176px;
        }

        .dg-metric-label {
            color: var(--text-faint);
            font-size: 0.64rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 12px;
        }

        .dg-metric-value {
            font-family: var(--font-display);
            color: var(--text-primary);
            font-size: 2.15rem;
            line-height: 1;
            letter-spacing: -0.035em;
            max-width: 100%;
            overflow-wrap: anywhere;
            word-break: break-word;
        }

        .dg-metric.hero .dg-metric-value {
            color: var(--accent);
            font-size: clamp(2.55rem, 5vw, 4.4rem);
            line-height: 0.98;
        }

        .dg-fit-value {
            display: block;
            hyphens: auto;
            white-space: normal;
        }

        .dg-metric.success { border-left: 1px solid var(--success); }
        .dg-metric.warning { border-left: 1px solid var(--warning); }
        .dg-metric.error { border-left: 1px solid var(--danger); }
        .dg-metric.critical { border-left: 1px solid var(--critical); }

        .dg-metric-sub {
            color: var(--text-faint);
            font-size: 0.7rem;
            margin-top: 12px;
        }

        .dg-row {
            padding: 14px 16px;
            margin-bottom: 10px;
            border-left-width: 2px;
        }

        .dg-row.state-pass { border-left-color: var(--success); }
        .dg-row.state-warn { border-left-color: var(--warning); }
        .dg-row.state-fail { border-left-color: var(--danger); }
        .dg-row.state-critical { border-left-color: var(--critical); }
        .dg-row.state-debug { border-left-color: var(--debug); }
        .dg-row.state-neutral { border-left-color: var(--border-default); }

        .dg-row-title {
            color: var(--text-primary);
            font-family: var(--font-mono);
            font-size: 0.84rem;
        }

        .dg-row-meta {
            color: var(--text-faint);
            font-family: var(--font-mono);
            font-size: 0.72rem;
            margin-top: 6px;
        }

        .dg-badge {
            display: inline-flex;
            align-items: center;
            padding: 3px 9px;
            border-radius: var(--radius-sm);
            border: 1px solid var(--border-default);
            color: var(--text-muted);
            background: var(--bg-elevated);
            font-size: 0.68rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .dg-badge.success { color: var(--success); border-color: rgba(143,169,130,0.42); background: var(--success-soft); }
        .dg-badge.warning { color: var(--warning); border-color: rgba(195,154,87,0.44); background: var(--warning-soft); }
        .dg-badge.error { color: var(--danger); border-color: rgba(197,121,98,0.46); background: var(--danger-soft); }
        .dg-badge.critical { color: var(--critical); border-color: rgba(208,138,127,0.56); background: var(--critical-soft); }
        .dg-badge.info { color: var(--text-secondary); border-color: var(--border-default); background: var(--bg-elevated); }
        .dg-badge.neutral { color: var(--text-muted); border-color: var(--border-default); background: var(--bg-elevated); }
        .dg-badge.debug { color: var(--debug); border-color: rgba(141,136,127,0.38); background: var(--debug-soft); }

        .dg-step {
            padding: 18px 20px;
            min-height: 118px;
            transition: border-color var(--transition), background var(--transition);
        }

        .dg-step.active {
            border-left: 1px solid rgba(200, 169, 110, 0.65);
            background: var(--bg-elevated);
        }

        .dg-step.done {
            border-left: 1px solid var(--success);
        }

        .dg-step-index {
            color: var(--accent);
            font-size: 0.7rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 12px;
        }

        .dg-step-title {
            color: var(--text-primary);
            font-size: 1.02rem;
        }

        .dg-step-meta {
            color: var(--text-faint);
            font-size: 0.68rem;
            margin-top: 8px;
        }

        .dg-ledger {
            font-family: var(--font-mono);
            color: var(--text-secondary);
        }

        .dg-empty {
            padding: 34px;
            text-align: center;
            color: var(--text-muted);
            border: 1px solid var(--border-subtle);
            background: var(--bg-raised);
            border-radius: var(--radius-lg);
            font-family: var(--font-mono);
            line-height: 1.6;
        }

        .dg-loader-wrap {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 62vh;
        }

        .dg-loader-card {
            width: min(560px, 92vw);
            padding: 36px;
            background: var(--bg-raised);
            border: 1px solid var(--border-subtle);
            border-left: 1px solid rgba(200, 169, 110, 0.6);
            border-radius: var(--radius-lg);
        }

        .dg-loader-title {
            font-family: var(--font-display);
            font-size: 2rem;
            color: var(--text-primary);
            margin-bottom: 12px;
        }

        .dg-loader-title span {
            color: var(--accent);
        }

        .dg-loader-step {
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: var(--text-muted);
            letter-spacing: 0.04em;
            margin: 12px 0 0;
        }

        .stButton > button,
        .stDownloadButton > button {
            font-family: var(--font-mono) !important;
            border-radius: var(--radius-sm) !important;
            border: 1px solid var(--border-default) !important;
            background: var(--bg-elevated) !important;
            color: var(--text-secondary) !important;
            transition: background var(--transition), border-color var(--transition), color var(--transition) !important;
            box-shadow: none !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stButton > button:focus-visible,
        .stDownloadButton > button:focus-visible {
            background: var(--bg-hover) !important;
            border-color: var(--accent) !important;
            color: var(--text-primary) !important;
        }

        .stButton > button[kind="primary"] {
            background: var(--bg-elevated) !important;
            color: var(--accent) !important;
            border-color: rgba(200, 169, 110, 0.58) !important;
        }

        input,
        textarea,
        select,
        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div,
        [data-baseweb="textarea"] {
            background: var(--bg-elevated) !important;
            color: var(--text-primary) !important;
            border-color: var(--border-default) !important;
            font-family: var(--font-mono) !important;
        }

        label,
        .stMarkdown,
        .stCaption,
        p,
        li {
            color: var(--text-secondary);
        }

        h1, h2, h3, h4 {
            font-family: var(--font-display) !important;
            color: var(--text-primary) !important;
        }

        code,
        pre,
        .stCode,
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            font-family: var(--font-mono) !important;
        }

        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            overflow: hidden;
        }

        div[data-testid="stMetric"] {
            background: var(--bg-raised);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            padding: 16px 18px;
        }

        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
            font-family: var(--font-mono);
            color: var(--text-faint) !important;
        }

        div[data-testid="stMetricValue"] {
            font-family: var(--font-display);
            color: var(--text-primary);
        }

        div[data-testid="stTabs"] button {
            font-family: var(--font-mono) !important;
            color: var(--text-muted) !important;
        }

        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: var(--accent) !important;
            border-bottom-color: var(--accent) !important;
        }

        div[data-testid="stAlert"] {
            background: var(--bg-raised);
            border: 1px solid var(--border-default);
            color: var(--text-secondary);
        }

        div[data-testid="stProgress"] > div > div > div {
            background: var(--accent) !important;
        }

        *:focus-visible {
            outline: 1px solid rgba(200, 169, 110, 0.8) !important;
            outline-offset: 2px !important;
        }

        @media (max-width: 900px) {
            .main .block-container {
                padding: 30px 22px 54px !important;
            }
            .dg-page-title {
                font-size: 2.2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
