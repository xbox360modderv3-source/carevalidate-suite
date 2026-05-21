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
        "icon": "⌂",  "name": "Command Center",
        "tag": "CFO Morning View",
        "desc": "All critical KPIs in one dashboard — MRR, churn, compliance risk, and revenue scenarios aggregated for the CFO.",
        "page": "pages/01_Command_Center.py",
        "accent": "#3b82f6", "tag_bg": "rgba(59,130,246,0.10)", "tag_border": "rgba(59,130,246,0.30)",
    },
    {
        "icon": "💊", "name": "GLP-1 Scenario Model",
        "tag": "Revenue Modeling",
        "desc": "Four-scenario revenue impact of the FDA compounded semaglutide ban — branded vs alt-peptide pivot vs generic entry.",
        "page": "pages/02_GLP1_Scenarios.py",
        "accent": "#10b981", "tag_bg": "rgba(16,185,129,0.10)", "tag_border": "rgba(16,185,129,0.25)",
    },
    {
        "icon": "📊", "name": "Unit Economics",
        "tag": "Growth Analytics",
        "desc": "CAC, LTV, payback, cohort retention, and PMPM metrics across CareGLP, CareHRT, CareDERM, and AccommoCare.",
        "page": "pages/03_Unit_Economics.py",
        "accent": "#3b82f6", "tag_bg": "rgba(59,130,246,0.10)", "tag_border": "rgba(59,130,246,0.25)",
    },
    {
        "icon": "🏢", "name": "Employer ROI Calculator",
        "tag": "Sales Enablement",
        "desc": "B2B sales tool quantifying the financial case for CareValidate programs — claims savings, productivity, T2D prevention.",
        "page": "pages/04_Employer_ROI.py",
        "accent": "#8b5cf6", "tag_bg": "rgba(139,92,246,0.10)", "tag_border": "rgba(139,92,246,0.25)",
    },
    {
        "icon": "🔮", "name": "Predictive Churn Engine",
        "tag": "Retention ML",
        "desc": "ML-based patient churn risk scoring — flags at-risk patients 30–45 days early and ranks intervention by revenue at risk.",
        "page": "pages/05_Churn_Engine.py",
        "accent": "#f59e0b", "tag_bg": "rgba(245,158,11,0.10)", "tag_border": "rgba(245,158,11,0.25)",
    },
    {
        "icon": "📈", "name": "Series A Data Room",
        "tag": "Investor Ready",
        "desc": "Investor-ready metrics package with benchmark comparison, MRR trajectory, use-of-proceeds, and Series A checklist.",
        "page": "pages/06_Series_A.py",
        "accent": "#10b981", "tag_bg": "rgba(16,185,129,0.10)", "tag_border": "rgba(16,185,129,0.25)",
    },
    {
        "icon": "🔄", "name": "Retention Operations",
        "tag": "Patient Retention",
        "desc": "Refill gap early-warning, cohort survival curves, engagement scoring, and auto-generated employer renewal reports.",
        "page": "pages/08_Retention_Ops.py",
        "accent": "#06b6d4", "tag_bg": "rgba(6,182,212,0.10)", "tag_border": "rgba(6,182,212,0.25)",
    },
    {
        "icon": "🔍", "name": "Contract Compliance Monitor",
        "tag": "Compliance",
        "desc": "Detects billing deviations, HEDIS Stars impact, and CMS bonus modeling. Flags TRC gap closure below 68% floor.",
        "page": "pages/07_Compliance_Monitor.py",
        "accent": "#ef4444", "tag_bg": "rgba(239,68,68,0.10)", "tag_border": "rgba(239,68,68,0.25)",
    },
    {
        "icon": "⚙",  "name": "CFO Automation Suite",
        "tag": "CFO Tooling",
        "desc": "Monthly pack generator, 13-week cash flow forecast, MLR finance impact scenario model, and real-time alert engine.",
        "page": "pages/09_CFO_Suite.py",
        "accent": "#f59e0b", "tag_bg": "rgba(245,158,11,0.10)", "tag_border": "rgba(245,158,11,0.25)",
    },
    {
        "icon": "🧭", "name": "Navigator Workforce Intelligence",
        "tag": "Care Operations",
        "desc": "FTE productivity, capacity planning, per-FTE ROI, language coverage, and automated weekly ops brief for navigator teams.",
        "page": "pages/10_Navigator_Ops.py",
        "accent": "#06b6d4", "tag_bg": "rgba(6,182,212,0.10)", "tag_border": "rgba(6,182,212,0.25)",
    },
    {
        "icon": "🔒", "name": "Security & Compliance Readiness Center",
        "tag": "Compliance & Security",
        "desc": "RBAC access matrix, audit trail, BAA vendor tracker, breach cost model, and HITRUST control reference — illustrative prototype.",
        "page": "pages/11_Security_Center.py",
        "accent": "#ef4444", "tag_bg": "rgba(239,68,68,0.10)", "tag_border": "rgba(239,68,68,0.25)",
    },
    {
        "icon": "⚖",  "name": "Payment Reconciliation Engine",
        "tag": "Finance Automation",
        "desc": "Auto-matches transactions, flags discrepancies, detects duplicates, predicts failed settlements, and generates a prioritized exception queue.",
        "page": "pages/12_Reconciliation.py",
        "accent": "#3b82f6", "tag_bg": "rgba(59,130,246,0.10)", "tag_border": "rgba(59,130,246,0.25)",
    },
    {
        "icon": "💳", "name": "Payer Revenue Cycle",
        "tag": "Revenue Integrity",
        "desc": "Claims management, denial analytics, first-pass rates, DSO by payer, A/R aging buckets, and net collection rate scorecard.",
        "page": "pages/13_Payer_Revenue_Cycle.py",
        "accent": "#8b5cf6", "tag_bg": "rgba(139,92,246,0.10)", "tag_border": "rgba(139,92,246,0.25)",
    },
]

# ── Navigation bar ───────────────────────────────────────────────────────────
st.markdown(
    '<div style="background:linear-gradient(180deg,#0b0f1e 0%,#080b14 80%,#07090f 100%);'
    'border-bottom:1px solid rgba(59,130,246,0.18);'
    'box-shadow:0 1px 24px rgba(59,130,246,0.06);'
    'padding:14px 28px;margin:-1rem -1rem 0 -1rem;'
    'display:flex;align-items:center;justify-content:space-between;">'
    '<div style="font-size:16px;font-weight:800;letter-spacing:-0.3px;">'
    '<span style="color:#3b82f6;text-shadow:0 0 18px rgba(59,130,246,0.5);">Care</span>'
    '<span style="color:#f1f5f9;">Validate</span></div>'
    '<div style="display:flex;align-items:center;gap:8px;">'
    '<span style="display:inline-flex;align-items:center;gap:6px;background:rgba(16,185,129,0.10);'
    'border:1px solid rgba(16,185,129,0.25);color:#10b981;font-size:10px;font-weight:700;'
    'padding:4px 12px;border-radius:20px;letter-spacing:0.5px;">'
    '<span class="cv-pulse-dot" style="width:5px;height:5px;border-radius:50%;background:#10b981;'
    'display:inline-block;"></span>ALL SYSTEMS LIVE</span>'
    '<span style="font-size:11px;color:#334155;font-family:monospace;'
    'background:#0d1117;padding:3px 8px;border-radius:6px;border:1px solid rgba(255,255,255,0.06);">'
    'Synthetic Data Only</span>'
    '</div></div>',
    unsafe_allow_html=True
)

# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="position:relative;text-align:center;padding:64px 24px 52px 24px;overflow:hidden;">'
    '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-55%);'
    'width:600px;height:320px;pointer-events:none;z-index:0;'
    'background:radial-gradient(ellipse at center,rgba(59,130,246,0.09) 0%,rgba(139,92,246,0.05) 40%,transparent 70%);'
    'filter:blur(2px);"></div>'
    '<div style="position:relative;z-index:1;">'
    '<div style="display:inline-flex;align-items:center;gap:6px;'
    'background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.22);'
    'color:#3b82f6;font-size:11px;font-weight:700;padding:5px 16px;border-radius:20px;'
    'letter-spacing:0.8px;text-transform:uppercase;margin-bottom:24px;">'
    'Finance Suite · 12 Dashboards</div>'
    '<div style="font-size:52px;font-weight:800;letter-spacing:-2.5px;color:#f8fafc;'
    'line-height:1.05;margin-bottom:18px;">'
    'Financial Intelligence<br>'
    '<span class="cv-hero-gradient">for Digital Health</span></div>'
    '<div style="font-size:17px;color:#64748b;max-width:620px;margin:0 auto;line-height:1.7;font-weight:400;">'
    'CFO-grade modeling for GLP-1 revenue scenarios, care navigation ROI, payer PMPM compliance, '
    'member retention, unit economics, and Series A readiness — '
    'calibrated to HEDIS, IQVIA, and CMS Medicare Advantage benchmarks.</div>'
    '</div></div>',
    unsafe_allow_html=True
)

# ── Stats strip ───────────────────────────────────────────────────────────────
stats = [
    ("12", "Live Dashboards", BLUE, "rgba(59,130,246,0.3)"),
    ("850+", "Synthetic Patients", GREEN, "rgba(16,185,129,0.3)"),
    ("1M", "HealthJoy Lives Modeled", PURPLE, "rgba(139,92,246,0.3)"),
    ("Real Benchmarks", "KFF · ADA · NEJM · Omada S-1", YELLOW, "rgba(245,158,11,0.3)"),
]
cols = st.columns(4)
for col, (val, lbl, accent, glow) in zip(cols, stats):
    with col:
        st.markdown(
            f'<div style="text-align:center;padding:18px 12px;background:{CARD};'
            f'border:1px solid rgba(255,255,255,0.06);border-radius:12px;'
            f'border-left:3px solid {accent};">'
            f'<div style="font-size:22px;font-weight:800;color:#f8fafc;letter-spacing:-0.5px;'
            f'text-shadow:0 0 20px {glow};">{val}</div>'
            f'<div style="font-size:11px;color:#475569;margin-top:5px;font-weight:500;">{lbl}</div>'
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

# ── 3-column card grid ────────────────────────────────────────────────────────
for row_start in range(0, len(TOOLS), 3):
    row_tools = TOOLS[row_start:row_start + 3]
    cols = st.columns(3, gap="medium")
    for col, t in zip(cols, row_tools):
        with col:
            # Visual card — no <a> wrapper; st.page_link() below handles navigation
            # so session state (auth) is preserved across pages
            st.markdown(
                f'<div class="cv-card" style="background:{CARD};border:1px solid rgba(255,255,255,0.07);'
                f'border-radius:14px 14px 0 0;border-top:3px solid {t["accent"]};'
                f'padding:22px 22px 16px 22px;'
                f'box-shadow:0 1px 3px rgba(0,0,0,0.5),0 0 0 1px {t["tag_bg"]};">'
                f'<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:14px;">'
                f'<span style="font-size:32px;line-height:1;">{t["icon"]}</span>'
                f'<span style="display:inline-flex;align-items:center;gap:5px;'
                f'background:{t["tag_bg"]};border:1px solid {t["tag_border"]};'
                f'color:{t["accent"]};font-size:10px;font-weight:700;'
                f'padding:3px 9px;border-radius:20px;white-space:nowrap;letter-spacing:0.3px;">'
                f'<span style="width:4px;height:4px;border-radius:50%;background:{t["accent"]};'
                f'display:inline-block;"></span>{t["tag"]}</span>'
                f'</div>'
                f'<div style="font-size:15px;font-weight:700;color:#f1f5f9;'
                f'letter-spacing:-0.2px;margin-bottom:8px;">{t["name"]}</div>'
                f'<div style="font-size:13px;color:#64748b;line-height:1.6;min-height:52px;">'
                f'{t["desc"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            # st.page_link preserves Streamlit session — no re-login on navigation
            st.page_link(t["page"], label="Open dashboard →", use_container_width=True)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

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
    ("#10b981", "Synthetic Data Only", "No PHI processed"),
    ("#3b82f6", "HITRUST CSF Ref",    "19 control domains"),
    ("#8b5cf6", "HEDIS/NCQA 2026",   "Care gap measures"),
    ("#06b6d4", "HL7 FHIR R4",       "ONC interoperability"),
    ("#f59e0b", "CMS MA Stars",      "Medicare Advantage quality"),
    ("#94a3b8", "Prototype",         "Not for production use"),
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
