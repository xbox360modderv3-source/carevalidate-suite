"""
CareValidate Shared Design System v3
Professional dark theme — single-line HTML vars prevent markdown code-block false positives.
"""
import streamlit as st

# ── Palette ────────────────────────────────────────────────────────────────
BG     = "#07090f"
CARD   = "#0d1117"
CARD2  = "#111827"
BORDER = "rgba(255,255,255,0.07)"
TEXT   = "#f1f5f9"
MUTED  = "#64748b"
BLUE   = "#3b82f6"
GREEN  = "#10b981"
YELLOW = "#f59e0b"
RED    = "#ef4444"
PURPLE = "#8b5cf6"
TEAL   = "#06b6d4"

_COLOR_MAP = {
    "blue":    (BLUE,   "rgba(59,130,246,0.12)",  "rgba(59,130,246,0.30)"),
    "green":   (GREEN,  "rgba(16,185,129,0.12)",  "rgba(16,185,129,0.30)"),
    "yellow":  (YELLOW, "rgba(245,158,11,0.12)",  "rgba(245,158,11,0.30)"),
    "red":     (RED,    "rgba(239,68,68,0.12)",   "rgba(239,68,68,0.30)"),
    "purple":  (PURPLE, "rgba(139,92,246,0.12)",  "rgba(139,92,246,0.30)"),
    "teal":    (TEAL,   "rgba(6,182,212,0.12)",   "rgba(6,182,212,0.30)"),
    "default": (TEXT,   "transparent",            "transparent"),
}

# ── Global CSS ─────────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;0,14..32,800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp, .main {
    background-color: #07090f !important;
}
.main .block-container {
    background-color: #07090f !important;
    padding-top: 0 !important;
    padding-bottom: 48px !important;
    max-width: 1440px !important;
}

/* Dot-grid background texture on main content area */
.main .block-container::before {
    content: '';
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    background-image: radial-gradient(circle, rgba(255,255,255,0.018) 1px, transparent 1px);
    background-size: 28px 28px;
}

/* Hide Streamlit chrome */
#MainMenu { visibility: hidden !important; }
header[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
footer { visibility: hidden !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0d16 0%, #07090f 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important;
}
section[data-testid="stSidebar"] > div { background: transparent !important; }
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-size: 10px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 1.2px !important;
    color: #475569 !important; margin-top: 24px !important; margin-bottom: 8px !important;
}
section[data-testid="stSidebar"] .stSlider [data-testid="stTickBar"] { display: none; }

/* Sidebar nav item: hover background lift */
.cv-nav-item {
    transition: background 0.15s ease, box-shadow 0.15s ease;
}
.cv-nav-item:hover {
    background: rgba(255,255,255,0.04) !important;
}
/* Active sidebar nav item: left accent glow */
.cv-nav-item-active {
    background: rgba(59,130,246,0.13) !important;
    box-shadow: inset 3px 0 0 #3b82f6 !important;
    border-radius: 8px !important;
}

/* Dividers */
hr { border: none !important; border-top: 1px solid rgba(255,255,255,0.05) !important; margin: 24px 0 !important; }

/* Dataframe tables */
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden !important; }
[data-testid="stDataFrame"] iframe { border-radius: 12px !important; }

/* Headings */
h1 { font-size: 22px !important; font-weight: 800 !important; color: #f8fafc !important; letter-spacing: -0.5px !important; }
h2 { font-size: 17px !important; font-weight: 700 !important; color: #f1f5f9 !important; letter-spacing: -0.3px !important; }
h3 { font-size: 14px !important; font-weight: 600 !important; color: #e2e8f0 !important; }
p  { color: #cbd5e1 !important; font-size: 14px !important; line-height: 1.6 !important; }

/* Caption */
[data-testid="stCaptionContainer"] p { color: #475569 !important; font-size: 12px !important; }

/* Inputs */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: #0d1117 !important; border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 8px !important; color: #f1f5f9 !important; font-size: 13px !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: rgba(59,130,246,0.5) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
}

/* Select */
[data-baseweb="select"] > div {
    background: #0d1117 !important; border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 8px !important;
}
[data-baseweb="select"] span { color: #f1f5f9 !important; font-size: 13px !important; }

/* Slider */
[data-testid="stSlider"] > div > div > div { background: rgba(59,130,246,0.3) !important; }
[data-testid="stSlider"] [role="slider"] { background: #3b82f6 !important; border: 2px solid #1d4ed8 !important; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    color: #fff !important; border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; font-size: 13px !important; padding: 11px 22px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 0 0 1px rgba(59,130,246,0.3) !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.1px !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    box-shadow: 0 0 20px rgba(59,130,246,0.4), 0 4px 16px rgba(59,130,246,0.3) !important;
    transform: translateY(-1px) !important;
}

/* Native alerts */
[data-testid="stAlert"] { border-radius: 10px !important; border-width: 1px !important; border-style: solid !important; }

/* Tabs */
[data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid rgba(255,255,255,0.06) !important; gap: 0 !important; }
[data-baseweb="tab"] {
    background: transparent !important; color: #64748b !important; font-size: 13px !important;
    font-weight: 500 !important; padding: 10px 16px !important; border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    transition: color 0.15s ease, border-color 0.15s ease !important;
    position: relative !important;
}
[data-baseweb="tab"]:hover { color: #94a3b8 !important; border-bottom-color: rgba(59,130,246,0.35) !important; }
[aria-selected="true"][data-baseweb="tab"] { color: #f1f5f9 !important; border-bottom-color: #3b82f6 !important; }
[data-baseweb="tab-highlight"] { display: none !important; }

/* Checkbox */
[data-testid="stCheckbox"] label { color: #cbd5e1 !important; font-size: 13px !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.14); }

/* Metric delta */
[data-testid="stMetricDelta"] { font-size: 12px !important; font-weight: 600 !important; }
[data-testid="stMetric"] { background: #0d1117 !important; border-radius: 10px !important; padding: 12px 16px !important; border: 1px solid rgba(255,255,255,0.06) !important; }
[data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 800 !important; letter-spacing: -0.5px !important; }
[data-testid="stMetricLabel"] { font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.8px !important; color: #475569 !important; }

/* cv-card: hover lift + glow effect — accent color supplied via inline style */
.cv-card {
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease !important;
}
.cv-card:hover {
    transform: translateY(-4px) !important;
}

/* cv-hero-gradient: animated gradient text */
@keyframes hero-gradient-shift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.cv-hero-gradient {
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 40%, #06b6d4 70%, #3b82f6 100%);
    background-size: 200% 200%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: hero-gradient-shift 5s ease infinite;
}

/* Live status dot pulse */
@keyframes pulse-dot {
    0%, 100% { opacity: 1; box-shadow: 0 0 4px #10b981; }
    50%       { opacity: 0.55; box-shadow: 0 0 10px #10b981; }
}
.cv-pulse-dot {
    animation: pulse-dot 2s ease-in-out infinite;
}
</style>
"""


def render_header(title: str, subtitle: str = "", badge: str = None, badge_color: str = "blue"):
    color, bg, border = _COLOR_MAP.get(badge_color, _COLOR_MAP["blue"])
    dot_glow = f"box-shadow:0 0 6px {color};" if badge_color == "green" else ""

    # Single-line strings — multi-line vars with leading whitespace trigger markdown code-block parsing
    badge_part = ""
    if badge:
        badge_part = (
            f'<div style="display:inline-flex;align-items:center;gap:6px;padding:5px 14px;'
            f'border-radius:20px;background:{bg};border:1px solid {border};'
            f'font-size:11px;font-weight:700;color:{color};letter-spacing:0.5px;white-space:nowrap;">'
            f'<span style="width:6px;height:6px;border-radius:50%;background:{color};'
            f'display:inline-block;flex-shrink:0;{dot_glow}"></span>'
            f'{badge}</div>'
        )

    subtitle_part = ""
    if subtitle:
        subtitle_part = (
            f'<div style="font-size:12px;color:#475569;margin-top:4px;line-height:1.5;'
            f'max-width:640px;">{subtitle}</div>'
        )

    st.markdown(
        f'<div style="background:linear-gradient(180deg,#0b0f1e 0%,#080b14 80%,#07090f 100%);'
        f'border-bottom:1px solid rgba(59,130,246,0.18);'
        f'box-shadow:0 1px 24px rgba(59,130,246,0.06);'
        f'padding:16px 28px;margin:-1rem -1rem 28px -1rem;'
        f'display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;">'
        f'<div style="display:flex;align-items:center;gap:14px;min-width:0;">'
        f'<div style="font-size:15px;font-weight:800;letter-spacing:-0.3px;white-space:nowrap;flex-shrink:0;">'
        f'<span style="color:#3b82f6;text-shadow:0 0 16px rgba(59,130,246,0.45);">Care</span>'
        f'<span style="color:#f1f5f9;">Validate</span></div>'
        f'<div style="width:1px;height:24px;background:rgba(255,255,255,0.1);flex-shrink:0;"></div>'
        f'<div style="min-width:0;">'
        f'<div style="font-size:15px;font-weight:700;color:#f1f5f9;letter-spacing:-0.2px;'
        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{title}</div>'
        f'<div style="height:2px;width:32px;background:linear-gradient(90deg,#3b82f6,#8b5cf6);'
        f'border-radius:2px;margin-top:4px;"></div>'
        f'{subtitle_part}</div></div>{badge_part}</div>',
        unsafe_allow_html=True
    )


def kpi_card(value: str, label: str, sublabel: str = "",
             trend: str = None, trend_good: bool = True, color: str = "default") -> str:
    val_color, bg, border = _COLOR_MAP.get(color, _COLOR_MAP["default"])
    if color == "default":
        val_color = "#f8fafc"

    trend_part = ""
    if trend is not None:
        is_up = str(trend).lstrip().startswith(("+", "▲", "↑"))
        good  = (is_up and trend_good) or (not is_up and not trend_good)
        tc    = GREEN if good else RED
        tbg   = "rgba(16,185,129,0.12)" if good else "rgba(239,68,68,0.12)"
        arrow = "↑" if is_up else "↓"
        trend_part = (
            f'<div style="display:inline-flex;align-items:center;gap:3px;margin-top:10px;'
            f'padding:3px 8px;border-radius:10px;font-size:11px;font-weight:600;'
            f'color:{tc};background:{tbg};">{arrow} {trend}</div>'
        )

    sublabel_part = ""
    if sublabel:
        sublabel_part = f'<div style="font-size:12px;color:#64748b;margin-top:5px;line-height:1.5;">{sublabel}</div>'

    return (
        f'<div class="cv-card" style="background:{CARD};border:1px solid rgba(255,255,255,0.07);border-radius:14px;'
        f'padding:22px 24px;height:100%;position:relative;overflow:hidden;'
        f'box-shadow:0 2px 8px rgba(0,0,0,0.4),0 0 0 1px rgba(255,255,255,0.03);'
        f'border-left:3px solid {val_color};">'
        f'<div style="position:absolute;top:0;right:0;width:120px;height:120px;pointer-events:none;'
        f'background:radial-gradient(circle at 100% 0%, {bg} 0%, transparent 70%);border-radius:14px;"></div>'
        f'<div style="position:relative;z-index:1;">'
        f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;'
        f'color:#475569;margin-bottom:10px;">{label}</div>'
        f'<div style="font-size:32px;font-weight:800;letter-spacing:-1px;color:{val_color};'
        f'line-height:1.1;">{value}</div>'
        f'{sublabel_part}{trend_part}</div></div>'
    )


def kpi_row(cards: list, gap: str = "12px"):
    cols = st.columns(len(cards))
    for col, html in zip(cols, cards):
        col.markdown(html, unsafe_allow_html=True)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)


def section(title: str, icon: str = ""):
    icon_part = f'<span style="font-size:16px;line-height:1;flex-shrink:0;">{icon}</span>' if icon else ""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;margin:32px 0 16px 0;'
        f'padding-bottom:12px;border-bottom:1px solid rgba(255,255,255,0.07);">'
        f'{icon_part}'
        f'<span style="font-size:14px;font-weight:700;color:#f1f5f9;letter-spacing:-0.2px;'
        f'white-space:nowrap;">{title}</span>'
        f'<div style="flex:1;height:1px;background:rgba(255,255,255,0.04);margin-left:8px;"></div>'
        f'</div>',
        unsafe_allow_html=True
    )


def alert(message: str, level: str = "info"):
    cfg = {
        "info":    ("#3b82f6", "rgba(59,130,246,0.08)",  "rgba(59,130,246,0.2)",  "ℹ"),
        "warning": ("#f59e0b", "rgba(245,158,11,0.08)",  "rgba(245,158,11,0.2)",  "⚠"),
        "error":   ("#ef4444", "rgba(239,68,68,0.08)",   "rgba(239,68,68,0.2)",   "✕"),
        "success": ("#10b981", "rgba(16,185,129,0.08)",  "rgba(16,185,129,0.2)",  "✓"),
    }
    color, bg, border, icon = cfg.get(level, cfg["info"])
    st.markdown(
        f'<div style="background:{bg};border:1px solid {border};border-radius:10px;'
        f'padding:14px 18px;font-size:13px;line-height:1.65;margin:12px 0 20px 0;'
        f'color:{TEXT};display:flex;gap:10px;align-items:flex-start;">'
        f'<span style="font-size:15px;flex-shrink:0;margin-top:1px;color:{color};">{icon}</span>'
        f'<span>{message}</span></div>',
        unsafe_allow_html=True
    )


def stat_table_row(label: str, value: str, status: str = "", muted: bool = False):
    val_color = "#f1f5f9" if not muted else "#64748b"
    status_part = f'<span style="font-size:13px;">{status}</span>' if status else ""
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:10px 16px;border-bottom:1px solid rgba(255,255,255,0.04);">'
        f'<span style="font-size:13px;color:#94a3b8;">{label}</span>'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'<span style="font-size:13px;font-weight:600;color:{val_color};">{value}</span>'
        f'{status_part}</div></div>',
        unsafe_allow_html=True
    )


_NAV_TOOLS = [
    {"key": "cmd",    "icon": "⌂",  "name": "Command Center",  "slug": "Command_Center",    "page": "pages/01_Command_Center.py"},
    {"key": "glp1",   "icon": "💊", "name": "GLP-1 Scenarios", "slug": "GLP1_Scenarios",    "page": "pages/02_GLP1_Scenarios.py"},
    {"key": "units",  "icon": "📊", "name": "Unit Economics",  "slug": "Unit_Economics",    "page": "pages/03_Unit_Economics.py"},
    {"key": "roi",    "icon": "🏢", "name": "Employer ROI",    "slug": "Employer_ROI",      "page": "pages/04_Employer_ROI.py"},
    {"key": "churn",  "icon": "🔮", "name": "Churn Engine",    "slug": "Churn_Engine",      "page": "pages/05_Churn_Engine.py"},
    {"key": "series", "icon": "📈", "name": "Series A",        "slug": "Series_A",          "page": "pages/06_Series_A.py"},
    {"key": "comply", "icon": "🔍", "name": "Compliance",      "slug": "Compliance_Monitor","page": "pages/07_Compliance_Monitor.py"},
    {"key": "retain", "icon": "🔄", "name": "Retention Ops",   "slug": "Retention_Ops",     "page": "pages/08_Retention_Ops.py"},
    {"key": "cfo",    "icon": "⚙",  "name": "CFO Suite",       "slug": "CFO_Suite",         "page": "pages/09_CFO_Suite.py"},
    {"key": "nav",    "icon": "🧭", "name": "Navigator Ops",   "slug": "Navigator_Ops",     "page": "pages/10_Navigator_Ops.py"},
    {"key": "sec",    "icon": "🔒", "name": "Security Center", "slug": "Security_Center",   "page": "pages/11_Security_Center.py"},
    {"key": "recon",  "icon": "⚖",  "name": "Reconciliation",  "slug": "Reconciliation",    "page": "pages/12_Reconciliation.py"},
]


def sidebar_nav(current: str = ""):
    with st.sidebar:
        st.markdown(
            '<div style="padding:20px 4px 18px 4px;border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:16px;">'
            '<div style="font-size:18px;font-weight:800;letter-spacing:-0.3px;">'
            '<span style="color:#3b82f6;text-shadow:0 0 18px rgba(59,130,246,0.5);">Care</span>'
            '<span style="color:#f1f5f9;">Validate</span></div>'
            '<div style="font-size:10px;color:#334155;margin-top:3px;font-weight:700;letter-spacing:1px;">FINANCE SUITE</div>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div style="font-size:10px;font-weight:700;color:#334155;'
            'letter-spacing:1.2px;text-transform:uppercase;margin-bottom:8px;">Navigation</div>',
            unsafe_allow_html=True
        )
        for t in _NAV_TOOLS:
            active = t["key"] == current
            item_class = "cv-nav-item cv-nav-item-active" if active else "cv-nav-item"
            fc = "#e2e8f0" if active else "#64748b"
            fw = "600" if active else "400"
            dot = ('<span style="margin-left:auto;width:5px;height:5px;border-radius:50%;'
                   'background:#3b82f6;box-shadow:0 0 6px #3b82f6;display:inline-block;flex-shrink:0;"></span>') if active else ""
            st.markdown(
                f'<a href="/{t["slug"]}" style="text-decoration:none;">'
                f'<div class="{item_class}" style="display:flex;align-items:center;gap:9px;padding:8px 10px;border-radius:8px;'
                f'margin-bottom:2px;cursor:pointer;">'
                f'<span style="font-size:14px;line-height:1;flex-shrink:0;">{t["icon"]}</span>'
                f'<span style="font-size:13px;font-weight:{fw};color:{fc};flex:1;">{t["name"]}</span>'
                f'{dot}</div></a>',
                unsafe_allow_html=True
            )
        st.markdown(
            '<div style="margin-top:24px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.06);">'
            '<div style="font-size:10px;font-weight:700;color:#334155;letter-spacing:1.2px;'
            'text-transform:uppercase;margin-bottom:10px;">Compliance Standards</div>'
            '<div style="display:flex;flex-direction:column;gap:5px;">'
            '<div style="display:flex;align-items:center;gap:7px;padding:5px 8px;'
            'background:rgba(16,185,129,0.07);border:1px solid rgba(16,185,129,0.18);border-radius:7px;">'
            '<span style="width:5px;height:5px;border-radius:50%;background:#10b981;flex-shrink:0;display:inline-block;"></span>'
            '<span style="font-size:10px;font-weight:600;color:#10b981;">Synthetic Data Only</span>'
            '<span style="font-size:9px;color:#334155;margin-left:auto;">No PHI</span></div>'
            '<div style="display:flex;align-items:center;gap:7px;padding:5px 8px;'
            'background:rgba(59,130,246,0.07);border:1px solid rgba(59,130,246,0.18);border-radius:7px;">'
            '<span style="width:5px;height:5px;border-radius:50%;background:#3b82f6;flex-shrink:0;display:inline-block;"></span>'
            '<span style="font-size:10px;font-weight:600;color:#3b82f6;">HITRUST CSF Aligned</span>'
            '<span style="font-size:9px;color:#334155;margin-left:auto;">r2</span></div>'
            '<div style="display:flex;align-items:center;gap:7px;padding:5px 8px;'
            'background:rgba(139,92,246,0.07);border:1px solid rgba(139,92,246,0.18);border-radius:7px;">'
            '<span style="width:5px;height:5px;border-radius:50%;background:#8b5cf6;flex-shrink:0;display:inline-block;"></span>'
            '<span style="font-size:10px;font-weight:600;color:#8b5cf6;">HEDIS/NCQA Referenced</span>'
            '<span style="font-size:9px;color:#334155;margin-left:auto;">2026</span></div>'
            '<div style="display:flex;align-items:center;gap:7px;padding:5px 8px;'
            'background:rgba(6,182,212,0.07);border:1px solid rgba(6,182,212,0.18);border-radius:7px;">'
            '<span style="width:5px;height:5px;border-radius:50%;background:#06b6d4;flex-shrink:0;display:inline-block;"></span>'
            '<span style="font-size:10px;font-weight:600;color:#06b6d4;">HL7 FHIR R4 Ready</span>'
            '<span style="font-size:9px;color:#334155;margin-left:auto;">ONC</span></div>'
            '</div>'
            '<div style="margin-top:10px;padding:8px 10px;background:rgba(255,255,255,0.03);'
            'border-radius:7px;font-size:10px;color:#334155;line-height:1.7;">'
            '<strong style="color:#475569;">No PHI processed</strong> · Synthetic data only<br>'
            'BAA required before production deployment</div>'
            '</div>',
            unsafe_allow_html=True
        )


def card_container(content_fn, title: str = "", padding: str = "20px 24px"):
    if title:
        st.markdown(
            f'<div style="background:{CARD};border:1px solid rgba(255,255,255,0.07);'
            f'border-radius:14px;padding:0;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.4);">'
            f'<div style="padding:14px 20px;border-bottom:1px solid rgba(255,255,255,0.06);'
            f'font-size:13px;font-weight:700;color:#f1f5f9;">{title}</div>'
            f'<div style="padding:{padding};">',
            unsafe_allow_html=True
        )
    content_fn()
    if title:
        st.markdown("</div></div>", unsafe_allow_html=True)
