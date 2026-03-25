import streamlit as st


def load_css():
    """
    DataGuard Design System — Enterprise Dark Edition
    Typography: Syne (display) + DM Mono (code/labels) + DM Sans (body)
    Palette: Deep graphite base · Electric indigo accent · Warm off-white text
    """
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap" rel="stylesheet">

        <style>
        /* ─────────────────────────────────────────────────────────────
           DESIGN TOKENS
        ───────────────────────────────────────────────────────────── */
        :root {
            /* Surface layers */
            --bg-base:        #090b10;
            --bg-raised:      #0e1018;
            --bg-elevated:    #131620;
            --bg-overlay:     #181c2a;
            --bg-hover:       #1c2133;

            /* Borders */
            --border-subtle:  #1a1e2e;
            --border-default: #222638;
            --border-accent:  #2e3450;

            /* Text */
            --text-primary:   #eaedf5;
            --text-secondary: #8b91aa;
            --text-muted:     #454d68;
            --text-disabled:  #2e3450;

            /* Accent — electric indigo */
            --accent:         #4f6fff;
            --accent-dim:     rgba(79, 111, 255, 0.15);
            --accent-glow:    rgba(79, 111, 255, 0.08);

            /* Semantic */
            --success:        #2ecc71;
            --success-dim:    rgba(46, 204, 113, 0.12);
            --warning:        #f0a500;
            --warning-dim:    rgba(240, 165, 0, 0.12);
            --danger:         #e04060;
            --danger-dim:     rgba(224, 64, 96, 0.12);
            --info:           #38bdf8;
            --info-dim:       rgba(56, 189, 248, 0.12);

            /* Typography */
            --font-display:   'Syne', sans-serif;
            --font-body:      'DM Sans', sans-serif;
            --font-mono:      'DM Mono', monospace;

            /* Radius */
            --radius-sm:      4px;
            --radius-md:      8px;
            --radius-lg:      12px;
            --radius-xl:      16px;

            /* Shadows */
            --shadow-sm:      0 1px 3px rgba(0,0,0,0.5);
            --shadow-md:      0 4px 16px rgba(0,0,0,0.4);
            --shadow-lg:      0 8px 32px rgba(0,0,0,0.5);
        }

        /* ─────────────────────────────────────────────────────────────
           BASE RESET
        ───────────────────────────────────────────────────────────── */
        html, body, [class*="css"] {
            font-family: var(--font-body);
        }

        .stApp {
            background-color: var(--bg-base);
            color: var(--text-secondary);
        }

        /* ─────────────────────────────────────────────────────────────
           SIDEBAR
        ───────────────────────────────────────────────────────────── */
        [data-testid="stSidebar"] {
            background-color: var(--bg-raised) !important;
            border-right: 1px solid var(--border-subtle) !important;
        }

        [data-testid="stSidebar"] .block-container {
            padding: 0 !important;
        }

        /* Brand */
        .dg-brand {
            padding: 28px 22px 22px;
            border-bottom: 1px solid var(--border-subtle);
        }

        .dg-brand-logo {
            font-family: var(--font-display);
            font-weight: 800;
            font-size: 1.2rem;
            color: var(--text-primary);
            letter-spacing: -0.02em;
        }

        .dg-brand-logo span {
            color: var(--accent);
        }

        .dg-brand-tag {
            font-family: var(--font-mono);
            font-size: 0.62rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-top: 3px;
        }

        /* Nav section label */
        .dg-nav-label {
            font-family: var(--font-mono);
            font-size: 0.6rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--text-disabled);
            padding: 20px 22px 6px;
        }

        /* Status pill */
        .dg-status {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 10px 16px;
            padding: 10px 14px;
            border-radius: var(--radius-md);
            border: 1px solid;
            font-family: var(--font-mono);
            font-size: 0.72rem;
        }

        .dg-status.locked {
            background: rgba(224,64,96,0.06);
            border-color: rgba(224,64,96,0.2);
            color: #b05060;
        }

        .dg-status.verified {
            background: rgba(46,204,113,0.06);
            border-color: rgba(46,204,113,0.2);
            color: #3a9e5f;
        }

        .dg-status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .dg-status.locked  .dg-status-dot { background: #b05060; }
        .dg-status.verified .dg-status-dot {
            background: var(--success);
            box-shadow: 0 0 6px rgba(46,204,113,0.6);
            animation: pulse-dot 2.5s ease-in-out infinite;
        }

        @keyframes pulse-dot {
            0%, 100% { opacity: 1; }
            50%       { opacity: 0.45; }
        }

        /* Registry card */
        .dg-registry {
            margin: 10px 16px;
            padding: 12px 14px;
            border-radius: var(--radius-md);
            background: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
        }

        .dg-registry-label {
            font-family: var(--font-mono);
            font-size: 0.6rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 10px;
        }

        .dg-registry-stats {
            display: flex;
            gap: 20px;
        }

        .dg-registry-stat-val {
            font-family: var(--font-display);
            font-weight: 700;
            font-size: 1.4rem;
            color: var(--text-primary);
            line-height: 1;
        }

        .dg-registry-stat-key {
            font-family: var(--font-mono);
            font-size: 0.65rem;
            color: var(--text-muted);
            margin-top: 3px;
        }

        /* ─────────────────────────────────────────────────────────────
           MAIN CONTENT
        ───────────────────────────────────────────────────────────── */
        .main .block-container {
            padding: 40px 44px 60px !important;
            max-width: 1280px !important;
        }

        /* ─────────────────────────────────────────────────────────────
           PAGE HEADER
        ───────────────────────────────────────────────────────────── */
        .dg-page-header {
            margin-bottom: 36px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border-subtle);
        }

        .dg-page-eyebrow {
            font-family: var(--font-mono);
            font-size: 0.65rem;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            color: var(--accent);
            margin-bottom: 8px;
        }

        .dg-page-title {
            font-family: var(--font-display);
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.025em;
            line-height: 1.2;
            margin: 0;
        }

        .dg-page-desc {
            font-family: var(--font-mono);
            font-size: 0.78rem;
            color: var(--text-muted);
            margin-top: 6px;
            letter-spacing: 0.02em;
        }

        /* ─────────────────────────────────────────────────────────────
           SECTION LABELS
        ───────────────────────────────────────────────────────────── */
        .dg-section-label {
            font-family: var(--font-mono);
            font-size: 0.62rem;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .dg-section-label::after {
            content: '';
            flex: 1;
            height: 1px;
            background: var(--border-subtle);
        }

        /* ─────────────────────────────────────────────────────────────
           METRIC CARDS
        ───────────────────────────────────────────────────────────── */
        .dg-metric {
            background: var(--bg-raised);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            padding: 22px 24px;
            position: relative;
            overflow: hidden;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .dg-metric::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: var(--accent);
            opacity: 0;
            transition: opacity 0.2s;
        }

        .dg-metric:hover {
            border-color: var(--border-accent);
            box-shadow: var(--shadow-md);
        }

        .dg-metric:hover::before { opacity: 1; }

        .dg-metric.error::before   { background: var(--danger);  opacity: 0.6; }
        .dg-metric.warning::before { background: var(--warning); opacity: 0.6; }
        .dg-metric.success::before { background: var(--success); opacity: 0.6; }

        .dg-metric-label {
            font-family: var(--font-mono);
            font-size: 0.62rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 10px;
        }

        .dg-metric-value {
            font-family: var(--font-display);
            font-weight: 700;
            font-size: 2rem;
            color: var(--text-primary);
            letter-spacing: -0.02em;
            line-height: 1;
        }

        .dg-metric.error   .dg-metric-value { color: var(--danger);  }
        .dg-metric.warning .dg-metric-value { color: var(--warning); }
        .dg-metric.success .dg-metric-value { color: var(--success); }

        .dg-metric-sub {
            font-family: var(--font-mono);
            font-size: 0.65rem;
            color: var(--text-muted);
            margin-top: 6px;
        }

        /* ─────────────────────────────────────────────────────────────
           CARDS (generic containers)
        ───────────────────────────────────────────────────────────── */
        .dg-card {
            background: var(--bg-raised);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            padding: 24px;
            margin-bottom: 16px;
        }

        .dg-card-title {
            font-family: var(--font-display);
            font-size: 0.82rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--text-secondary);
            margin-bottom: 16px;
        }

        /* ─────────────────────────────────────────────────────────────
           BADGES
        ───────────────────────────────────────────────────────────── */
        .dg-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 9px;
            border-radius: var(--radius-sm);
            font-family: var(--font-mono);
            font-size: 0.68rem;
            font-weight: 500;
            letter-spacing: 0.06em;
            border: 1px solid;
        }

        .dg-badge.error   { background: var(--danger-dim);  border-color: rgba(224,64,96,0.3);  color: var(--danger);  }
        .dg-badge.success { background: var(--success-dim); border-color: rgba(46,204,113,0.3); color: var(--success); }
        .dg-badge.warning { background: var(--warning-dim); border-color: rgba(240,165,0,0.3);  color: var(--warning); }
        .dg-badge.info    { background: var(--info-dim);    border-color: rgba(56,189,248,0.3);  color: var(--info);    }
        .dg-badge.neutral { background: var(--bg-elevated); border-color: var(--border-default); color: var(--text-secondary); }

        /* ─────────────────────────────────────────────────────────────
           STREAMLIT OVERRIDES
        ───────────────────────────────────────────────────────────── */

        /* --- Buttons --- */
        .stButton > button {
            font-family: var(--font-body) !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.02em !important;
            padding: 9px 20px !important;
            border-radius: var(--radius-md) !important;
            border: 1px solid var(--border-default) !important;
            background: var(--bg-elevated) !important;
            color: var(--text-secondary) !important;
            transition: all 0.15s ease !important;
            box-shadow: none !important;
            text-transform: none !important;
            text-shadow: none !important;
        }

        .stButton > button:hover {
            background: var(--bg-hover) !important;
            border-color: var(--border-accent) !important;
            color: var(--text-primary) !important;
        }

        .stButton > button[kind="primary"] {
            background: var(--accent) !important;
            border-color: var(--accent) !important;
            color: #fff !important;
        }

        .stButton > button[kind="primary"]:hover {
            background: #6080ff !important;
            border-color: #6080ff !important;
        }

        /* --- Inputs --- */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stTextArea > div > div > textarea {
            background: var(--bg-base) !important;
            border: 1px solid var(--border-default) !important;
            border-radius: var(--radius-md) !important;
            color: var(--text-primary) !important;
            font-family: var(--font-body) !important;
            font-size: 0.85rem !important;
            padding: 10px 14px !important;
            transition: border-color 0.15s !important;
        }

        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 3px var(--accent-dim) !important;
        }

        /* input[type=password] masking dots */
        input[type="password"] {
            font-family: var(--font-mono) !important;
            letter-spacing: 0.2em !important;
        }

        /* --- Labels --- */
        .stTextInput label, .stNumberInput label,
        .stTextArea label, .stSelectbox label,
        .stFileUploader label, .stCheckbox label {
            font-family: var(--font-mono) !important;
            font-size: 0.65rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.14em !important;
            text-transform: uppercase !important;
            color: var(--text-muted) !important;
        }

        /* --- Selectbox --- */
        .stSelectbox > div > div {
            background: var(--bg-base) !important;
            border: 1px solid var(--border-default) !important;
            border-radius: var(--radius-md) !important;
            color: var(--text-primary) !important;
        }

        div[data-baseweb="select"] span { color: var(--text-primary) !important; }
        div[data-baseweb="select"] svg  { fill: var(--text-muted) !important; }

        ul[data-baseweb="menu"] {
            background: var(--bg-elevated) !important;
            border: 1px solid var(--border-default) !important;
            border-radius: var(--radius-md) !important;
        }

        li[role="option"] { color: var(--text-secondary) !important; font-size: 0.85rem !important; }

        li[role="option"]:hover,
        li[role="option"][aria-selected="true"] {
            background: var(--accent-dim) !important;
            color: var(--text-primary) !important;
            font-weight: 500 !important;
        }

        /* --- File uploader --- */
        [data-testid="stFileUploader"] {
            background: var(--bg-raised) !important;
            border: 1px dashed var(--border-default) !important;
            border-radius: var(--radius-lg) !important;
            transition: border-color 0.2s, background 0.2s !important;
        }

        [data-testid="stFileUploader"]:hover {
            border-color: var(--accent) !important;
            background: var(--accent-glow) !important;
        }

        /* --- Dataframe --- */
        [data-testid="stDataFrame"] {
            border: 1px solid var(--border-subtle) !important;
            border-radius: var(--radius-lg) !important;
            overflow: hidden !important;
        }

        /* --- Metrics --- */
        .stMetric {
            background: var(--bg-raised) !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: var(--radius-lg) !important;
            padding: 20px !important;
        }

        .stMetric label {
            font-family: var(--font-mono) !important;
            font-size: 0.62rem !important;
            color: var(--text-muted) !important;
            text-transform: uppercase !important;
            letter-spacing: 0.14em !important;
        }

        .stMetric [data-testid="stMetricValue"] {
            font-family: var(--font-display) !important;
            font-size: 1.8rem !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
        }

        /* --- Alerts --- */
        .stAlert {
            border-radius: var(--radius-md) !important;
            font-size: 0.82rem !important;
            font-family: var(--font-body) !important;
        }

        /* --- Expander --- */
        .streamlit-expanderHeader {
            background: var(--bg-raised) !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: var(--radius-md) !important;
            color: var(--text-secondary) !important;
            font-family: var(--font-body) !important;
            font-size: 0.85rem !important;
        }

        /* --- Tabs --- */
        .stTabs [data-baseweb="tab-list"] {
            background: transparent !important;
            gap: 2px !important;
            border-bottom: 1px solid var(--border-subtle) !important;
        }

        .stTabs [data-baseweb="tab"] {
            font-family: var(--font-body) !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            color: var(--text-muted) !important;
            background: transparent !important;
            border: none !important;
            border-radius: 0 !important;
            padding: 10px 18px !important;
            transition: color 0.15s !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: var(--text-secondary) !important;
        }

        .stTabs [aria-selected="true"] {
            color: var(--text-primary) !important;
            border-bottom: 2px solid var(--accent) !important;
            background: transparent !important;
        }

        /* --- Progress --- */
        .stProgress > div > div > div {
            background: var(--accent) !important;
            border-radius: 999px !important;
        }

        /* --- Download button --- */
        .stDownloadButton > button {
            background: var(--bg-elevated) !important;
            border: 1px solid var(--border-default) !important;
            color: var(--text-secondary) !important;
            border-radius: var(--radius-md) !important;
            font-family: var(--font-body) !important;
            font-size: 0.82rem !important;
        }

        .stDownloadButton > button:hover {
            border-color: var(--accent) !important;
            color: var(--text-primary) !important;
        }

        /* --- Divider --- */
        hr {
            border-color: var(--border-subtle) !important;
            margin: 28px 0 !important;
        }

        /* ─────────────────────────────────────────────────────────────
           BOOT LOADER
        ───────────────────────────────────────────────────────────── */
        .dg-loader-wrap {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 60vh;
            gap: 24px;
        }

        .dg-loader-title {
            font-family: var(--font-display);
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.02em;
        }

        .dg-loader-title span { color: var(--accent); }

        .dg-spinner {
            width: 44px;
            height: 44px;
            border: 3px solid var(--border-default);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.9s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .dg-loader-step {
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: var(--text-muted);
            letter-spacing: 0.06em;
        }

        /* ─────────────────────────────────────────────────────────────
           ACTION BAR (pill group)
        ───────────────────────────────────────────────────────────── */
        .dg-pill-bar {
            display: flex;
            gap: 4px;
            background: var(--bg-raised);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            padding: 4px;
            width: fit-content;
            margin-bottom: 24px;
        }

        .dg-pill {
            padding: 6px 16px;
            border-radius: var(--radius-md);
            font-size: 0.78rem;
            font-weight: 500;
            font-family: var(--font-body);
            cursor: pointer;
            color: var(--text-muted);
            border: none;
            background: transparent;
            transition: all 0.15s;
        }

        .dg-pill.active {
            background: var(--bg-overlay);
            color: var(--text-primary);
        }

        /* ─────────────────────────────────────────────────────────────
           GLOBAL CHROME
        ───────────────────────────────────────────────────────────── */
        #MainMenu  { visibility: hidden; }
        footer     { visibility: hidden; }
        header     { visibility: hidden; }

        /* Scrollbar */
        ::-webkit-scrollbar       { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: var(--bg-base); }
        ::-webkit-scrollbar-thumb { background: var(--border-default); border-radius: 99px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--border-accent); }
        </style>
        """,
        unsafe_allow_html=True,
    )