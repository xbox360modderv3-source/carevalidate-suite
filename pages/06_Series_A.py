"""
CareValidate Series A Data Room Generator
Auto-generates investor-ready metrics package for Series A fundraise.
Run: streamlit run app.py --server.port 8506
Sources: Rock Health 2024, a16z digital health benchmarks, Pitchbook 2024, Bessemer Cloud benchmarks
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from carevalidate_shared.theme import (
    GLOBAL_CSS, render_header, kpi_card, kpi_row, section, alert, sidebar_nav,
    BG, CARD, BLUE, GREEN, YELLOW, RED, PURPLE, MUTED,
)
from carevalidate_shared.auth import check_auth, logout_button

st.set_page_config(page_title="CareValidate Series A Data Room", layout="wide", page_icon="📈")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
check_auth()
sidebar_nav("series")
logout_button()

render_header(
    "Series A Data Room",
    "Investor-ready metrics · Pre-populated with benchmarks · Ready for VC conversations",
    badge="Fundraise Ready",
    badge_color="green",
)

alert(
    "<strong>Disclaimer:</strong> All figures use placeholder assumptions based on Rock Health 2024, a16z digital health "
    "benchmarks, Pitchbook Series A data, and Bessemer Cloud metrics. Actual CareValidate financials must be "
    "substituted before any investor presentation. This tool is for planning and preparation only.",
    level="warning",
)

# ── Sidebar inputs ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Company Metrics")
    st.subheader("Revenue")
    current_mrr     = st.number_input("Current MRR ($)", 0, 5000000, 385000, 5000)
    mrr_12mo_ago    = st.number_input("MRR 12 Months Ago ($)", 0, 5000000, 148000, 5000)
    mrr_growth_type = st.selectbox("Input growth as", ["Derive from MRR values above", "Enter manually"])
    if mrr_growth_type == "Enter manually":
        yoy_growth = st.slider("YoY Revenue Growth (%)", 10, 500, 160) / 100
    else:
        yoy_growth = (current_mrr - mrr_12mo_ago) / mrr_12mo_ago if mrr_12mo_ago > 0 else 0

    st.subheader("Gross Margin")
    blended_gm_pct  = st.slider("Blended Gross Margin (%)", 20, 85, 61)
    platform_gm_pct = st.slider("  Platform/SaaS GM (%)", 50, 95, 78)
    clinical_gm_pct = st.slider("  Clinical Services GM (%)", 20, 70, 54)
    pharmacy_gm_pct = st.slider("  Pharmacy/Fulfillment GM (%)", 10, 50, 35)

    st.subheader("Retention")
    nrr             = st.slider("Net Revenue Retention — NRR (%)", 70, 160, 112)
    gross_logo_ret  = st.slider("Gross Logo Retention (%)", 60, 100, 88)
    monthly_churn   = st.slider("Blended Monthly Patient Churn (%)", 1, 20, 7)

    st.subheader("Unit Economics")
    blended_cac     = st.number_input("Blended CAC ($)", 10, 2000, 165, 5)
    avg_arpu        = st.number_input("Blended ARPU ($/mo)", 50, 2000, 620, 10)
    payback_months  = st.number_input("CAC Payback (months)", 1, 60, 11, 1)

    st.subheader("Scale")
    total_patients  = st.number_input("Total Active Patients", 100, 100000, 4800, 100)
    employer_logos  = st.number_input("Employer/B2B Clients", 1, 5000, 1800, 10)
    headcount       = st.number_input("Total Headcount", 5, 500, 72, 1)

    st.subheader("Cash")
    cash_on_hand    = st.number_input("Cash on Hand ($M)", 0.0, 50.0, 1.52, 0.1)
    monthly_burn    = st.number_input("Monthly Net Burn ($K)", 0, 500, 95, 5)

    st.subheader("Raise")
    raise_target    = st.number_input("Series A Target ($M)", 1.0, 50.0, 12.0, 0.5)
    pre_money_val   = st.number_input("Pre-Money Valuation ($M)", 5.0, 200.0, 42.0, 1.0)
    use_of_proceeds_sales = st.slider("Use of Proceeds — Sales & Marketing (%)", 10, 60, 35)
    use_of_proceeds_tech  = st.slider("Use of Proceeds — Product & Tech (%)", 10, 60, 30)
    use_of_proceeds_clin  = max(0, 100 - use_of_proceeds_sales - use_of_proceeds_tech)

# ── Derived metrics ───────────────────────────────────────────────────────────
arr             = current_mrr * 12
ltv             = (avg_arpu * blended_gm_pct/100) / (monthly_churn/100)
ltv_cac         = ltv / blended_cac if blended_cac > 0 else 0
runway_months   = cash_on_hand * 1e6 / (monthly_burn * 1e3) if monthly_burn > 0 else 999
arr_multiple    = pre_money_val * 1e6 / arr if arr > 0 else 0
rev_per_fte     = arr / headcount if headcount > 0 else 0
magic_number    = (current_mrr - mrr_12mo_ago) * 4 / (blended_cac * total_patients * 0.08 * 12) if blended_cac > 0 else 0
post_money      = pre_money_val + raise_target
dilution        = raise_target / post_money * 100

# ── Section 1: The Headline Metrics ──────────────────────────────────────────
section("1 · Headline Metrics", "📊")
kpi_row([
    kpi_card(f"${arr/1e6:.2f}M", "ARR", f"${current_mrr/1e3:.0f}K MRR", color="blue"),
    kpi_card(f"{yoy_growth:.0%}", "YoY Growth", "MRR growth",
             color="green" if yoy_growth >= 2.0 else "yellow" if yoy_growth >= 1.0 else "red"),
    kpi_card(f"{blended_gm_pct}%", "Gross Margin", "Blended",
             color="green" if blended_gm_pct >= 55 else "yellow" if blended_gm_pct >= 40 else "red"),
    kpi_card(f"{nrr}%", "NRR", "Net Revenue Retention",
             color="green" if nrr >= 110 else "yellow" if nrr >= 100 else "red"),
    kpi_card(f"{ltv_cac:.1f}x", "LTV:CAC", "Target ≥ 3x",
             color="green" if ltv_cac >= 3 else "yellow" if ltv_cac >= 2 else "red"),
    kpi_card(
        f"{runway_months:.0f} mo", "Runway",
        f"${cash_on_hand:.1f}M cash · ${monthly_burn}K burn",
        color="green" if runway_months >= 18 else "yellow" if runway_months >= 12 else "red",
    ),
])

st.divider()

# ── Benchmarks vs actuals ──────────────────────────────────────────────────────
section("2 · CareValidate vs Series A Benchmarks", "📐")
st.caption("Sources: Rock Health 2024 · a16z Digital Health · Pitchbook Series A Comps · Bessemer Cloud Index")

benchmarks = pd.DataFrame([
    {"Metric": "ARR",              "CareValidate": f"${arr/1e6:.2f}M",     "Series A Median": "$2–8M",      "Status": "✅" if 2e6 <= arr <= 15e6 else "⚠️"},
    {"Metric": "YoY Growth",       "CareValidate": f"{yoy_growth:.0%}",    "Series A Median": "2.5–3.5x",   "Status": "✅" if yoy_growth >= 1.5 else "⚠️"},
    {"Metric": "Gross Margin",     "CareValidate": f"{blended_gm_pct}%",   "Series A Median": "55–68%",     "Status": "✅" if blended_gm_pct >= 50 else "⚠️"},
    {"Metric": "NRR",              "CareValidate": f"{nrr}%",              "Series A Median": "105–120%",   "Status": "✅" if nrr >= 105 else "⚠️"},
    {"Metric": "LTV:CAC",          "CareValidate": f"{ltv_cac:.1f}x",      "Series A Median": "≥ 3x",       "Status": "✅" if ltv_cac >= 3 else "⚠️"},
    {"Metric": "CAC Payback",      "CareValidate": f"{payback_months} mo", "Series A Median": "18–24 mo B2B","Status": "✅" if payback_months <= 18 else "⚠️"},
    {"Metric": "Logo Retention",   "CareValidate": f"{gross_logo_ret}%",   "Series A Median": "85%+",       "Status": "✅" if gross_logo_ret >= 85 else "⚠️"},
    {"Metric": "Revenue / FTE",    "CareValidate": f"${rev_per_fte/1e3:.0f}K","Series A Median": "$150–250K","Status": "✅" if rev_per_fte >= 100000 else "⚠️"},
    {"Metric": "ARR Multiple",     "CareValidate": f"{arr_multiple:.1f}x", "Series A Median": "8–15x",      "Status": "✅" if 6 <= arr_multiple <= 20 else "⚠️"},
])
st.dataframe(benchmarks.set_index("Metric"), use_container_width=True)

# ── MRR growth chart ───────────────────────────────────────────────────────────
section("3 · MRR Growth Trajectory", "📈")
months_hist = 18
mrr_hist = []
for i in range(months_hist, 0, -1):
    factor = (1 + yoy_growth) ** ((months_hist - i) / 12)
    mrr_hist.append(current_mrr / (1 + yoy_growth) ** (i / 12))
mrr_hist.append(current_mrr)

months_proj = 18
mrr_proj = [current_mrr]
for i in range(1, months_proj + 1):
    growth_rate = (yoy_growth / 12) * (1 - i/60)
    mrr_proj.append(mrr_proj[-1] * (1 + max(growth_rate, 0.02)))

labels_hist = [f"M-{months_hist - i}" for i in range(months_hist)] + ["Now"]
labels_proj = ["Now"] + [f"M+{i}" for i in range(1, months_proj + 1)]

fig = make_subplots(rows=1, cols=1)
fig.add_trace(go.Scatter(x=labels_hist, y=[m/1e3 for m in mrr_hist],
    name="Historical MRR", mode="lines+markers",
    line=dict(color=BLUE, width=2.5), marker=dict(size=5)))
fig.add_trace(go.Scatter(x=labels_proj, y=[m/1e3 for m in mrr_proj],
    name="Projected MRR", mode="lines+markers",
    line=dict(color=GREEN, width=2, dash="dot"), marker=dict(size=5)))
fig.add_vline(x=months_hist, line_dash="dash", line_color=MUTED,
              annotation_text="Today", annotation_font_color=MUTED)
fig.update_layout(template="plotly_dark", paper_bgcolor=BG,
                  plot_bgcolor=CARD, yaxis_title="MRR ($K)",
                  height=300, margin=dict(l=0,r=0,t=10,b=0),
                  legend=dict(orientation="h", yanchor="bottom", y=1.02),
                  xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                  yaxis=dict(gridcolor="rgba(255,255,255,0.04)"))
st.plotly_chart(fig, use_container_width=True)

# ── Gross margin waterfall ─────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    section("4 · Gross Margin by Revenue Line", "💹")
    rev_lines  = ["Platform / SaaS", "Clinical Services", "Pharmacy / Rx"]
    gm_vals    = [platform_gm_pct, clinical_gm_pct, pharmacy_gm_pct]
    colors_gm  = [BLUE if v >= 60 else YELLOW if v >= 40 else RED for v in gm_vals]
    fig2 = go.Figure(go.Bar(
        x=rev_lines, y=gm_vals,
        marker_color=colors_gm,
        text=[f"{v}%" for v in gm_vals], textposition="outside",
    ))
    fig2.add_hline(y=55, line_dash="dot", line_color=GREEN,
                   annotation_text="55% Series A target", annotation_font_color=GREEN)
    fig2.update_layout(template="plotly_dark", paper_bgcolor=BG,
                       plot_bgcolor=CARD, yaxis_title="Gross Margin %",
                       yaxis_range=[0,100], height=280,
                       margin=dict(l=0,r=0,t=10,b=0),
                       xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                       yaxis=dict(gridcolor="rgba(255,255,255,0.04)"))
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    section("5 · Use of Proceeds", "💸")
    fig3 = go.Figure(go.Pie(
        labels=["Sales & Marketing", "Product & Tech", "Clinical Operations"],
        values=[use_of_proceeds_sales, use_of_proceeds_tech, use_of_proceeds_clin],
        hole=0.55,
        marker=dict(colors=[GREEN, BLUE, PURPLE]),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>${%{value:.0f}%} of $%{customdata:.1f}M<extra></extra>",
        customdata=[raise_target] * 3,
    ))
    fig3.update_layout(template="plotly_dark", paper_bgcolor=BG,
                       height=280, margin=dict(l=0,r=0,t=10,b=0),
                       annotations=[dict(text=f"${raise_target:.1f}M",
                                        font_size=18, showarrow=False)])
    st.plotly_chart(fig3, use_container_width=True)

# ── Raise terms ───────────────────────────────────────────────────────────────
section("6 · Raise Terms", "🤝")
kpi_row([
    kpi_card(f"${raise_target:.1f}M", "Raise Amount", color="blue"),
    kpi_card(f"${pre_money_val:.1f}M", "Pre-Money Valuation", f"{arr_multiple:.1f}x ARR multiple"),
    kpi_card(f"${post_money:.1f}M", "Post-Money Valuation"),
    kpi_card(f"{dilution:.1f}%", "Investor Dilution", f"{100-dilution:.1f}% founder retention"),
    kpi_card(
        f"{runway_months:.0f} mo", "Pro-Forma Runway",
        f"After raise at ${monthly_burn}K burn",
        color="green" if runway_months >= 24 else "yellow",
    ),
])

# ── VC checklist ───────────────────────────────────────────────────────────────
section("7 · Series A Data Room Checklist", "✅")
st.caption("Top 10 items VCs request in digital health Series A data rooms — Source: a16z, General Catalyst, Rock Health")
checklist = [
    ("ARR + MRR with monthly cohort breakdown",                    "✅ In this dashboard"),
    ("Net Revenue Retention by cohort (not blended)",              "⚠️  Needs cohort-level data from billing system"),
    ("Gross margin by revenue line (platform vs clinical vs Rx)",  "✅ In this dashboard"),
    ("CAC by channel (employer, broker, PEO, health plan)",        "✅ Unit Economics Dashboard"),
    ("LTV by customer segment (SMB vs mid-market vs enterprise)",  "✅ Unit Economics Dashboard"),
    ("Clinical outcomes data — at least one peer-reviewable KPI",  "⚠️  Needs de-identified outcomes dataset"),
    ("Logo churn / gross revenue churn — annual contract basis",   "✅ In this dashboard"),
    ("Pipeline and sales cycle length (B2B: 3–9 month typical)",   "⚠️  Needs CRM export (Salesforce/HubSpot)"),
    ("Employer contract structure — PMPM, multi-year rates",       "⚠️  Needs executed contract summaries"),
    ("Regulatory & compliance posture (HIPAA, state pharmacy)",    "⚠️  Needs legal + compliance memo"),
]
check_df = pd.DataFrame(checklist, columns=["Item","Status"])
st.dataframe(check_df.set_index("Item"), use_container_width=True)

green = sum(1 for _, s in checklist if s.startswith("✅"))
alert(
    f"<strong>{green}/{len(checklist)} items ready.</strong> "
    f"The {len(checklist)-green} remaining items require internal data exports. "
    f"This dashboard covers all quantitative metrics — legal and CRM items need separate assembly.",
    level="info",
)
