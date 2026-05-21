"""
CareValidate Employer ROI Calculator
B2B sales tool — shows employers their ROI from offering CareValidate programs.
Run: streamlit run app.py --server.port 8504
Sources: KFF EHBS 2024, ADA 2022, STEP/SURMOUNT/SELECT trials, Omada S-1 2024
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

st.set_page_config(page_title="CareValidate Employer ROI", layout="wide", page_icon="🏢")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
sidebar_nav("roi")

render_header(
    "Employer ROI Calculator",
    "Show employers the financial case for offering CareValidate health programs to their workforce",
    badge="B2B Sales Tool",
    badge_color="purple",
)

alert(
    "<strong>Disclaimer:</strong> All projections use published clinical benchmarks (KFF EHBS 2024, ADA Economic Costs 2022, "
    "NEJM STEP/SURMOUNT trials, Omada S-1 2024). Actual results depend on enrollment, employee health status, "
    "drug adherence, and plan design. This tool is for planning and sales conversations — not a guarantee of outcomes. "
    "No PHI collected. All data stays local.",
    level="warning",
)

INDUSTRY_COSTS = {
    "Technology":            {"hc_cost": 7600,  "obesity_rate": 0.34, "t2d_rate": 0.09},
    "Finance / Insurance":   {"hc_cost": 7800,  "obesity_rate": 0.33, "t2d_rate": 0.10},
    "Healthcare":            {"hc_cost": 7300,  "obesity_rate": 0.38, "t2d_rate": 0.12},
    "Manufacturing":         {"hc_cost": 8100,  "obesity_rate": 0.42, "t2d_rate": 0.13},
    "Retail / Hospitality":  {"hc_cost": 6900,  "obesity_rate": 0.44, "t2d_rate": 0.14},
    "Construction":          {"hc_cost": 7900,  "obesity_rate": 0.40, "t2d_rate": 0.12},
    "Government / Education":{"hc_cost": 8400,  "obesity_rate": 0.36, "t2d_rate": 0.11},
    "Professional Services": {"hc_cost": 7500,  "obesity_rate": 0.32, "t2d_rate": 0.09},
    "Custom":                {"hc_cost": 7800,  "obesity_rate": 0.38, "t2d_rate": 0.11},
}

PROGRAMS = {
    "CareGLP (GLP-1 Weight Management)": {
        "arpu": 950, "cogs_pct": 0.42,
        "weight_loss_6mo": 0.10, "weight_loss_12mo": 0.15,
        "claims_reduction_12mo": 0.17, "adherence_12mo": 0.55,
        "cv_risk_reduction": 0.08, "t2d_reduction": 0.32,
    },
    "CareGLP + CareHRT Bundle": {
        "arpu": 1089, "cogs_pct": 0.43,
        "weight_loss_6mo": 0.11, "weight_loss_12mo": 0.16,
        "claims_reduction_12mo": 0.19, "adherence_12mo": 0.58,
        "cv_risk_reduction": 0.10, "t2d_reduction": 0.34,
    },
    "CareHRT (Hormone Therapy)": {
        "arpu": 189, "cogs_pct": 0.38,
        "weight_loss_6mo": 0.03, "weight_loss_12mo": 0.05,
        "claims_reduction_12mo": 0.09, "adherence_12mo": 0.70,
        "cv_risk_reduction": 0.05, "t2d_reduction": 0.08,
    },
    "AccommoCare (Chronic Condition Management)": {
        "arpu": 48, "cogs_pct": 0.45,
        "weight_loss_6mo": 0.02, "weight_loss_12mo": 0.03,
        "claims_reduction_12mo": 0.12, "adherence_12mo": 0.82,
        "cv_risk_reduction": 0.06, "t2d_reduction": 0.15,
    },
}

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Employer Profile")
    company      = st.text_input("Company Name", "Acme Corp")
    industry     = st.selectbox("Industry", list(INDUSTRY_COSTS.keys()))
    employees    = st.number_input("Total Employees", 50, 100000, 1200, 50)
    avg_salary   = st.number_input("Average Annual Salary ($)", 30000, 300000, 72000, 1000)
    pct_insured  = st.slider("% Employees on Company Health Plan", 40, 100, 78)

    st.subheader("Program Selection")
    program_name = st.selectbox("CareValidate Program", list(PROGRAMS.keys()))
    prog         = PROGRAMS[program_name]

    st.subheader("Enrollment Assumptions")
    eligibility_override = st.checkbox("Override eligibility estimate", False)
    if eligibility_override:
        eligible_pct = st.slider("% Workforce Eligible", 1, 50, 20) / 100
    else:
        eligible_pct = 0.20  # base case from research
    enrollment_rate = st.slider("Expected Enrollment Rate (%)", 5, 60, 22) / 100

    st.subheader("Contract Model")
    contract_model = st.selectbox("Contract Structure",
        ["PMPM (Per Member Per Month)", "Per-Engaged-Member", "Hybrid Platform + Per-Patient"])
    if contract_model == "PMPM (Per Member Per Month)":
        pmpm_rate = st.slider("PMPM Rate ($)", 5, 30, 12)
    elif contract_model == "Per-Engaged-Member":
        pmpm_rate = st.slider("Per-Engaged-Member Rate ($/mo)", 20, 80, 45)
    else:
        platform_fee_annual = st.number_input("Annual Platform Fee ($)", 10000, 500000, 85000, 5000)
        per_patient_fee     = st.number_input("Per-Patient Fee ($/mo)", 50, 400, 180, 10)
        pmpm_rate           = 0

    st.subheader("Projection Period")
    years = st.slider("Years to Project", 1, 5, 3)

# ── Calculations ─────────────────────────────────────────────────────────────
ind            = INDUSTRY_COSTS[industry]
insured_pop    = int(employees * pct_insured / 100)
eligible_count = int(insured_pop * eligible_pct)
enrolled_count = int(eligible_count * enrollment_rate)

# Cost baselines
base_hc_cost   = ind["hc_cost"]
obesity_excess = 4000    # $ per obese employee/yr (JOEM + CDC)
t2d_excess     = 6800    # $ excess per T2D employee/yr (ADA 2022)
productivity_loss = 1750 # $ per obese employee/yr (Gallup-Healthways)
obese_employees   = int(insured_pop * ind["obesity_rate"])
t2d_employees     = int(insured_pop * ind["t2d_rate"])
current_excess_cost = (obese_employees * (obesity_excess + productivity_loss) +
                       t2d_employees   * t2d_excess)

# Program cost to employer
if contract_model == "PMPM (Per Member Per Month)":
    annual_program_cost = insured_pop * pmpm_rate * 12
elif contract_model == "Per-Engaged-Member":
    annual_program_cost = enrolled_count * pmpm_rate * 12
else:
    annual_program_cost = platform_fee_annual + enrolled_count * per_patient_fee * 12

# Savings from enrolled patients
enrolled_obese = int(enrolled_count * ind["obesity_rate"])
enrolled_t2d   = int(enrolled_count * ind["t2d_rate"])
adhered_12mo   = int(enrolled_count * prog["adherence_12mo"])

claims_savings_yr1  = (enrolled_count * base_hc_cost * prog["claims_reduction_12mo"] *
                       prog["adherence_12mo"])
obesity_savings     = enrolled_obese * (obesity_excess + productivity_loss) * prog["weight_loss_12mo"] / 0.15
t2d_savings         = enrolled_t2d * t2d_excess * prog["t2d_reduction"]
total_savings_yr1   = claims_savings_yr1 + obesity_savings + t2d_savings
net_roi_yr1         = total_savings_yr1 - annual_program_cost
roi_pct_yr1         = (net_roi_yr1 / annual_program_cost * 100) if annual_program_cost > 0 else 0
payback_months      = (annual_program_cost / total_savings_yr1 * 12) if total_savings_yr1 > 0 else 999

# Multi-year projection (compounding adherence improvements)
yearly_data = []
cumulative_savings = 0
cumulative_cost    = 0
for y in range(1, years + 1):
    scale       = 1 + (y - 1) * 0.08   # 8% improvement per year with coaching
    yr_savings  = total_savings_yr1 * min(scale, 1.35)
    yr_cost     = annual_program_cost * (1 + (y-1) * 0.03)  # 3% cost inflation
    yr_net      = yr_savings - yr_cost
    cumulative_savings += yr_savings
    cumulative_cost    += yr_cost
    yearly_data.append({
        "Year": f"Year {y}",
        "Enrolled Members": enrolled_count,
        "Program Cost": yr_cost,
        "Gross Savings": yr_savings,
        "Net ROI": yr_net,
        "ROI %": (yr_net / yr_cost * 100) if yr_cost > 0 else 0,
    })

df_years = pd.DataFrame(yearly_data)
total_net_3yr = cumulative_savings - cumulative_cost

# ── KPI Row ───────────────────────────────────────────────────────────────────
section(f"ROI Summary — {company}", "📊")
kpi_row([
    kpi_card(
        f"{enrolled_count:,}", "Enrolled Employees",
        f"{eligible_count:,} eligible · {enrollment_rate:.0%} enrolled",
    ),
    kpi_card(
        f"${annual_program_cost/1e3:.0f}K", "Annual Program Cost",
        f"${annual_program_cost/enrolled_count:.0f}/enrolled/yr" if enrolled_count else "—",
    ),
    kpi_card(
        f"${total_savings_yr1/1e3:.0f}K", "Year 1 Gross Savings",
        "Claims + productivity + T2D",
        color="green" if total_savings_yr1 > annual_program_cost else "yellow",
    ),
    kpi_card(
        f"{roi_pct_yr1:.0f}%", "Year 1 ROI",
        f"${net_roi_yr1/1e3:.0f}K net",
        color="green" if roi_pct_yr1 >= 150 else "yellow" if roi_pct_yr1 >= 50 else "red",
    ),
    kpi_card(
        f"{payback_months:.1f} mo", "Payback Period",
        "Time to break even",
        color="green" if payback_months <= 18 else "yellow" if payback_months <= 30 else "red",
    ),
])

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.subheader("Cost vs. Savings by Year")
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Program Cost", x=df_years["Year"],
                         y=df_years["Program Cost"]/1e3,
                         marker_color=RED))
    fig.add_trace(go.Bar(name="Gross Savings", x=df_years["Year"],
                         y=df_years["Gross Savings"]/1e3,
                         marker_color=GREEN))
    fig.add_trace(go.Scatter(name="Net ROI", x=df_years["Year"],
                             y=df_years["Net ROI"]/1e3, mode="lines+markers",
                             line=dict(color=BLUE, width=2.5),
                             marker=dict(size=8)))
    fig.update_layout(template="plotly_dark", paper_bgcolor=BG,
                      plot_bgcolor=CARD, barmode="group",
                      yaxis_title="$K", height=300,
                      margin=dict(l=0,r=0,t=10,b=0),
                      xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                      yaxis=dict(gridcolor="rgba(255,255,255,0.04)"))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Where Savings Come From (Year 1)")
    labels  = ["Claims Reduction", "Obesity / Productivity", "Diabetes Management"]
    values  = [claims_savings_yr1, obesity_savings, t2d_savings]
    colors  = [BLUE, GREEN, PURPLE]
    fig2 = go.Figure(go.Pie(labels=labels, values=values, hole=0.55,
                            marker=dict(colors=colors), textinfo="label+percent",
                            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<extra></extra>"))
    fig2.update_layout(template="plotly_dark", paper_bgcolor=BG, height=300,
                       margin=dict(l=0,r=0,t=10,b=0),
                       annotations=[dict(text=f"${total_savings_yr1/1e3:.0f}K",
                                        font_size=16, showarrow=False)])
    st.plotly_chart(fig2, use_container_width=True)

# ── Sensitivity ───────────────────────────────────────────────────────────────
section("ROI Sensitivity — Enrollment Rate vs. Adherence", "🔬")
enroll_range = np.arange(0.05, 0.55, 0.05)
adhere_range = np.arange(0.30, 0.85, 0.05)
z = np.zeros((len(adhere_range), len(enroll_range)))
for i, adh in enumerate(adhere_range):
    for j, enr in enumerate(enroll_range):
        enrolled_s  = int(eligible_count * enr)
        savings_s   = (enrolled_s * base_hc_cost * prog["claims_reduction_12mo"] * adh +
                       int(enrolled_s * ind["obesity_rate"]) * (obesity_excess + productivity_loss) *
                       prog["weight_loss_12mo"] / 0.15 +
                       int(enrolled_s * ind["t2d_rate"]) * t2d_excess * prog["t2d_reduction"])
        cost_s = (insured_pop * pmpm_rate * 12 if contract_model == "PMPM (Per Member Per Month)"
                  else enrolled_s * pmpm_rate * 12 if contract_model == "Per-Engaged-Member"
                  else platform_fee_annual + enrolled_s * per_patient_fee * 12
                  if 'platform_fee_annual' in dir() else annual_program_cost)
        z[i, j] = (savings_s - cost_s) / cost_s * 100 if cost_s > 0 else 0

fig3 = go.Figure(go.Heatmap(
    z=z, x=[f"{e:.0%}" for e in enroll_range], y=[f"{a:.0%}" for a in adhere_range],
    colorscale=[[0, RED],[0.25, YELLOW],[0.5, GREEN],[1.0, BLUE]],
    colorbar=dict(title="ROI %"),
    hovertemplate="Enrollment %{x}<br>Adherence %{y}<br>ROI: %{z:.0f}%<extra></extra>",
    text=np.round(z).astype(int), texttemplate="%{text}%",
))
fig3.add_shape(type="rect",
    x0=f"{enrollment_rate:.0%}", x1=f"{enrollment_rate:.0%}",
    y0=f"{prog['adherence_12mo']:.0%}", y1=f"{prog['adherence_12mo']:.0%}",
    line=dict(color="white", width=3))
fig3.update_layout(
    template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
    xaxis_title="Enrollment Rate", yaxis_title="12-Month Adherence",
    height=320, margin=dict(l=0,r=0,t=10,b=0),
)
st.plotly_chart(fig3, use_container_width=True)

# ── Clinical outcomes ─────────────────────────────────────────────────────────
section("Expected Clinical Outcomes — Enrolled Employees", "🩺")
kpi_row([
    kpi_card(f"{prog['weight_loss_12mo']:.0%}", "Avg Weight Loss (12mo)",
             "Source: STEP-1 / SURMOUNT-1 trials", color="green"),
    kpi_card(f"{adhered_12mo:,}", "Members Still Active at 12mo",
             f"{prog['adherence_12mo']:.0%} adherence with coaching", color="green"),
    kpi_card(f"{prog['cv_risk_reduction']:.0%}", "CV Risk Reduction",
             "Source: SELECT trial (NEJM 2023)", color="green"),
    kpi_card(f"{enrolled_t2d * prog['t2d_reduction']:.0f}", "T2D Patients Improved A1C",
             f"{prog['t2d_reduction']:.0%} of enrolled T2D members", color="green"),
])

# ── Multi-year summary table ───────────────────────────────────────────────────
section(f"{years}-Year Financial Summary", "📋")
display_df = df_years.copy()
for col in ["Program Cost","Gross Savings","Net ROI"]:
    display_df[col] = display_df[col].apply(lambda x: f"${x/1e3:.0f}K")
display_df["ROI %"] = display_df["ROI %"].apply(lambda x: f"{x:.0f}%")
st.dataframe(display_df.set_index("Year"), use_container_width=True)

alert(
    f"<strong>{years}-Year Cumulative Net ROI: ${total_net_3yr/1e3:.0f}K</strong> "
    f"(${cumulative_savings/1e3:.0f}K savings − ${cumulative_cost/1e3:.0f}K cost)",
    level="success",
)

# ── Export section ────────────────────────────────────────────────────────────
st.divider()
section("Export for Sales Conversation", "📤")
st.text_area("Copy this summary into your proposal:",
f"""CareValidate ROI Analysis — {company}
Program: {program_name}
Employees Analyzed: {employees:,} ({insured_pop:,} insured)
Eligible for Program: {eligible_count:,} ({eligible_pct:.0%} of insured)
Expected Enrollment: {enrolled_count:,} ({enrollment_rate:.0%} of eligible)

YEAR 1 FINANCIALS
  Program Cost:      ${annual_program_cost:,.0f}
  Gross Savings:     ${total_savings_yr1:,.0f}
  Net ROI:           ${net_roi_yr1:,.0f} ({roi_pct_yr1:.0f}%)
  Payback Period:    {payback_months:.1f} months

{years}-YEAR CUMULATIVE
  Total Cost:        ${cumulative_cost:,.0f}
  Total Savings:     ${cumulative_savings:,.0f}
  Net ROI:           ${total_net_3yr:,.0f}

CLINICAL OUTCOMES (enrolled members)
  Expected weight loss at 12 mo:  {prog['weight_loss_12mo']:.0%}
  12-month adherence rate:         {prog['adherence_12mo']:.0%}
  CV risk reduction:               {prog['cv_risk_reduction']:.0%}

Sources: KFF EHBS 2024 · ADA Economic Costs 2022 · NEJM STEP/SURMOUNT/SELECT trials · Omada S-1 2024
Disclaimer: Projections based on published benchmarks. Actual results vary.
""", height=280)

# ── Outcomes-Based Pricing Model ─────────────────────────────────────────────
section("Outcomes-Based Pricing Model", "📐")
st.caption("Compare flat PMPM vs shared-savings contract structure — model CareValidate's revenue upside under each.")

pricing_mode = st.radio(
    "Contract structure",
    ["Flat PMPM", "Shared Savings (30% of documented claims reduction)"],
    horizontal=True,
)

ob_col1, ob_col2 = st.columns(2, gap="large")
with ob_col1:
    ob_lives      = st.number_input("Employer member lives", value=10000, step=500)
    ob_pmpm       = st.number_input("Flat PMPM rate ($)", value=12, step=1)
    eligible_pct  = st.slider("% eligible for GLP-1/metabolic programs", 5, 25, 8)
    savings_share = st.slider("CareValidate share of savings (%)", 15, 40, 30)
    # ADA 2022: $2,800/member/yr average claims savings for GLP-1 programs
    claims_saving_per_member = st.number_input(
        "Documented claims savings per enrolled member ($/yr)", value=2800, step=100,
        help="ADA 2022: $2,800/member/yr average for GLP-1 programs"
    )

with ob_col2:
    enrolled_members = int(ob_lives * eligible_pct / 100)
    flat_annual_rev  = ob_lives * ob_pmpm * 12
    total_savings    = enrolled_members * claims_saving_per_member
    shared_rev       = total_savings * savings_share / 100

    if pricing_mode == "Flat PMPM":
        cv_annual_rev = flat_annual_rev
        label         = "Flat PMPM Revenue"
        color         = "blue"
    else:
        cv_annual_rev = shared_rev
        label         = "Shared Savings Revenue"
        color         = "green"

    upside_multiple = shared_rev / max(flat_annual_rev, 1)

    kpi_row([
        kpi_card(f"${flat_annual_rev/1e3:.0f}K", "Flat PMPM Annual Revenue",
                 f"${ob_pmpm}/mo × {ob_lives:,} lives", color="blue"),
        kpi_card(f"${shared_rev/1e3:.0f}K", "Shared Savings Revenue",
                 f"{savings_share}% of ${total_savings/1e3:.0f}K employer savings",
                 color="green"),
        kpi_card(f"{upside_multiple:.1f}x", "Shared Savings Upside",
                 "vs flat PMPM on performing cohort",
                 color="green" if upside_multiple > 1 else "yellow"),
        kpi_card(f"{enrolled_members:,}", "Enrolled Members",
                 f"{eligible_pct}% of {ob_lives:,} lives", color="purple"),
    ])

    fig_price = go.Figure(go.Bar(
        x=["Flat PMPM", "Shared Savings (30%)", "Shared Savings (40%)"],
        y=[flat_annual_rev/1e3,
           total_savings*0.30/1e3,
           total_savings*0.40/1e3],
        marker_color=[BLUE, GREEN, PURPLE],
        text=[f"${v/1e3:.0f}K" for v in [flat_annual_rev,
              total_savings*0.30, total_savings*0.40]],
        textposition="outside",
        textfont=dict(size=12, color="#f1f5f9"),
    ))
    fig_price.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        height=260, margin=dict(l=0, r=0, t=10, b=0),
        yaxis=dict(title="Annual Revenue ($K)", gridcolor="rgba(255,255,255,0.04)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    )
    st.plotly_chart(fig_price, use_container_width=True)

alert(
    f"For a <strong>{ob_lives:,}-life employer</strong>, flat PMPM generates "
    f"<strong>${flat_annual_rev/1e3:.0f}K/year</strong>. "
    f"A shared-savings contract at {savings_share}% of documented claims reduction generates "
    f"<strong>${shared_rev/1e3:.0f}K/year</strong> — a "
    f"<strong>{upside_multiple:.1f}x uplift</strong> on performing cohorts. "
    f"Risk: CareValidate bears outcome risk. Mitigation: include a PMPM floor (e.g., $4/mo) "
    f"and cap the measurement period at 12 months. "
    f"Source: ADA 2022 — GLP-1 programs average $2,800/member/yr in documented claims savings.",
    level="info",
)
