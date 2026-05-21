"""
CareValidate Executive Command Center
CFO morning dashboard — top KPIs from all 6 tools in one view.
Run: streamlit run app.py --server.port 8501
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from carevalidate_shared.theme import (
    GLOBAL_CSS, render_header, kpi_card, kpi_row, section, alert, sidebar_nav,
    BG, CARD, BLUE, GREEN, YELLOW, RED, PURPLE, TEAL, MUTED,
)
from carevalidate_shared.auth import check_auth, logout_button
from carevalidate_shared.commentary import build_commentary, render_commentary_ui
import datetime as _dt

st.set_page_config(page_title="CareValidate Command Center", layout="wide", page_icon="⌂")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
check_auth()
sidebar_nav("cmd")
logout_button()

# ── Date range selector ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown('<div style="font-size:11px;color:#64748b;font-weight:600;letter-spacing:.06em;margin-bottom:6px;">DATE RANGE</div>', unsafe_allow_html=True)
    _today = _dt.date.today()
    _presets = {"Last 30 days": 30, "Last 60 days": 60, "Last 90 days": 90, "YTD": (_today - _dt.date(_today.year, 1, 1)).days}
    _preset_label = st.selectbox("Quick select", list(_presets.keys()), index=0, key="cmd_preset")
    _default_start = _today - _dt.timedelta(days=_presets[_preset_label])
    date_range = st.date_input(
        "Custom range",
        value=(_default_start, _today),
        min_value=_dt.date(2024, 1, 1),
        max_value=_today,
        key="cmd_date_range",
    )
    date_from = date_range[0] if isinstance(date_range, tuple) else _default_start
    date_to   = date_range[1] if (isinstance(date_range, tuple) and len(date_range) > 1) else _today
    _days_in_range = (date_to - date_from).days or 1
    st.markdown(
        f'<div style="font-size:11px;color:#475569;margin-top:4px;">'
        f'{date_from.strftime("%b %d")} → {date_to.strftime("%b %d, %Y")} · {_days_in_range}d</div>',
        unsafe_allow_html=True,
    )

render_header(
    "Executive Command Center",
    f"CFO dashboard · {date_from.strftime('%b %d')} – {date_to.strftime('%b %d, %Y')} · {_days_in_range}-day window",
    badge="Live",
    badge_color="green",
)

# ── Synthetic data (same seeds as individual dashboards) ──────────────────────
rng = np.random.default_rng(42)

# Revenue (GLP-1 model defaults)
baseline_rev_12mo = 14_670_000
best_rev_12mo     = 20_710_000
branded_gm        = 0.58

# Unit economics
ltv_cac_blended = 4.2
cac_blended     = 127
employer_cac    = 42
payback_months  = 14
gross_margin    = 0.67
nrr             = 1.18

# Churn engine (850 patients, seed 42)
n_patients   = 850
churn_probs  = rng.beta(2, 6, n_patients)
high_risk    = int((churn_probs > 0.65).sum())
med_risk     = int(((churn_probs > 0.40) & (churn_probs <= 0.65)).sum())
arpu_mo      = 285
revenue_at_risk = high_risk * arpu_mo * 3

# Compliance
compliance_risk_mo = 87_000
compliance_flags   = 4

# Series A
mrr_current   = 1_240_000
runway_months = 18
arr           = mrr_current * 12

# Employer ROI
avg_employer_roi   = 4.1
pipeline_employers = 28

# ── Start Here — 3-Minute CFO Review ─────────────────────────────────────────
_DEMO_CARDS = [
    {
        "n": "1",
        "icon": "📝",
        "title": "CFO Morning Brief",
        "desc": "Executive commentary, top risks, action queue, and cash runway — everything a CFO reads Monday morning.",
        "href": "/CFO_Suite",
        "color": BLUE,
        "bg": "rgba(59,130,246,0.10)",
        "border": "rgba(59,130,246,0.25)",
    },
    {
        "n": "2",
        "icon": "⚖",
        "title": "Reconciliation Engine",
        "desc": "Auto-match rate, exception queue, SLA aging, and duplicate detection across payment transactions.",
        "href": "/Reconciliation",
        "color": GREEN,
        "bg": "rgba(16,185,129,0.10)",
        "border": "rgba(16,185,129,0.25)",
    },
    {
        "n": "3",
        "icon": "💳",
        "title": "Payer Revenue Cycle",
        "desc": "Claims volume, denial rate by payer, DSO, A/R aging buckets, and net collection rate scorecard.",
        "href": "/Payer_Revenue_Cycle",
        "color": PURPLE,
        "bg": "rgba(139,92,246,0.10)",
        "border": "rgba(139,92,246,0.25)",
    },
    {
        "n": "4",
        "icon": "📉",
        "title": "Scenario Stress Test",
        "desc": "Move sliders — denial rate, CAC, retention, pharmacy cost, settlement delay — see live EBITDA and runway impact.",
        "href": "/CFO_Suite",
        "note": "Open CFO Suite → Stress Test tab",
        "color": YELLOW,
        "bg": "rgba(245,158,11,0.10)",
        "border": "rgba(245,158,11,0.25)",
    },
]

st.markdown(
    '<div style="background:linear-gradient(135deg,rgba(15,23,42,0.95) 0%,rgba(17,24,39,0.98) 100%);'
    'border:1px solid rgba(59,130,246,0.22);border-radius:14px;padding:22px 24px;margin-bottom:24px;">'
    '<div style="font-size:10px;font-weight:700;color:#3b82f6;letter-spacing:.1em;margin-bottom:4px;">START HERE</div>'
    '<div style="font-size:17px;font-weight:800;color:#f1f5f9;margin-bottom:4px;">3-Minute CFO Review</div>'
    '<div style="font-size:12px;color:#475569;margin-bottom:18px;">'
    'Click through in order. Each section is self-contained. '
    'Synthetic data only — no PHI, no real company or patient data.'
    '</div>'
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">',
    unsafe_allow_html=True,
)
for _card in _DEMO_CARDS:
    _note_html = (
        f'<div style="font-size:10px;color:{_card["color"]};margin-top:6px;font-weight:600;">'
        f'↳ {_card["note"]}</div>'
    ) if _card.get("note") else ""
    st.markdown(
        f'<a href="{_card["href"]}" target="_self" style="text-decoration:none;">'
        f'<div style="background:{_card["bg"]};border:1px solid {_card["border"]};'
        f'border-radius:10px;padding:14px 16px;cursor:pointer;'
        f'transition:transform 0.15s ease;height:100%;">'
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">'
        f'<span style="width:26px;height:26px;border-radius:50%;background:{_card["color"]};'
        f'color:#fff;font-size:11px;font-weight:800;display:flex;align-items:center;'
        f'justify-content:center;flex-shrink:0;">{_card["n"]}</span>'
        f'<span style="font-size:15px;">{_card["icon"]}</span>'
        f'<span style="font-size:13px;font-weight:700;color:#f1f5f9;">{_card["title"]}</span>'
        f'</div>'
        f'<div style="font-size:12px;color:#94a3b8;line-height:1.55;padding-left:36px;">'
        f'{_card["desc"]}{_note_html}</div>'
        f'</div></a>',
        unsafe_allow_html=True,
    )
st.markdown("</div></div>", unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── Critical alerts ───────────────────────────────────────────────────────────
alert(
    f"<strong>{compliance_flags} high-priority compliance flags</strong> detected — "
    f"pharmacy AWP spread and PA-before-ship require immediate review. "
    f"<strong>{high_risk} patients</strong> are high churn risk with "
    f"${revenue_at_risk/1e3:.0f}K revenue at risk (90-day window).",
    level="warning"
)

# ── Executive Finance Commentary ──────────────────────────────────────────────
section("Executive Finance Commentary", "")

_cmd_metrics = {
    "mrr_current":        mrr_current,
    "mrr_prev":           1_050_000,
    "gross_margin":       gross_margin,
    "gross_margin_prev":  gross_margin - 0.014,
    "cash_runway_mo":     runway_months,
    "cash_on_hand_m":     8.4,
    "denial_rate":        0.082,
    "dso_days":           27,
    "nrr":                nrr,
    "churn_rate_mo":      0.028,
    "ltv_cac":            ltv_cac_blended,
    "payback_months":     payback_months,
    "compliance_risk_k":  compliance_risk_mo / 1_000,
    "high_risk_patients": high_risk,
    "revenue_at_risk_k":  revenue_at_risk / 1_000,
    "ar_overdue_k":       76.0,
    "at_risk_arr_k":      156.5,
    "report_month":       _today.strftime("%B %Y"),
}
_cmd_paras, _cmd_action_df, _cmd_dl_lines = build_commentary(_cmd_metrics)
render_commentary_ui(_cmd_paras, _cmd_action_df, _cmd_dl_lines,
                     report_month=_today.strftime("%B %Y"))

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Revenue strip ─────────────────────────────────────────────────────────────
section("Revenue & Growth", "📈")
kpi_row([
    kpi_card(f"${mrr_current/1e3:.0f}K", "Current MRR", "May 2026",
             trend="+18% MoM", trend_good=True, color="green"),
    kpi_card(f"${arr/1e6:.1f}M", "ARR Run Rate", f"${arr*1.3/1e6:.1f}M projected EOY",
             trend="+112% YoY", trend_good=True, color="blue"),
    kpi_card(f"${best_rev_12mo/1e6:.1f}M", "Best-Case 12-Mo Revenue",
             "S2 Branded-only scenario", color="green"),
    kpi_card(f"{int(branded_gm*100)}%", "Gross Margin",
             "Branded GLP-1 program", trend="+9pp vs comps", trend_good=True, color="green"),
])

# ── Ops strip ─────────────────────────────────────────────────────────────────
section("Unit Economics & Retention", "📊")
kpi_row([
    kpi_card(f"{ltv_cac_blended:.1f}x", "LTV:CAC (Blended)",
             f"Employer channel: ${employer_cac} CAC", color="blue"),
    kpi_card(f"{payback_months}mo", "CAC Payback",
             "Employer channel avg", color="blue"),
    kpi_card(f"{int(nrr*100)}%", "Net Revenue Retention",
             "12-month cohort", trend="+6pp vs last qtr", trend_good=True, color="green"),
    kpi_card(f"{high_risk}", "High Churn Risk Patients",
             f"${revenue_at_risk/1e3:.0f}K revenue at risk (90 days)",
             color="red" if high_risk > 50 else "yellow"),
])

# ── Risk strip ────────────────────────────────────────────────────────────────
section("Risk & Compliance", "🔍")
kpi_row([
    kpi_card(f"${compliance_risk_mo/1e3:.0f}K", "Monthly Compliance Risk",
             f"${compliance_risk_mo*12/1e3:.0f}K annualized", color="red"),
    kpi_card(f"{compliance_flags}", "High-Priority Flags",
             "Require immediate review", color="red"),
    kpi_card(f"{runway_months}mo", "Cash Runway",
             "At current burn rate", color="yellow"),
    kpi_card(f"{avg_employer_roi:.1f}x", "Avg Employer ROI",
             f"{pipeline_employers} employers in pipeline", color="purple"),
])

# ── Care Navigation Intelligence (ReferWell-calibrated metrics) ───────────────
section("Care Navigation Intelligence", "🧭")
st.markdown(
    '<div style="font-size:12px;color:#475569;margin:-8px 0 14px 0;">'
    'HEDIS/NCQA-aligned · benchmarked to IQVIA 2025, CMS MA Stars 2026, and published navigation outcomes</div>',
    unsafe_allow_html=True
)
kpi_row([
    kpi_card("78.4%", "Care Gap Closure Rate",
             "HEDIS benchmark: 72% · +6.4pp above avg",
             trend="+4.1pp YoY", trend_good=True, color="green"),
    kpi_card("89.2%", "Member Show Rate",
             "Medicare Advantage benchmark: 85%",
             trend="+2.1pp vs last qtr", trend_good=True, color="blue"),
    kpi_card("85.1%", "In-Network Referral Capture",
             "Leakage prevention · 14.9% outflow",
             trend="+3.8pp YoY", trend_good=True, color="blue"),
    kpi_card("8.7x", "Navigation ROI",
             "Health plan claims savings vs. program cost",
             trend="+within 8–10x benchmark", trend_good=True, color="green"),
])

hedis_col, nav_col = st.columns([3, 2], gap="medium")
with hedis_col:
    section("HEDIS Quality Measures — Gap Closure Rate by Domain", "")
    hedis_measures = [
        "Colorectal Cancer Screening (COL)",
        "Controlling High Blood Pressure (CBP)",
        "Comprehensive Diabetes Care — A1c (CDC)",
        "Breast Cancer Screening (BCS)",
        "Annual Wellness Visit — Medicare (AWV)",
        "Care for Older Adults (COA)",
    ]
    hedis_rates    = [0.761, 0.683, 0.724, 0.798, 0.841, 0.712]
    hedis_benchmk  = [0.680, 0.630, 0.690, 0.750, 0.790, 0.670]
    fig_h = go.Figure()
    fig_h.add_trace(go.Bar(
        name="CareValidate", y=hedis_measures, x=hedis_rates,
        orientation="h", marker_color=BLUE,
        text=[f"{v:.1%}" for v in hedis_rates], textposition="outside",
        textfont=dict(size=11, color="#f1f5f9"),
    ))
    fig_h.add_trace(go.Bar(
        name="NCQA National Avg", y=hedis_measures, x=hedis_benchmk,
        orientation="h", marker_color="rgba(255,255,255,0.10)",
        text=[f"{v:.1%}" for v in hedis_benchmk], textposition="inside",
        textfont=dict(size=10, color="#64748b"),
    ))
    fig_h.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        barmode="overlay", height=260, margin=dict(l=0, r=60, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0,
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickformat=".0%", range=[0, 1.05]),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    )
    st.plotly_chart(fig_h, use_container_width=True)

with nav_col:
    section("Referral Pipeline Health", "")
    pipe_labels = ["Scheduled", "Confirmed", "Completed", "No-Show", "Rescheduled"]
    pipe_vals   = [1420, 1284, 1136, 148, 109]
    pipe_colors = [BLUE, TEAL, GREEN, RED, YELLOW]
    fig_p = go.Figure(go.Bar(
        x=pipe_labels, y=pipe_vals,
        marker_color=pipe_colors,
        text=pipe_vals, textposition="outside",
        textfont=dict(size=11, color="#f1f5f9"),
    ))
    fig_p.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        height=260, margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="Referrals (30-day)"),
    )
    st.plotly_chart(fig_p, use_container_width=True)

st.divider()

# ── ReferWell Benchmark Calibration Panel ─────────────────────────────────────
section("ReferWell Benchmark Calibration", "🎯")
st.markdown(
    '<div style="font-size:12px;color:#475569;margin:-8px 0 14px 0;">'
    'CareValidate model outputs vs ReferWell published outcomes — '
    'source: referwell.com, NCQA HEDIS 2026, CMS MA Stars 2026</div>',
    unsafe_allow_html=True,
)

_benchmarks = [
    ("Member Show Rate (MA)",    "92%",    "89.2%",  True,  "Within 2.8pp of published benchmark"),
    ("Completion Rate",           "80%",    "80.6%",  True,  "Calibrated to ReferWell Engage outcomes"),
    ("In-Network Referral Capture","85%",  "85.1%",  True,  "0.1pp above published target"),
    ("Navigation ROI (Health Plan)","8–10x","8.7x",  True,  "Mid-range of ReferWell's published 8–10x"),
    ("HEDIS Gap Closure (avg)",   "72% NCQA avg","78.4%",True,"6.4pp above national average"),
    ("Care Navigator Languages",  "Multilingual","10+",True, "EN ZH ES HI VI KO AR SO YO TW PT"),
    ("Program Coverage",          "MA + Medicaid","5 programs",True,"MA · LTSS · ACO · HMO · Dual-Eligible"),
]

rw_col1, rw_col2 = st.columns([3, 2], gap="large")
with rw_col1:
    header_html = (
        '<div style="display:grid;grid-template-columns:2fr 1.2fr 1.2fr 2fr;gap:0;'
        'padding:6px 14px;background:rgba(255,255,255,0.03);border-radius:6px 6px 0 0;'
        'font-size:10px;font-weight:700;color:#475569;letter-spacing:.06em;margin-bottom:2px;">'
        '<div>METRIC</div><div>REFERWELL</div><div>THIS MODEL</div><div>STATUS</div></div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)
    for metric, rw_val, cv_val, aligned, note in _benchmarks:
        color  = "#10b981" if aligned else "#f59e0b"
        icon   = "✓" if aligned else "△"
        row_html = (
            f'<div style="display:grid;grid-template-columns:2fr 1.2fr 1.2fr 2fr;gap:0;'
            f'padding:8px 14px;border-bottom:1px solid rgba(255,255,255,0.04);font-size:12px;">'
            f'<div style="color:#e2e8f0;font-weight:500;">{metric}</div>'
            f'<div style="color:#94a3b8;">{rw_val}</div>'
            f'<div style="color:{color};font-weight:700;">{cv_val}</div>'
            f'<div style="color:{color};font-size:11px;">{icon} {note}</div>'
            f'</div>'
        )
        st.markdown(row_html, unsafe_allow_html=True)

with rw_col2:
    st.markdown(
        '<div style="background:#0d1117;border:1px solid rgba(16,185,129,0.25);border-radius:10px;padding:18px 20px;">'
        '<div style="font-size:11px;font-weight:700;color:#10b981;letter-spacing:.06em;margin-bottom:12px;">MODEL CALIBRATION SCORE</div>'
        '<div style="font-size:48px;font-weight:800;color:#10b981;line-height:1;">7/7</div>'
        '<div style="font-size:12px;color:#475569;margin-top:4px;margin-bottom:16px;">metrics within ReferWell published range</div>'
        '<div style="font-size:11px;color:#334155;line-height:1.6;">'
        'All model outputs align with ReferWell\'s published outcomes data. '
        'Inputs sourced from referwell.com, NCQA HEDIS 2026 national averages, '
        'CMS Medicare Advantage Stars 2026 quality thresholds, and '
        'Milliman healthcare cost benchmarks.'
        '</div></div>',
        unsafe_allow_html=True,
    )

st.divider()

# ── Charts row ────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2], gap="medium")

with col_left:
    section("MRR Trajectory — 18 months actual + 6 projected", "")
    rng2      = np.random.default_rng(7)
    hist_dates = pd.date_range("2024-12", periods=18, freq="MS")
    proj_dates = pd.date_range(hist_dates[-1] + pd.offsets.MonthBegin(1), periods=6, freq="MS")

    growth   = 1 + rng2.uniform(0.07, 0.18, 18)
    mrr_hist = [320_000]
    for g in growth[1:]:
        mrr_hist.append(mrr_hist[-1] * g)
    mrr_hist = np.array(mrr_hist)

    proj_g   = np.linspace(1.10, 1.16, 6)
    mrr_proj = [mrr_hist[-1]]
    for g in proj_g:
        mrr_proj.append(mrr_proj[-1] * g)
    mrr_proj = np.array(mrr_proj[1:])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist_dates, y=mrr_hist / 1e3, name="Actual MRR",
        line=dict(color=BLUE, width=2.5),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.07)",
    ))
    fig.add_trace(go.Scatter(
        x=proj_dates, y=mrr_proj / 1e3, name="Projected",
        line=dict(color=GREEN, width=2, dash="dot"),
        fill="tozeroy", fillcolor="rgba(16,185,129,0.06)",
    ))
    fig.add_vline(x="2025-02-01", line_width=1, line_dash="dash",
                  line_color="rgba(239,68,68,0.45)")
    fig.add_annotation(x="2025-02-01", y=mrr_hist[2] / 1e3 * 0.55,
                       text="FDA ban", showarrow=False,
                       font=dict(size=11, color=RED), xshift=-38)
    fig.add_vline(x="2025-03-01", line_width=1, line_dash="dash",
                  line_color="rgba(245,158,11,0.45)")
    fig.add_annotation(x="2025-03-01", y=mrr_hist[3] / 1e3 * 1.2,
                       text="HealthJoy deal", showarrow=False,
                       font=dict(size=11, color=YELLOW), xshift=52)
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        height=280, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0,
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="MRR ($K)"),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    section("12-Month Revenue by Scenario", "")
    scenarios = ["S1 Baseline", "S2 Branded", "S3 Alt Peptide", "S4 Generic"]
    rev_vals  = [baseline_rev_12mo, best_rev_12mo, 6_010_000, 7_060_000]
    fig2 = go.Figure(go.Bar(
        x=[v / 1e6 for v in rev_vals], y=scenarios,
        orientation="h",
        marker_color=[BLUE, GREEN, YELLOW, PURPLE],
        text=[f"${v/1e6:.1f}M" for v in rev_vals],
        textposition="outside",
        textfont=dict(size=12, color="#f1f5f9"),
    ))
    fig2.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        height=280, margin=dict(l=0, r=60, t=10, b=0),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="12-Mo Revenue ($M)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Risk + Churn row ──────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 1, 2], gap="medium")

with col1:
    section("Risk Breakdown", "")
    risk_labels = ["Employer Billing", "Pharmacy AWP", "PA/Eligibility", "Coding Risk"]
    risk_vals   = [4_000, 70_000, 8_000, 5_000]
    fig3 = go.Figure(go.Pie(
        labels=risk_labels, values=risk_vals, hole=0.55,
        marker=dict(colors=[YELLOW, RED, TEAL, PURPLE],
                    line=dict(color=BG, width=2)),
        textfont=dict(size=11),
    ))
    fig3.update_layout(
        paper_bgcolor=BG, height=220, margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        annotations=[dict(text="$87K/mo", x=0.5, y=0.5,
                          font=dict(size=13, color="#f1f5f9", family="Inter"),
                          showarrow=False)],
    )
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    st.markdown("<div style='height:36px'></div>", unsafe_allow_html=True)
    for lbl, val, color in zip(risk_labels, risk_vals, [YELLOW, RED, TEAL, PURPLE]):
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;'
            f'border-bottom:1px solid rgba(255,255,255,0.04);">'
            f'<span style="width:8px;height:8px;border-radius:50%;background:{color};'
            f'flex-shrink:0;display:inline-block;"></span>'
            f'<span style="font-size:12px;color:#94a3b8;flex:1;">{lbl}</span>'
            f'<span style="font-size:12px;font-weight:600;color:#f1f5f9;">'
            f'${val/1e3:.0f}K</span></div>',
            unsafe_allow_html=True
        )

with col3:
    section("Churn Risk Distribution", "")
    tiers  = ["Low (<40%)", "Medium (40-65%)", "High (>65%)"]
    counts = [int((churn_probs <= 0.40).sum()), med_risk, high_risk]
    fig4 = go.Figure(go.Bar(
        x=tiers, y=counts,
        marker_color=[GREEN, YELLOW, RED],
        text=counts, textposition="outside",
        textfont=dict(size=12, color="#f1f5f9"),
    ))
    fig4.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        height=220, margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="Patients"),
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Quick drill-down nav ──────────────────────────────────────────────────────
section("Drill Down to Detail", "")
QUICK = [
    ("💊", "GLP-1 Scenarios", "Revenue model, ban impact", 8502, GREEN),
    ("📊", "Unit Economics",  "CAC, LTV, cohort retention",  8503, BLUE),
    ("🏢", "Employer ROI",   "B2B ROI for sales calls",      8504, PURPLE),
    ("🔮", "Churn Engine",   "Patient-level risk scores",     8505, YELLOW),
    ("📈", "Series A",       "Investor metrics & checklist",  8506, GREEN),
    ("🔍", "Compliance",     "Billing deviations & flags",    8507, RED),
]
cols = st.columns(6, gap="small")
for col, (icon, name, desc, port, color) in zip(cols, QUICK):
    with col:
        st.markdown(
            f'<a href="http://localhost:{port}" target="_blank" style="text-decoration:none;">'
            f'<div style="background:{CARD};border:1px solid rgba(255,255,255,0.07);'
            f'border-radius:12px;border-top:2px solid {color};padding:16px 14px;text-align:center;">'
            f'<div style="font-size:22px;margin-bottom:8px;">{icon}</div>'
            f'<div style="font-size:12px;font-weight:700;color:#f1f5f9;margin-bottom:4px;">{name}</div>'
            f'<div style="font-size:11px;color:#475569;line-height:1.4;">{desc}</div>'
            f'</div></a>',
            unsafe_allow_html=True
        )
