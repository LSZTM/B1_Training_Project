import streamlit as st


def load_css():
    """
    DataGuard Design System â€” Enterprise Dark Edition
    Typography: Syne (display) + DM Mono (code/labels) + DM Sans (body)
    Palette: Deep graphite base Â· Electric indigo accent Â· Warm off-white text
    """
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap" rel="stylesheet">

        <style>
        /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
           DESIGN TOKENS
        â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
        :root {
            /* Surface layers */
            --bg-base:        #040507;
            --bg-raised:      #0b0e14;
            --bg-elevated:    #11141b;
            --bg-overlay:     #181c25;
            --bg-hover:       #1e232e;

            /* Borders */
            --border-subtle:  #141820;
            --border-default: #1c222d;
            --border-accent:  #3b4a6b;

            /* Text */
            --text-primary:   #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted:     #475569;
            --text-disabled:  #1e293b;

            /* Accent â€” Electric Indigo */
            --accent:         #6366f1;
            --accent-dim:     rgba(99, 102, 241, 0.12);
            --accent-glow:    rgba(99, 102, 241, 0.06);

            /* Semantic */
            --success:        #06b6d4; /* Cyber Cyan */
            --success-dim:    rgba(6, 182, 212, 0.1);
            --warning:        #f59e0b; /* Amber */
            --warning-dim:    rgba(245, 158, 11, 0.1);
            --danger:         #f43f5e; /* Rose 500 */
            --danger-dim:     rgba(244, 63, 94, 0.12);
            --info:           #0ea5e9; /* Sky */
            --info-dim:       rgba(14, 165, 233, 0.1);

            /* Typography */
            --font-display:   'Syne', sans-serif;
            --font-body:      'DM Sans', sans-serif;
            --font-mono:      'DM Mono', monospace;

            /* Radius */
            --radius-sm:      6px;
            --radius-md:      10px;
            --radius-lg:      14px;
            --radius-xl:      20px;

            /* Shadows & Glows */
            --shadow-sm:      0 1px 3px rgba(0,0,0,0.6);
            --shadow-md:      0 4px 20px rgba(0,0,0,0.5);
            --shadow-lg:      0 8px 32px rgba(0,0,0,0.6);
            --glow-accent:    0 0 15px rgba(99, 102, 241, 0.2);
        }

        /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
           BASE RESET
        â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
        html, body, [class*="css"] {
            font-family: var(--font-body);
        }

        .stApp {
            background-color: var(--bg-base);
            color: var(--text-secondary);
        }

        /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
           SIDEBAR
        â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
        /* --- Sidebar --- */
        [data-testid="stSidebar"] {
            background-color: var(--bg-raised) !important;
            border-right: 1px solid var(--border-subtle) !important;
        }

        /* Hide default Streamlit navigation */
        [data-testid="stSidebarNav"] {
            display: none !important;
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

        /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
           MAIN CONTENT
        â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
        .main .block-container {
            padding: 40px 44px 60px !important;
            max-width: 1280px !important;
        }

        /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
           PAGE HEADER
        â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
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

        /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
           SECTION LABELS
        â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
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

        /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
           METRIC CARDS
        â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
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

        /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
           CARDS (generic containers)
        â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
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

        /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
           BADGES
        â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
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

           BOOT LOADER
        â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
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

        /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
           ACTION BAR (pill group)
        â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
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

        </style>
        """,
        unsafe_allow_html=True,
    )
