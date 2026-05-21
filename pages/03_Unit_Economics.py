"""
CareValidate Unit Economics & Growth Dashboard
CAC, LTV, Payback, Cohort Retention, PMPM, Series A Metrics
Run: streamlit run dashboard.py --server.port 8503
"""
import sys
import datetime as _dt
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

TEXT = "#f1f5f9"

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from carevalidate_shared.theme import (
    GLOBAL_CSS, render_header, kpi_card, kpi_row, section, alert, sidebar_nav,
    BG, CARD, BLUE, GREEN, YELLOW, RED, PURPLE, TEAL, MUTED,
)
from carevalidate_shared.auth import check_auth, logout_button

st.set_page_config(page_title="CareValidate Unit Economics", layout="wide", page_icon="📊")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
check_auth()
sidebar_nav("units")
logout_button()

render_header(
    "Unit Economics & Growth Dashboard",
    "CAC · LTV · Payback · Cohort Retention · PMPM · Series A Metrics",
    badge="Live Model",
    badge_color="green",
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # Date range
    st.markdown('<div style="font-size:11px;color:#64748b;font-weight:600;letter-spacing:.06em;margin-bottom:6px;">DATE RANGE</div>', unsafe_allow_html=True)
    _today = _dt.date.today()
    _presets_ue = {"Last 30 days": 30, "Last 60 days": 60, "Last 90 days": 90, "YTD": (_today - _dt.date(_today.year, 1, 1)).days}
    _preset_ue = st.selectbox("Quick select", list(_presets_ue.keys()), index=0, key="ue_preset")
    _def_start = _today - _dt.timedelta(days=_presets_ue[_preset_ue])
    _dr = st.date_input("Custom range", value=(_def_start, _today), min_value=_dt.date(2024, 1, 1), max_value=_today, key="ue_date_range")
    date_from = _dr[0] if isinstance(_dr, tuple) else _def_start
    date_to   = _dr[1] if (isinstance(_dr, tuple) and len(_dr) > 1) else _today
    _days_ue  = max((date_to - date_from).days, 1)
    st.markdown(f'<div style="font-size:11px;color:#475569;margin-bottom:12px;">{date_from.strftime("%b %d")} → {date_to.strftime("%b %d, %Y")} · {_days_ue}d</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.header("Assumptions")

    st.subheader("Acquisition")
    cac_organic   = st.number_input("CAC — Organic / SEO ($)", 0, 2000, 85, 5)
    cac_employer  = st.number_input("CAC — Employer / HealthJoy ($)", 0, 2000, 42, 5)
    cac_paid      = st.number_input("CAC — Paid Digital ($)", 0, 5000, 380, 10)
    cac_direct    = st.number_input("CAC — Direct Sales ($)", 0, 5000, 620, 10)
    channel_mix   = st.slider("% Employer Channel (HealthJoy)", 0, 100, 35)
    organic_pct   = st.slider("% Organic", 0, 100 - channel_mix, 30)
    paid_pct      = max(0, 100 - channel_mix - organic_pct - 5)
    direct_pct    = 5
    st.caption(f"Mix: {channel_mix}% Employer | {organic_pct}% Organic | {paid_pct}% Paid | {direct_pct}% Direct")

    st.subheader("Revenue & Margin")
    arpu_glp1      = st.number_input("ARPU — CareGLP ($/mo)", 100, 2000, 950, 25)
    arpu_hrt       = st.number_input("ARPU — CareHRT ($/mo)", 50, 500, 189, 10)
    arpu_derm      = st.number_input("ARPU — CareDERM ($/mo)", 50, 400, 149, 10)
    arpu_accommo   = st.number_input("ARPU — AccommoCare PMPM ($)", 10, 200, 48, 2)
    platform_fee   = st.number_input("White-Label Platform Fee ($/mo/client)", 1000, 50000, 8500, 500)
    gm_glp1        = st.slider("Gross Margin — CareGLP (%)", 10, 80, 58)
    gm_hrt         = st.slider("Gross Margin — CareHRT (%)", 10, 80, 62)
    gm_derm        = st.slider("Gross Margin — CareDERM (%)", 10, 80, 65)
    gm_accommo     = st.slider("Gross Margin — AccommoCare (%)", 20, 80, 55)

    st.subheader("Retention")
    monthly_churn_glp1  = st.slider("Monthly Churn — GLP-1 (%)", 1, 25, 8)
    monthly_churn_hrt   = st.slider("Monthly Churn — HRT (%)", 1, 20, 5)
    monthly_churn_derm  = st.slider("Monthly Churn — Derm (%)", 1, 20, 7)
    monthly_churn_accom = st.slider("Monthly Churn — AccommoCare (%)", 1, 15, 3)

    st.subheader("Scale")
    total_patients = st.number_input("Total Active Patients", 100, 100000, 4800, 100)
    accommo_lives  = st.number_input("AccommoCare Covered Lives", 0, 500000, 28000, 1000)
    platform_clients = st.number_input("White-Label Platform Clients", 1, 50, 7, 1)
    hj_members     = st.number_input("HealthJoy Members", 0, 2000000, 1000000, 10000)
    hj_enrolled_pct= st.slider("% HealthJoy Members Enrolled in a Program", 0, 20, 4)

    st.subheader("G&A & Overhead")
    monthly_fixed  = st.number_input("Monthly Fixed Costs ($)", 0, 1000000, 185000, 5000)
    headcount      = st.number_input("Total Headcount", 10, 500, 72, 1)
    avg_salary     = st.number_input("Avg Fully-Loaded Salary ($)", 40000, 300000, 95000, 5000)

# ── Blended CAC ──────────────────────────────────────────────────────────────
direct_pct_real = max(0, 100 - channel_mix - organic_pct - paid_pct)
blended_cac = (
    (channel_mix/100) * cac_employer +
    (organic_pct/100) * cac_organic  +
    (paid_pct/100)    * cac_paid     +
    (direct_pct_real/100) * cac_direct
)

# ── LTV calculations ──────────────────────────────────────────────────────────
def calc_ltv(arpu, gm_pct, monthly_churn_pct):
    gm     = arpu * gm_pct / 100
    churn  = monthly_churn_pct / 100
    avg_life_months = 1 / churn if churn > 0 else 999
    ltv    = gm * avg_life_months
    return ltv, avg_life_months

ltv_glp1, life_glp1   = calc_ltv(arpu_glp1, gm_glp1, monthly_churn_glp1)
ltv_hrt,  life_hrt    = calc_ltv(arpu_hrt,  gm_hrt,  monthly_churn_hrt)
ltv_derm, life_derm   = calc_ltv(arpu_derm, gm_derm, monthly_churn_derm)
ltv_accom,life_accom  = calc_ltv(arpu_accommo, gm_accommo, monthly_churn_accom)

payback_glp1 = blended_cac / (arpu_glp1 * gm_glp1/100) if arpu_glp1 > 0 else 0
payback_hrt  = blended_cac / (arpu_hrt  * gm_hrt /100)  if arpu_hrt  > 0 else 0
payback_derm = blended_cac / (arpu_derm * gm_derm/100)  if arpu_derm > 0 else 0

# ── Revenue build ─────────────────────────────────────────────────────────────
hj_enrolled         = int(hj_members * hj_enrolled_pct / 100)
glp1_patients       = int(total_patients * 0.52)
hrt_patients        = int(total_patients * 0.28)
derm_patients       = int(total_patients * 0.20)
mrr_glp1            = glp1_patients * arpu_glp1
mrr_hrt             = hrt_patients  * arpu_hrt
mrr_derm            = derm_patients * arpu_derm
mrr_accommo         = accommo_lives * arpu_accommo
mrr_platform        = platform_clients * platform_fee
total_mrr           = mrr_glp1 + mrr_hrt + mrr_derm + mrr_accommo + mrr_platform
arr                 = total_mrr * 12
gp_monthly          = (mrr_glp1*gm_glp1/100 + mrr_hrt*gm_hrt/100 +
                       mrr_derm*gm_derm/100 + mrr_accommo*gm_accommo/100 +
                       mrr_platform*0.72)
blended_gm          = gp_monthly / total_mrr if total_mrr > 0 else 0
contribution_margin = gp_monthly - monthly_fixed
burn_rate           = max(0, -contribution_margin)
revenue_per_head    = arr / headcount if headcount > 0 else 0
annual_people_cost  = headcount * avg_salary

# ── KPI Row 1: Revenue ────────────────────────────────────────────────────────
section("Revenue & Scale", "💰")
kpi_row([
    kpi_card(f"${total_mrr/1e3:.0f}K", "MRR", f"ARR ${arr/1e6:.2f}M", color="blue"),
    kpi_card(f"{total_patients:,}", "Active Patients", f"+{hj_enrolled:,} via HealthJoy"),
    kpi_card(
        f"{blended_gm:.0%}", "Blended Gross Margin",
        "Above 55% target" if blended_gm >= 0.55 else "Below 55% target",
        color="green" if blended_gm >= 0.55 else "yellow",
    ),
    kpi_card(f"${gp_monthly/1e3:.0f}K", "Monthly Gross Profit",
             f"CM: ${contribution_margin/1e3:.0f}K/mo",
             color="green" if contribution_margin >= 0 else "red"),
    kpi_card(f"${revenue_per_head/1e3:.0f}K", "Revenue / Head",
             f"{headcount} headcount · ${arr/1e6:.1f}M ARR"),
])

# ── KPI Row 2: Unit Economics ─────────────────────────────────────────────────
section("Unit Economics — CAC · LTV · Payback", "📐")
ltv_cac_glp1 = ltv_glp1 / blended_cac if blended_cac > 0 else 0
kpi_row([
    kpi_card(
        f"${blended_cac:.0f}", "Blended CAC",
        f"Employer ${cac_employer} · Organic ${cac_organic}",
        color="green" if blended_cac < 200 else "yellow" if blended_cac < 400 else "red",
    ),
    kpi_card(
        f"${ltv_glp1:.0f}", "LTV — CareGLP",
        f"Life: {life_glp1:.1f} mo · {monthly_churn_glp1}% churn",
        color="green" if ltv_glp1 > blended_cac*3 else "yellow",
    ),
    kpi_card(
        f"{ltv_cac_glp1:.1f}x", "LTV:CAC — GLP-1",
        "Target ≥ 3x",
        color="green" if ltv_cac_glp1 >= 3 else "yellow" if ltv_cac_glp1 >= 2 else "red",
    ),
    kpi_card(
        f"{payback_glp1:.1f} mo", "CAC Payback — GLP-1",
        "Target ≤ 12 mo",
        color="green" if payback_glp1 <= 12 else "yellow" if payback_glp1 <= 18 else "red",
    ),
])

st.divider()

# ── Charts row 1 ──────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("LTV vs CAC by Product")
    products_ue = ["CareGLP", "CareHRT", "CareDERM", "AccommoCare"]
    ltvs        = [ltv_glp1, ltv_hrt, ltv_derm, ltv_accom]
    colors      = [BLUE, GREEN, PURPLE, RED]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="LTV", x=products_ue, y=ltvs,
                         marker_color=colors, text=[f"${v:.0f}" for v in ltvs],
                         textposition="outside"))
    fig.add_trace(go.Scatter(name="Blended CAC", x=products_ue,
                             y=[blended_cac]*4, mode="lines+markers",
                             line=dict(color=RED, dash="dash", width=2),
                             marker=dict(size=8)))
    fig.add_hrect(y0=0, y1=blended_cac*3, fillcolor="rgba(16,185,129,0.04)",
                  line_width=0, annotation_text="3x CAC floor", annotation_position="top left",
                  annotation_font_color=MUTED)
    fig.update_layout(template="plotly_dark", paper_bgcolor=BG,
                      plot_bgcolor=CARD, height=300,
                      margin=dict(l=0, r=0, t=10, b=0), barmode="group",
                      yaxis_title="$ per Patient",
                      xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                      yaxis=dict(gridcolor="rgba(255,255,255,0.04)"))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("MRR Breakdown by Product")
    labels = ["CareGLP", "CareHRT", "CareDERM", "AccommoCare", "Platform"]
    values = [mrr_glp1, mrr_hrt, mrr_derm, mrr_accommo, mrr_platform]
    fig2 = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.55,
        marker=dict(colors=[BLUE, GREEN, PURPLE, RED, YELLOW]),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}/mo<extra></extra>",
    ))
    fig2.update_layout(template="plotly_dark", paper_bgcolor=BG,
                       height=300, margin=dict(l=0, r=0, t=10, b=0),
                       annotations=[dict(text=f"${total_mrr/1e3:.0f}K<br>MRR",
                                         font_size=14, showarrow=False, font_color=TEXT)])
    st.plotly_chart(fig2, use_container_width=True)

# ── Cohort retention ──────────────────────────────────────────────────────────
section("Cohort Retention Curves — 24 Month", "📉")
months_r = np.arange(0, 25)
fig3 = go.Figure()
for pname, churn, color in [
    ("CareGLP",      monthly_churn_glp1/100,  BLUE),
    ("CareHRT",      monthly_churn_hrt/100,   GREEN),
    ("CareDERM",     monthly_churn_derm/100,  PURPLE),
    ("AccommoCare",  monthly_churn_accom/100, RED),
]:
    retention = (1 - churn) ** months_r * 100
    fig3.add_trace(go.Scatter(
        x=months_r, y=retention, name=pname, mode="lines",
        line=dict(color=color, width=2.5),
        hovertemplate=f"<b>{pname}</b><br>Month %{{x}}: %{{y:.1f}}% retained<extra></extra>"
    ))
fig3.add_hline(y=50, line_dash="dot", line_color=MUTED,
               annotation_text="50% retention threshold", annotation_font_color=MUTED)
fig3.update_layout(
    template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
    yaxis_title="% of Cohort Retained", xaxis_title="Month",
    height=280, margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
)
st.plotly_chart(fig3, use_container_width=True)

# ── CAC payback waterfall ──────────────────────────────────────────────────────
col3, col4 = st.columns(2)
with col3:
    st.subheader("CAC Payback by Channel")
    channels = ["Organic", "Employer\n(HealthJoy)", "Paid Digital", "Direct Sales"]
    cacs_ch  = [cac_organic, cac_employer, cac_paid, cac_direct]
    gm_mo    = arpu_glp1 * gm_glp1 / 100
    paybacks = [c / gm_mo if gm_mo > 0 else 0 for c in cacs_ch]
    colors_pb = [GREEN if p <= 12 else YELLOW if p <= 18 else RED for p in paybacks]
    fig4 = go.Figure(go.Bar(
        x=channels, y=paybacks,
        marker_color=colors_pb,
        text=[f"{p:.1f} mo" for p in paybacks],
        textposition="outside",
    ))
    fig4.add_hline(y=12, line_dash="dash", line_color=GREEN,
                   annotation_text="12-mo target", annotation_font_color=GREEN)
    fig4.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        yaxis_title="Payback (Months)", height=280,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    )
    st.plotly_chart(fig4, use_container_width=True)

with col4:
    st.subheader("PMPM Economics — AccommoCare")
    pmpm_arpu   = arpu_accommo
    pmpm_cogs   = pmpm_arpu * (1 - gm_accommo/100)
    pmpm_gp     = pmpm_arpu * gm_accommo/100
    pmpm_alloc  = monthly_fixed / max(accommo_lives, 1)
    pmpm_cm     = pmpm_gp - pmpm_alloc

    fig5 = go.Figure(go.Waterfall(
        name="PMPM",
        orientation="v",
        measure=["absolute","relative","relative","total"],
        x=["ARPU","COGS","Overhead Alloc","Contribution Margin"],
        y=[pmpm_arpu, -pmpm_cogs, -pmpm_alloc, 0],
        connector={"line": {"color": "rgba(255,255,255,0.1)"}},
        decreasing={"marker": {"color": RED}},
        increasing={"marker": {"color": GREEN}},
        totals={"marker": {"color": BLUE}},
        text=[f"${pmpm_arpu:.2f}", f"-${pmpm_cogs:.2f}",
              f"-${pmpm_alloc:.2f}", f"${pmpm_cm:.2f}"],
        textposition="outside",
    ))
    fig5.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        yaxis_title="$ per Member per Month", height=280,
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    )
    st.plotly_chart(fig5, use_container_width=True)

# ── Series A Metrics ──────────────────────────────────────────────────────────
st.divider()
section("Series A Investor Metrics", "📈")
magic_number = contribution_margin / (blended_cac * (total_patients * 0.08)) if blended_cac > 0 else 0
rule_of_40   = (arr / 1e6 * 0.35 * 100) + (blended_gm * 100)  # growth + margin proxy
nrr_proxy    = 100 + (1 - monthly_churn_glp1/100)**12 * 15 - 5

kpi_row([
    kpi_card(f"${arr/1e6:.2f}M", "ARR", "Annual Recurring Revenue", color="blue"),
    kpi_card(f"{blended_gm:.0%}", "Gross Margin", "Target 55%+",
             color="green" if blended_gm >= 0.55 else "yellow"),
    kpi_card(f"{ltv_cac_glp1:.1f}x", "LTV:CAC", "Target 3x+",
             color="green" if ltv_cac_glp1 >= 3 else "yellow" if ltv_cac_glp1 >= 2 else "red"),
    kpi_card(f"{payback_glp1:.1f} mo", "CAC Payback", "Target ≤12 mo",
             color="green" if payback_glp1 <= 12 else "yellow"),
    kpi_card(f"~{nrr_proxy:.0f}%", "NRR (Est.)", "Target 110%+",
             color="green" if nrr_proxy >= 110 else "yellow"),
    kpi_card(f"${revenue_per_head/1e3:.0f}K", "Rev/FTE", f"{headcount} headcount"),
])

# ── Sensitivity: LTV:CAC at different churn levels ────────────────────────────
section("LTV:CAC Sensitivity — Churn vs ARPU (CareGLP)", "🔬")
churn_range = np.arange(3, 20, 1)
arpu_range  = np.arange(500, 1400, 100)
z = np.zeros((len(churn_range), len(arpu_range)))
for i, ch in enumerate(churn_range):
    for j, ar in enumerate(arpu_range):
        ltv_s, _ = calc_ltv(ar, gm_glp1, ch)
        z[i, j] = ltv_s / blended_cac if blended_cac > 0 else 0

fig6 = go.Figure(go.Heatmap(
    z=z, x=arpu_range, y=churn_range,
    colorscale=[[0, RED],[0.33, YELLOW],[0.67, GREEN],[1.0, BLUE]],
    zmin=0, zmax=8,
    colorbar=dict(title="LTV:CAC"),
    hovertemplate="ARPU $%{x}<br>Churn %{y}%<br>LTV:CAC %{z:.1f}x<extra></extra>",
    text=np.round(z, 1),
    texttemplate="%{text}x",
))
fig6.add_shape(type="rect",
               x0=arpu_glp1-50, x1=arpu_glp1+50,
               y0=monthly_churn_glp1-0.5, y1=monthly_churn_glp1+0.5,
               line=dict(color="white", width=2))
fig6.add_annotation(x=arpu_glp1, y=monthly_churn_glp1,
                    text="Current", showarrow=True, arrowhead=2,
                    arrowcolor="white", font=dict(color="white", size=11))
fig6.update_layout(
    template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
    xaxis_title="Monthly ARPU ($)", yaxis_title="Monthly Churn (%)",
    height=340, margin=dict(l=0, r=0, t=10, b=0),
)
st.plotly_chart(fig6, use_container_width=True)

# ── Detailed product table ─────────────────────────────────────────────────────
section("Product Line Summary", "📋")
product_table = pd.DataFrame([
    {"Product": "CareGLP",      "Patients": glp1_patients, "ARPU": arpu_glp1,
     "Gross Margin": f"{gm_glp1}%", "Monthly Churn": f"{monthly_churn_glp1}%",
     "LTV": f"${ltv_glp1:.0f}", "Payback": f"{payback_glp1:.1f} mo",
     "MRR": f"${mrr_glp1/1e3:.0f}K"},
    {"Product": "CareHRT",      "Patients": hrt_patients, "ARPU": arpu_hrt,
     "Gross Margin": f"{gm_hrt}%",  "Monthly Churn": f"{monthly_churn_hrt}%",
     "LTV": f"${ltv_hrt:.0f}",  "Payback": f"{payback_hrt:.1f} mo",
     "MRR": f"${mrr_hrt/1e3:.0f}K"},
    {"Product": "CareDERM",     "Patients": derm_patients, "ARPU": arpu_derm,
     "Gross Margin": f"{gm_derm}%", "Monthly Churn": f"{monthly_churn_derm}%",
     "LTV": f"${ltv_derm:.0f}", "Payback": f"{payback_derm:.1f} mo",
     "MRR": f"${mrr_derm/1e3:.0f}K"},
    {"Product": "AccommoCare",  "Patients": accommo_lives, "ARPU": arpu_accommo,
     "Gross Margin": f"{gm_accommo}%","Monthly Churn": f"{monthly_churn_accom}%",
     "LTV": f"${ltv_accom:.0f}","Payback": "N/A (B2B)",
     "MRR": f"${mrr_accommo/1e3:.0f}K"},
    {"Product": "White-Label Platform", "Patients": f"{platform_clients} clients",
     "ARPU": platform_fee, "Gross Margin": "72%", "Monthly Churn": "~1%",
     "LTV": "N/A", "Payback": "N/A",
     "MRR": f"${mrr_platform/1e3:.0f}K"},
])
st.dataframe(product_table.set_index("Product"), use_container_width=True)

# ── Bundle Upsell Simulator ───────────────────────────────────────────────────
section("Bundle Upsell Simulator — ARPU Expansion Without New CAC", "💡")
st.caption("Model the revenue impact of cross-selling HRT, metabolic labs, or CGM to existing GLP-1 patients.")

up_col1, up_col2 = st.columns(2, gap="large")
with up_col1:
    upsell_pct_hrt  = st.slider("% of GLP-1 patients adding CareHRT", 0, 40, 12)
    upsell_pct_labs = st.slider("% of GLP-1 patients adding metabolic labs", 0, 60, 25)
    upsell_pct_cgm  = st.slider("% of GLP-1 patients adding CGM monitoring", 0, 30, 8)
    hrt_add_arpu    = st.number_input("HRT add-on ARPU ($/mo)", value=89, step=5)
    labs_add_arpu   = st.number_input("Labs add-on ARPU ($/mo)", value=35, step=5)
    cgm_add_arpu    = st.number_input("CGM monitoring ARPU ($/mo)", value=55, step=5)

with up_col2:
    upsell_pts_hrt  = int(glp1_patients * upsell_pct_hrt  / 100)
    upsell_pts_labs = int(glp1_patients * upsell_pct_labs / 100)
    upsell_pts_cgm  = int(glp1_patients * upsell_pct_cgm  / 100)

    incremental_mrr = (upsell_pts_hrt  * hrt_add_arpu +
                       upsell_pts_labs * labs_add_arpu +
                       upsell_pts_cgm  * cgm_add_arpu)
    new_blended_arpu = arpu_glp1 + (
        upsell_pct_hrt/100 * hrt_add_arpu +
        upsell_pct_labs/100 * labs_add_arpu +
        upsell_pct_cgm/100 * cgm_add_arpu
    )
    arpu_lift_pct = (new_blended_arpu - arpu_glp1) / arpu_glp1

    kpi_row([
        kpi_card(f"${incremental_mrr/1e3:.0f}K", "Incremental MRR",
                 "Zero additional CAC", color="green"),
        kpi_card(f"${incremental_mrr*12/1e3:.0f}K", "Incremental ARR",
                 "Run-rate revenue expansion", color="green"),
        kpi_card(f"${new_blended_arpu:.0f}", "New Blended ARPU",
                 f"vs ${arpu_glp1} baseline (+{arpu_lift_pct:.0%})", color="blue"),
        kpi_card(f"${incremental_mrr*12 / max(glp1_patients*cac_employer,1):.1f}x",
                 "Upsell ROI",
                 "Incremental ARR ÷ original employer CAC", color="purple"),
    ])

alert(
    f"Cross-selling to <strong>{upsell_pts_hrt + upsell_pts_labs + upsell_pts_cgm} existing GLP-1 patients</strong> "
    f"generates <strong>${incremental_mrr/1e3:.0f}K/month (${incremental_mrr*12/1e3:.0f}K/year)</strong> "
    f"in incremental revenue with <strong>zero additional CAC spend</strong>. "
    f"Blended ARPU lifts from ${arpu_glp1} → ${new_blended_arpu:.0f}/mo (+{arpu_lift_pct:.0%}). "
    f"Each upsold patient extends effective LTV without restarting the payback clock.",
    level="success",
)


st.divider()

# ── Contribution Margin Waterfall ─────────────────────────────────────────────
section("Contribution Margin Waterfall — By Product Line", "📉")
st.markdown(
    '<div style="font-size:12px;color:#475569;margin:-8px 0 14px 0;">'
    'Revenue → COGS → Gross Profit → S&amp;M → R&amp;D → G&amp;A → EBITDA · '
    'SaaS unit economics framework per Bessemer Venture Partners benchmarks</div>',
    unsafe_allow_html=True
)

products_wf = ["CareGLP", "CareHRT", "CareDERM", "AccommoCare", "White-Label"]
rev_wf      = [mrr_glp1, mrr_hrt, mrr_derm, mrr_accommo, mrr_platform]
cogs_pct    = [0.42, 0.38, 0.31, 0.25, 0.28]  # COGS as % of rev
sm_pct      = [0.18, 0.22, 0.19, 0.28, 0.12]  # S&M
rd_pct      = [0.08, 0.08, 0.08, 0.06, 0.07]  # R&D
ga_pct      = [0.07, 0.07, 0.07, 0.07, 0.06]  # G&A

wf_rows = []
for i, prod in enumerate(products_wf):
    rev  = rev_wf[i]
    cogs = rev * cogs_pct[i]
    gp   = rev - cogs
    sm   = rev * sm_pct[i]
    rd   = rev * rd_pct[i]
    ga   = rev * ga_pct[i]
    ebit = gp - sm - rd - ga
    wf_rows.append({
        "Product":      prod,
        "Revenue":      rev,
        "COGS":         -cogs,
        "Gross Profit": gp,
        "S&M":          -sm,
        "R&D":          -rd,
        "G&A":          -ga,
        "EBITDA":       ebit,
        "GM%":          gp / rev,
        "EBITDA%":      ebit / rev,
    })
wf_df = pd.DataFrame(wf_rows)

wf_col1, wf_col2 = st.columns([3, 2], gap="medium")
with wf_col1:
    fig_wf = go.Figure()
    bar_items = [("Revenue","Revenue",BLUE), ("COGS","COGS",RED),
                 ("S&M","S&M",YELLOW), ("R&D","R&D",PURPLE), ("G&A","G&A","#f97316")]
    for col, label, color in bar_items:
        vals = wf_df[col].tolist()
        fig_wf.add_trace(go.Bar(
            name=label, x=wf_df["Product"], y=vals,
            marker_color=color,
            text=[f"${abs(v)/1e3:.0f}K" for v in vals],
            textposition="inside", textfont=dict(size=10, color="#f1f5f9"),
        ))
    fig_wf.add_trace(go.Scatter(
        name="EBITDA", x=wf_df["Product"], y=wf_df["EBITDA"],
        mode="markers+text", marker=dict(color=GREEN, size=10, symbol="diamond"),
        text=[f"${v/1e3:.0f}K" for v in wf_df["EBITDA"]],
        textposition="top center", textfont=dict(size=11, color=GREEN),
    ))
    fig_wf.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        barmode="relative", height=300, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0,
                    font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="$/mo"),
    )
    st.plotly_chart(fig_wf, use_container_width=True)

with wf_col2:
    margin_disp = wf_df[["Product","GM%","EBITDA%","Revenue"]].copy()
    for _, row in margin_disp.iterrows():
        gm_color  = GREEN if row["GM%"] > 0.60 else (YELLOW if row["GM%"] > 0.45 else RED)
        eb_color  = GREEN if row["EBITDA%"] > 0.15 else (YELLOW if row["EBITDA%"] > 0 else RED)
        st.markdown(
            f'<div style="padding:10px 14px;background:{CARD};border:1px solid rgba(255,255,255,0.06);'
            f'border-radius:10px;margin-bottom:6px;display:flex;align-items:center;gap:12px;">'
            f'<div style="min-width:100px;font-size:12px;font-weight:700;color:#f1f5f9;">{row["Product"]}</div>'
            f'<div style="flex:1;font-size:11px;color:#475569;">GM: <span style="color:{gm_color};font-weight:700;">{row["GM%"]:.0%}</span></div>'
            f'<div style="flex:1;font-size:11px;color:#475569;">EBITDA: <span style="color:{eb_color};font-weight:700;">{row["EBITDA%"]:.0%}</span></div>'
            f'<div style="font-size:11px;color:#334155;">${row["Revenue"]/1e3:.0f}K/mo</div>'
            f'</div>',
            unsafe_allow_html=True
        )

st.divider()

# ── Payment Processing Cost Model ─────────────────────────────────────────────
section("Payment Processing Cost Model — Stripe / ACH / Chargeback Analysis", "💳")
st.markdown(
    '<div style="font-size:12px;color:#475569;margin:-8px 0 14px 0;">'
    'Processing fees reduce net revenue. Optimizing ACH mix and reducing chargebacks '
    'is often a $50K–$200K/year opportunity at this ARR scale.</div>',
    unsafe_allow_html=True
)

pay_c1, pay_c2 = st.columns(2, gap="large")
with pay_c1:
    total_monthly_rev = sum(rev_wf)
    pct_card  = st.slider("% transactions on credit/debit card", 20, 80, 55, 5, format="%d%%")
    pct_ach   = 100 - pct_card
    chargeback_rate = st.slider("Chargeback rate (basis points)", 5, 50, 18, 1, format="%d bps")

with pay_c2:
    card_vol   = total_monthly_rev * pct_card / 100
    ach_vol    = total_monthly_rev * pct_ach  / 100
    card_fee   = card_vol * 0.029 + (card_vol / 285) * 0.30  # 2.9% + $0.30/tx
    ach_fee    = (ach_vol / 285) * 0.80                       # $0.80 flat per ACH tx
    cb_cost    = total_monthly_rev * (chargeback_rate / 10000) * 35  # $35 dispute fee avg
    total_fee  = card_fee + ach_fee + cb_cost
    net_take   = total_monthly_rev - total_fee
    fee_pct    = total_fee / total_monthly_rev

    kpi_row([
        kpi_card(f"${total_fee/1e3:.1f}K", "Monthly Processing Cost",
                 f"${total_fee*12/1e3:.0f}K annualized", color="yellow"),
        kpi_card(f"{fee_pct:.2%}", "Effective Fee Rate",
                 f"Stripe avg: 2.9% · ACH avg: 0.28%", color="yellow"),
        kpi_card(f"${net_take/1e3:.0f}K", "Net Revenue After Fees",
                 f"of ${total_monthly_rev/1e3:.0f}K gross", color="blue"),
        kpi_card(f"${(card_fee - (card_vol * 0.005 + card_vol/285 * 0.80))/12/1e3:.0f}K",
                 "Annual Savings (ACH Migration)",
                 "Shift 20pp card → ACH at current volume", color="green"),
    ])

st.divider()

# ── Patient Profitability Segmentation ────────────────────────────────────────
section("Patient Profitability Segmentation", "👤")
st.markdown(
    '<div style="font-size:12px;color:#475569;margin:-8px 0 14px 0;">'
    'LTV:CAC ratio by acquisition channel and product — identifies highest-ROI growth levers. '
    'Bubble size = patient count. Quadrant target: LTV:CAC > 3x, Payback < 18mo.</div>',
    unsafe_allow_html=True
)

seg_data = [
    ("CareGLP",     "Employer",   4.8, 42,   320),
    ("CareGLP",     "DTC",        3.1, 138,  180),
    ("CareGLP",     "Health Plan",6.2, 28,   95),
    ("CareHRT",     "Employer",   3.9, 52,   145),
    ("CareHRT",     "DTC",        2.4, 142,  88),
    ("CareDERM",    "Employer",   3.3, 48,   62),
    ("CareDERM",    "DTC",        2.1, 155,  41),
    ("AccommoCare", "Employer",   5.1, 38,   210),
    ("AccommoCare", "Health Plan",7.8, 18,   310),
]
seg_df = pd.DataFrame(seg_data, columns=["Product","Channel","LTV_CAC","Payback_Mo","Patients"])
seg_df["LTV"]  = seg_df["LTV_CAC"] * seg_df["Payback_Mo"] * 285 / 12 * 12
seg_df["CAC"]  = seg_df["Payback_Mo"] * 285 / 12
colors_seg = {p: c for p, c in zip(
    ["CareGLP","CareHRT","CareDERM","AccommoCare"],
    [BLUE, GREEN, PURPLE, TEAL]
)}

fig_seg = go.Figure()
for prod in seg_df["Product"].unique():
    sub = seg_df[seg_df["Product"] == prod]
    fig_seg.add_trace(go.Scatter(
        name=prod, x=sub["Payback_Mo"], y=sub["LTV_CAC"],
        mode="markers+text",
        marker=dict(size=[p/8 for p in sub["Patients"]], color=colors_seg.get(prod, BLUE),
                    opacity=0.8, line=dict(color="rgba(255,255,255,0.2)", width=1)),
        text=sub["Channel"], textposition="top center",
        textfont=dict(size=10, color="#94a3b8"),
    ))
fig_seg.add_hline(y=3, line_width=1, line_dash="dash", line_color="rgba(16,185,129,0.4)")
fig_seg.add_vline(x=18, line_width=1, line_dash="dash", line_color="rgba(245,158,11,0.4)")
fig_seg.add_annotation(x=19, y=7.5, text="Target zone →", showarrow=False,
                       font=dict(size=10, color="#334155"))
fig_seg.update_layout(
    template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
    height=320, margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1, x=0,
                font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="CAC Payback (months)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="LTV:CAC Ratio"),
)
st.plotly_chart(fig_seg, use_container_width=True)

st.divider()

# ── Refund Rate Analysis ───────────────────────────────────────────────────────
section("Refund Rate & Churn Cost Analysis", "↩")
st.markdown(
    '<div style="font-size:12px;color:#475569;margin:-8px 0 14px 0;">'
    'Refunds represent lost revenue AND a processing cost. Each refund costs ~$15 in ops overhead '
    'plus the original processing fee (non-refundable on Stripe). Target: &lt;2% refund rate.</div>',
    unsafe_allow_html=True
)

ref_products  = ["CareGLP", "CareHRT", "CareDERM", "AccommoCare", "White-Label"]
ref_rates     = [0.018, 0.023, 0.031, 0.009, 0.005]
ref_reasons   = {
    "CareGLP":     [("Side effects", 0.41), ("Cost", 0.28), ("No results", 0.19), ("Other", 0.12)],
    "CareHRT":     [("Side effects", 0.38), ("No results", 0.31), ("Cost", 0.21), ("Other", 0.10)],
    "CareDERM":    [("No results", 0.44), ("Side effects", 0.29), ("Cost", 0.18), ("Other", 0.09)],
    "AccommoCare": [("Employer dropped", 0.52), ("Member left company", 0.31), ("Other", 0.17)],
    "White-Label": [("Contract ended", 0.60), ("Budget cut", 0.28), ("Other", 0.12)],
}
ref_patients  = [glp1_patients, hrt_patients, derm_patients, accommo_lives, platform_clients * 50]
ref_arpu      = [arpu_glp1, arpu_hrt, arpu_derm, arpu_accommo, platform_fee]

ref_c1, ref_c2 = st.columns([2, 3], gap="medium")
with ref_c1:
    fig_r = go.Figure(go.Bar(
        y=ref_products, x=[r * 100 for r in ref_rates],
        orientation="h",
        marker_color=[GREEN if r < 0.02 else (YELLOW if r < 0.03 else RED) for r in ref_rates],
        text=[f"{r:.1%}" for r in ref_rates], textposition="outside",
        textfont=dict(size=11, color="#f1f5f9"),
    ))
    fig_r.add_vline(x=2, line_width=1, line_dash="dash", line_color="rgba(16,185,129,0.5)")
    fig_r.add_annotation(x=2.1, y=4, text="2% target", showarrow=False,
                         font=dict(size=10, color=GREEN))
    fig_r.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        height=260, margin=dict(l=0, r=60, t=10, b=0),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", ticksuffix="%", title="Refund Rate"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    )
    st.plotly_chart(fig_r, use_container_width=True)

with ref_c2:
    total_refund_mo = sum(ref_rates[i] * ref_patients[i] * ref_arpu[i]
                          for i in range(len(ref_products)))
    total_refund_ops = sum(ref_rates[i] * ref_patients[i] * 15 for i in range(len(ref_products)))
    total_refund_fee = sum(ref_rates[i] * ref_patients[i] * ref_arpu[i] * 0.029
                           for i in range(len(ref_products)))

    kpi_row([
        kpi_card(f"${total_refund_mo/1e3:.1f}K", "Monthly Refund Volume",
                 f"${total_refund_mo*12/1e3:.0f}K annualized", color="yellow"),
        kpi_card(f"${(total_refund_ops + total_refund_fee)/1e3:.1f}K",
                 "Monthly Refund Overhead",
                 "Ops processing + non-refundable Stripe fee", color="red"),
    ])
    selected_prod = st.selectbox("Refund reason breakdown", ref_products, key="refund_prod")
    idx = ref_products.index(selected_prod)
    reasons, pcts = zip(*ref_reasons[selected_prod])
    for reason, pct in zip(reasons, pcts):
        bar_w = int(pct * 100)
        st.markdown(
            f'<div style="margin-bottom:8px;">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:3px;">'
            f'<span style="font-size:12px;color:#94a3b8;">{reason}</span>'
            f'<span style="font-size:12px;font-weight:600;color:#f1f5f9;">{pct:.0%}</span>'
            f'</div>'
            f'<div style="background:rgba(255,255,255,0.06);border-radius:4px;height:6px;">'
            f'<div style="width:{bar_w}%;background:{RED};border-radius:4px;height:6px;"></div>'
            f'</div></div>',
            unsafe_allow_html=True
        )

alert(
    f"CareDERM has the highest refund rate at {ref_rates[2]:.1%} — <strong>'No results'</strong> accounts for 44% of refunds. "
    f"Recommend: add a 30-day outcome check-in at week 6 (before the refund window closes). "
    f"Reducing CareDERM refunds to 2% recovers <strong>${(ref_rates[2] - 0.02) * derm_patients * arpu_derm / 1e3:.1f}K/month</strong>. "
    f"ACH migration for recurring billing would recover ~${(total_refund_fee * 0.8)/1e3:.1f}K/month in non-refundable card fees.",
    level="warning",
)
