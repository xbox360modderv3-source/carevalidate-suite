"""
CareValidate Finance Suite Hub
Landing page — links to all 6 finance dashboards.
Run: streamlit run app.py --server.port 8500
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

import streamlit as st
from carevalidate_shared.theme import GLOBAL_CSS, BG, CARD, BLUE, GREEN, YELLOW, RED, PURPLE, MUTED
from carevalidate_shared.auth import check_auth, logout_button

st.set_page_config(
    page_title="CareValidate Finance Suite",
    layout="wide",
    page_icon="⬡",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
check_auth()
logout_button()

# ── Tool definitions ─────────────────────────────────────────────────────────
TOOLS = [
    {
        "icon": "⌂",
        "name": "Command Center",
        "tag": "CFO Morning View",
        "desc": "All critical KPIs in one dashboard — MRR, churn, compliance risk, and revenue scenarios aggregated for the CFO.",
        "slug": "Command_Center",
        "accent": "#3b82f6",
        "tag_bg": "rgba(59,130,246,0.10)",
        "tag_border": "rgba(59,130,246,0.30)",
    },
    {
        "icon": "💊",
        "name": "GLP-1 Scenario Model",
        "tag": "Revenue Modeling",
        "desc": "Four-scenario revenue impact of the FDA compounded semaglutide ban — branded vs alt-peptide pivot vs generic entry.",
        "slug": "GLP1_Scenarios",
        "accent": "#10b981",
        "tag_bg": "rgba(16,185,129,0.10)",
        "tag_border": "rgba(16,185,129,0.25)",
    },
    {
        "icon": "📊",
        "name": "Unit Economics",
        "tag": "Growth Analytics",
        "desc": "CAC, LTV, payback, cohort retention, and PMPM metrics across CareGLP, CareHRT, CareDERM, and AccommoCare.",
        "slug": "Unit_Economics",
        "accent": "#3b82f6",
        "tag_bg": "rgba(59,130,246,0.10)",
        "tag_border": "rgba(59,130,246,0.25)",
    },
    {
        "icon": "🏢",
        "name": "Employer ROI Calculator",
        "tag": "Sales Enablement",
        "desc": "B2B sales tool quantifying the financial case for CareValidate programs — claims savings, productivity, T2D prevention.",
        "slug": "Employer_ROI",
        "accent": "#8b5cf6",
        "tag_bg": "rgba(139,92,246,0.10)",
        "tag_border": "rgba(139,92,246,0.25)",
    },
    {
        "icon": "🔮",
        "name": "Predictive Churn Engine",
        "tag": "Retention ML",
        "desc": "ML-based patient churn risk scoring — flags at-risk patients 30–45 days early and ranks intervention by revenue at risk.",
        "slug": "Churn_Engine",
        "accent": "#f59e0b",
        "tag_bg": "rgba(245,158,11,0.10)",
        "tag_border": "rgba(245,158,11,0.25)",
    },
    {
        "icon": "📈",
        "name": "Series A Data Room",
        "tag": "Investor Ready",
        "desc": "Investor-ready metrics package with benchmark comparison, MRR trajectory, use-of-proceeds, and Series A checklist.",
        "slug": "Series_A",
        "accent": "#10b981",
        "tag_bg": "rgba(16,185,129,0.10)",
        "tag_border": "rgba(16,185,129,0.25)",
    },
    {
        "icon": "🔄",
        "name": "Retention Operations",
        "tag": "Patient Retention",
        "desc": "Refill gap early-warning, cohort survival curves, engagement scoring, and auto-generated employer renewal reports.",
        "slug": "Retention_Ops",
        "accent": "#06b6d4",
        "tag_bg": "rgba(6,182,212,0.10)",
        "tag_border": "rgba(6,182,212,0.25)",
    },
    {
        "icon": "🔍",
        "name": "Contract Compliance Monitor",
        "tag": "Compliance",
        "desc": "Detects billing deviations, HEDIS Stars impact, and CMS bonus modeling. Flags TRC gap closure below 68% floor.",
        "slug": "Compliance_Monitor",
        "accent": "#ef4444",
        "tag_bg": "rgba(239,68,68,0.10)",
        "tag_border": "rgba(239,68,68,0.25)",
    },
    {
        "icon": "⚙",
        "name": "CFO Automation Suite",
        "tag": "CFO Tooling",
        "desc": "Monthly pack generator, 13-week cash flow forecast, MLR spend qualification model, and real-time alert engine.",
        "slug": "CFO_Suite",
        "accent": "#f59e0b",
        "tag_bg": "rgba(245,158,11,0.10)",
        "tag_border": "rgba(245,158,11,0.25)",
    },
    {
        "icon": "🧭",
        "name": "Navigator Workforce Intelligence",
        "tag": "Care Operations",
        "desc": "FTE productivity, capacity planning, per-FTE ROI, language coverage, and automated weekly ops brief for navigator teams.",
        "slug": "Navigator_Ops",
        "accent": "#06b6d4",
        "tag_bg": "rgba(6,182,212,0.10)",
        "tag_border": "rgba(6,182,212,0.25)",
    },
    {
        "icon": "🔒",
        "name": "HIPAA Security Center",
        "tag": "Compliance & Security",
        "desc": "RBAC access matrix, immutable audit trail, BAA vendor tracker, breach cost model, and HITRUST control status — production-ready compliance posture.",
        "slug": "Security_Center",
        "accent": "#ef4444",
        "tag_bg": "rgba(239,68,68,0.10)",
        "tag_border": "rgba(239,68,68,0.25)",
    },
    {
        "icon": "⚖",
        "name": "Payment Reconciliation Engine",
        "tag": "Finance Automation",
        "desc": "Auto-matches transactions, flags discrepancies, detects duplicates, predicts failed settlements, and generates a prioritized exception queue.",
        "slug": "Reconciliation",
        "accent": "#3b82f6",
        "tag_bg": "rgba(59,130,246,0.10)",
        "tag_border": "rgba(59,130,246,0.25)",
    },
]

# ── Navigation bar ───────────────────────────────────────────────────────────
st.markdown(
    '<div style="background:linear-gradient(180deg,#0b0f1e 0%,#080b14 100%);'
    'border-bottom:1px solid rgba(255,255,255,0.07);'
    'padding:14px 28px;margin:-1rem -1rem 0 -1rem;'
    'display:flex;align-items:center;justify-content:space-between;">'
    '<div style="font-size:15px;font-weight:800;color:#3b82f6;letter-spacing:-0.3px;">'
    'Care<span style="color:#f1f5f9;">Validate</span></div>'
    '<div style="display:flex;align-items:center;gap:8px;">'
    '<span style="display:inline-flex;align-items:center;gap:5px;background:rgba(16,185,129,0.10);'
    'border:1px solid rgba(16,185,129,0.25);color:#10b981;font-size:10px;font-weight:700;'
    'padding:3px 10px;border-radius:20px;letter-spacing:0.5px;">'
    '<span style="width:5px;height:5px;border-radius:50%;background:#10b981;'
    'display:inline-block;box-shadow:0 0 6px #10b981;"></span>ALL SYSTEMS LIVE</span>'
    '<span style="font-size:11px;color:#334155;font-family:monospace;'
    'background:#0d1117;padding:3px 8px;border-radius:6px;border:1px solid rgba(255,255,255,0.06);">'
    'Synthetic Data Only</span>'
    '</div></div>',
    unsafe_allow_html=True
)

# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;padding:56px 24px 48px 24px;">'
    '<div style="display:inline-flex;align-items:center;gap:6px;'
    'background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.18);'
    'color:#3b82f6;font-size:11px;font-weight:700;padding:4px 14px;border-radius:20px;'
    'letter-spacing:0.8px;text-transform:uppercase;margin-bottom:20px;">'
    'Finance Suite · 12 Dashboards</div>'
    '<div style="font-size:48px;font-weight:800;letter-spacing:-2px;color:#f8fafc;'
    'line-height:1;margin-bottom:16px;">'
    'Financial Intelligence<br>'
    '<span style="background:linear-gradient(135deg,#3b82f6 0%,#8b5cf6 100%);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
    'background-clip:text;">for Digital Health</span></div>'
    '<div style="font-size:16px;color:#64748b;max-width:600px;margin:0 auto;line-height:1.65;">'
    'CFO-grade modeling for GLP-1 revenue scenarios, care navigation ROI, payer PMPM compliance, '
    'member retention, unit economics, and Series A readiness — '
    'calibrated to HEDIS, IQVIA, and CMS Medicare Advantage benchmarks.</div>'
    '</div>',
    unsafe_allow_html=True
)

# ── Stats strip ───────────────────────────────────────────────────────────────
stats = [
    ("12", "Live Dashboards"),
    ("850+", "Synthetic Patients"),
    ("1M", "HealthJoy Lives Modeled"),
    ("Real Benchmarks", "KFF · ADA · NEJM · Omada S-1"),
]
cols = st.columns(4)
for col, (val, lbl) in zip(cols, stats):
    with col:
        st.markdown(
            f'<div style="text-align:center;padding:16px 12px;background:{CARD};'
            f'border:1px solid rgba(255,255,255,0.06);border-radius:12px;">'
            f'<div style="font-size:22px;font-weight:800;color:#f8fafc;letter-spacing:-0.5px;">{val}</div>'
            f'<div style="font-size:11px;color:#475569;margin-top:4px;font-weight:500;">{lbl}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# ── Section label ─────────────────────────────────────────────────────────────
st.markdown(
    '<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">'
    '<div style="height:1px;flex:1;background:rgba(255,255,255,0.05);"></div>'
    '<span style="font-size:11px;font-weight:700;text-transform:uppercase;'
    'letter-spacing:1.2px;color:#334155;">Select a dashboard</span>'
    '<div style="height:1px;flex:1;background:rgba(255,255,255,0.05);"></div>'
    '</div>',
    unsafe_allow_html=True
)

# ── 3×2 card grid ────────────────────────────────────────────────────────────
for row_start in range(0, len(TOOLS), 3):
    row_tools = TOOLS[row_start:row_start + 3]
    cols = st.columns(3, gap="medium")
    for col, t in zip(cols, row_tools):
        url = f"/{t['slug']}"
        with col:
            st.markdown(
                f'<a href="{url}" style="text-decoration:none;display:block;">'
                f'<div style="background:{CARD};border:1px solid rgba(255,255,255,0.07);'
                f'border-radius:14px;border-top:3px solid {t["accent"]};padding:22px 22px 20px 22px;'
                f'box-shadow:0 1px 3px rgba(0,0,0,0.5),0 0 0 1px rgba(255,255,255,0.02);">'
                f'<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:14px;">'
                f'<span style="font-size:28px;line-height:1;">{t["icon"]}</span>'
                f'<span style="display:inline-flex;align-items:center;gap:5px;'
                f'background:{t["tag_bg"]};border:1px solid {t["tag_border"]};'
                f'color:{t["accent"]};font-size:10px;font-weight:700;'
                f'padding:3px 9px;border-radius:20px;white-space:nowrap;letter-spacing:0.3px;">'
                f'<span style="width:4px;height:4px;border-radius:50%;background:{t["accent"]};'
                f'display:inline-block;"></span>{t["tag"]}</span>'
                f'</div>'
                f'<div style="font-size:15px;font-weight:700;color:#f1f5f9;'
                f'letter-spacing:-0.2px;margin-bottom:8px;">{t["name"]}</div>'
                f'<div style="font-size:13px;color:#64748b;line-height:1.6;margin-bottom:20px;'
                f'min-height:52px;">{t["desc"]}</div>'
                f'<div style="display:flex;align-items:center;padding-top:12px;'
                f'border-top:1px solid rgba(255,255,255,0.05);">'
                f'<span style="font-size:12px;font-weight:600;color:{t["accent"]};">Open dashboard →</span>'
                f'</div></div></a>',
                unsafe_allow_html=True
            )
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Data sources ──────────────────────────────────────────────────────────────
st.markdown(
    '<div style="display:flex;align-items:center;gap:12px;margin:8px 0 16px 0;">'
    '<div style="height:1px;flex:1;background:rgba(255,255,255,0.05);"></div>'
    '<span style="font-size:11px;font-weight:700;text-transform:uppercase;'
    'letter-spacing:1.2px;color:#334155;">Data Sources</span>'
    '<div style="height:1px;flex:1;background:rgba(255,255,255,0.05);"></div>'
    '</div>',
    unsafe_allow_html=True
)

sources = [
    ("KFF EHBS 2024", "Employer benchmarks"),
    ("NCQA HEDIS 2026", "Care gap measures"),
    ("NEJM STEP/SELECT", "GLP-1 outcomes"),
    ("Omada S-1 2024", "Digital health UE"),
    ("CMS MA 2026", "Medicare Advantage"),
    ("OIG Work Plan 2025", "Billing guidance"),
]
cols = st.columns(6, gap="small")
for col, (src, desc) in zip(cols, sources):
    with col:
        st.markdown(
            f'<div style="text-align:center;padding:11px 8px;background:{CARD};'
            f'border:1px solid rgba(255,255,255,0.06);border-radius:10px;">'
            f'<div style="font-size:11px;font-weight:700;color:#94a3b8;margin-bottom:3px;">{src}</div>'
            f'<div style="font-size:10px;color:#475569;">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

# ── Compliance standards strip ───────────────────────────────────────────────
st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
standards = [
    ("#10b981", "HIPAA Safe Harbor", "§164.514(b) de-identified"),
    ("#3b82f6", "HITRUST CSF r2",    "19 control domains"),
    ("#8b5cf6", "HEDIS/NCQA 2026",   "Care gap measures"),
    ("#06b6d4", "HL7 FHIR R4",       "ONC interoperability"),
    ("#f59e0b", "CMS MA Stars",      "Medicare Advantage quality"),
    ("#94a3b8", "No PHI Processed",  "Synthetic data only"),
]
cols = st.columns(6, gap="small")
for col, (color, title, sub) in zip(cols, standards):
    with col:
        st.markdown(
            f'<div style="text-align:center;padding:11px 8px;'
            f'background:rgba(255,255,255,0.02);border:1px solid {color}22;'
            f'border-top:2px solid {color};border-radius:10px;">'
            f'<div style="font-size:10px;font-weight:700;color:{color};margin-bottom:3px;">{title}</div>'
            f'<div style="font-size:9px;color:#334155;">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;padding:32px 0 24px 0;color:#334155;font-size:12px;line-height:2;">'
    'Built by <span style="color:#94a3b8;font-weight:600;">Connor Savenas</span>'
    ' · Finance &amp; Economics, University of Alabama · May 2026<br>'
    '<a href="https://www.linkedin.com/in/connorsavenas/" target="_blank" '
    'style="color:#3b82f6;text-decoration:none;">linkedin.com/in/connorsavenas</a>'
    ' · crsavenas@crimson.ua.edu'
    ' · <span style="color:#1e293b;">No PHI · Synthetic data only</span>'
    '</div>',
    unsafe_allow_html=True
)
