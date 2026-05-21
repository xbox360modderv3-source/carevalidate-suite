"""
CareValidate GLP-1 Scenario Model
Analyzes revenue impact of FDA compounded semaglutide ban across four scenarios.
Run: streamlit run app.py --server.port 8502
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from carevalidate_shared.theme import (
    GLOBAL_CSS, render_header, kpi_card, kpi_row, section, alert, sidebar_nav,
    BG, CARD, BLUE, GREEN, YELLOW, RED, PURPLE, MUTED,
)
from carevalidate_shared.auth import check_auth, logout_button

def _hex_to_rgba(hex_color: str, alpha: float = 0.06) -> str | None:
    try:
        h = hex_color.lstrip("#")
        if len(h) != 6:
            return None
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    except Exception:
        return None

st.set_page_config(page_title="CareValidate GLP-1 Scenario Model", layout="wide", page_icon="💊")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
check_auth()
sidebar_nav("glp1")
logout_button()

render_header(
    "GLP-1 Revenue Scenario Model",
    "Impact analysis of FDA compounded semaglutide ban · Feb 2025 pivot · Built for CFO planning",
    badge="CFO Planning",
    badge_color="blue",
)

# ── Sidebar assumptions ─────────────────────────────────────────────────────
with st.sidebar:
    st.header("Model Assumptions")
    st.subheader("Patient Base")
    current_glp1_patients = st.number_input("Current GLP-1 Patients", 100, 50000, 3200, 100)
    monthly_new_patients   = st.number_input("New Patients/Month (pre-ban run rate)", 50, 5000, 280, 10)
    employer_members       = st.number_input("HealthJoy Employer Members", 0, 2000000, 1000000, 10000)
    employer_glp1_pct      = st.slider("% Employer Members Eligible for GLP-1", 1, 30, 8)

    st.subheader("Pricing")
    branded_price    = st.slider("Branded GLP-1 ARPU ($/mo)", 400, 1500, 950)
    compounded_price = st.slider("Compounded ARPU ($/mo) [pre-ban]", 150, 450, 297)
    alt_peptide_price= st.slider("Alt Peptide Program ARPU ($/mo)", 100, 400, 220)
    generic_price    = st.slider("Generic GLP-1 ARPU ($/mo) [2027+]", 80, 300, 140)

    st.subheader("Cost Structure")
    branded_cogs_pct  = st.slider("Branded COGS % Revenue", 20, 70, 42)
    compound_cogs_pct = st.slider("Compounded COGS % Revenue", 30, 70, 55)
    alt_cogs_pct      = st.slider("Alt Peptide COGS % Revenue", 25, 65, 48)
    generic_cogs_pct  = st.slider("Generic COGS % Revenue [2027+]", 15, 50, 28)
    fixed_monthly     = st.number_input("Fixed Costs/Month ($)", 0, 500000, 85000, 5000)

    st.subheader("Churn & Retention")
    branded_churn  = st.slider("Monthly Churn — Branded (%)", 1, 20, 8)
    alt_churn      = st.slider("Monthly Churn — Alt Peptides (%)", 1, 25, 12)
    price_dropout  = st.slider("% Patients Lost to Price Shock (branded)", 0, 80, 45)

    st.subheader("Timeline")
    months = st.slider("Projection Months", 6, 36, 24)
    generic_launch_month = st.slider("Generic GLP-1 Entry (Month #)", 12, 36, 24)

# ── Scenario definitions ─────────────────────────────────────────────────────
SCENARIOS = {
    "S1: Compounded (Pre-Ban Baseline)": {
        "color": GREEN, "desc": "Jan 2025 baseline — compounded available at $297/mo",
        "price": compounded_price, "cogs_pct": compound_cogs_pct/100,
        "churn": 3/100, "retention_new": 1.0, "dropout": 0.0,
    },
    "S2: Branded Only (Current State)": {
        "color": RED, "desc": "FDA ban in effect — only branded at $950/mo",
        "price": branded_price, "cogs_pct": branded_cogs_pct/100,
        "churn": branded_churn/100, "retention_new": 1 - price_dropout/100, "dropout": price_dropout/100,
    },
    "S3: Alt Peptide Pivot": {
        "color": BLUE, "desc": "Pivot to CIC peptide programs — $220/mo, lower margin",
        "price": alt_peptide_price, "cogs_pct": alt_cogs_pct/100,
        "churn": alt_churn/100, "retention_new": 0.75, "dropout": 0.15,
    },
    "S4: Generic Entry (2027)": {
        "color": PURPLE, "desc": f"Generic GLP-1 available at month {generic_launch_month} — $140/mo, high volume",
        "price": generic_price, "cogs_pct": generic_cogs_pct/100,
        "churn": 4/100, "retention_new": 1.2, "dropout": 0.0,
    },
}

# ── Model computation ────────────────────────────────────────────────────────
@st.cache_data
def run_scenario(name, cfg, n_months, start_patients, new_pm, gen_month, gen_price, gen_cogs):
    rows = []
    patients = start_patients * (1 - cfg["dropout"])
    for m in range(1, n_months + 1):
        # Generic switch at launch month for S4
        if "Generic" in name and m >= gen_month:
            price    = gen_price
            cogs_pct = gen_cogs / 100
            churn    = 4 / 100
            new_mult = 1.3
        else:
            price    = cfg["price"]
            cogs_pct = cfg["cogs_pct"]
            churn    = cfg["churn"]
            new_mult = cfg["retention_new"]

        revenue     = patients * price
        cogs        = revenue * cogs_pct
        gross_profit= revenue - cogs
        new_pts     = new_pm * new_mult
        patients    = max(0, patients * (1 - churn) + new_pts)
        rows.append({
            "Month": m, "Patients": round(patients),
            "Revenue": revenue, "COGS": cogs,
            "Gross_Profit": gross_profit,
            "Gross_Margin": gross_profit / revenue if revenue > 0 else 0,
        })
    return pd.DataFrame(rows)

dfs = {}
for name, cfg in SCENARIOS.items():
    dfs[name] = run_scenario(
        name, cfg, months, current_glp1_patients, monthly_new_patients,
        generic_launch_month, generic_price, generic_cogs_pct
    )

# ── KPI summary ──────────────────────────────────────────────────────────────
section("12-Month Revenue Summary by Scenario", "💰")
baseline_12 = dfs["S1: Compounded (Pre-Ban Baseline)"][dfs["S1: Compounded (Pre-Ban Baseline)"].Month <= 12]["Revenue"].sum()

cards = []
for name, df in dfs.items():
    cfg   = SCENARIOS[name]
    rev12 = df[df.Month <= 12]["Revenue"].sum()
    gp12  = df[df.Month <= 12]["Gross_Profit"].sum()
    gm12  = gp12 / rev12 if rev12 > 0 else 0
    pts   = int(df[df.Month == min(12, months)]["Patients"].values[0])
    delta = rev12 - baseline_12
    short = name.split(":")[0]
    trend_txt = f"${abs(delta)/1e6:.2f}M vs baseline"
    trend_good = delta >= 0

    # pick color by scenario order
    color_map = {
        "S1": "green", "S2": "red", "S3": "blue", "S4": "purple",
    }
    card_color = color_map.get(short, "default")

    cards.append(kpi_card(
        value=f"${rev12/1e6:.2f}M",
        label=f"{short} — 12-mo Revenue",
        sublabel=f"GM {gm12:.0%}  ·  {pts:,} patients",
        trend=trend_txt,
        trend_good=trend_good,
        color=card_color,
    ))

kpi_row(cards)

st.divider()

# ── Revenue chart ────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Monthly Revenue by Scenario")
    fig = go.Figure()
    for name, df in dfs.items():
        fig.add_trace(go.Scatter(
            x=df["Month"], y=df["Revenue"]/1e3,
            name=name.split(":")[0], mode="lines",
            line=dict(color=SCENARIOS[name]["color"], width=2.5),
            hovertemplate=f"<b>{name.split(':')[0]}</b><br>Month %{{x}}<br>Revenue: $%{{y:.0f}}K<extra></extra>"
        ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        yaxis_title="Revenue ($K/mo)", xaxis_title="Month",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
        margin=dict(l=0, r=0, t=10, b=0), height=320,
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Patient Volume by Scenario")
    fig2 = go.Figure()
    for name, df in dfs.items():
        fig2.add_trace(go.Scatter(
            x=df["Month"], y=df["Patients"],
            name=name.split(":")[0], mode="lines",
            line=dict(color=SCENARIOS[name]["color"], width=2.5),
            hovertemplate=f"<b>{name.split(':')[0]}</b><br>Month %{{x}}<br>Patients: %{{y:,}}<extra></extra>"
        ))
    fig2.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        yaxis_title="Active Patients", xaxis_title="Month",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
        margin=dict(l=0, r=0, t=10, b=0), height=320,
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Margin comparison ─────────────────────────────────────────────────────────
section("Gross Margin % Over Time", "📉")
fig3 = go.Figure()
for name, df in dfs.items():
    fig3.add_trace(go.Scatter(
        x=df["Month"], y=df["Gross_Margin"]*100,
        name=name.split(":")[0], mode="lines",
        line=dict(color=SCENARIOS[name]["color"], width=2),
        fill="tozeroy", fillcolor=_hex_to_rgba(SCENARIOS[name]["color"]),
    ))
fig3.add_hline(y=40, line_dash="dot", line_color=MUTED,
               annotation_text="40% GM Target", annotation_position="right",
               annotation_font_color=MUTED)
fig3.update_layout(
    template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
    yaxis_title="Gross Margin %", xaxis_title="Month",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
    margin=dict(l=0, r=0, t=10, b=0), height=280,
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
)
st.plotly_chart(fig3, use_container_width=True)

# ── Revenue loss table ─────────────────────────────────────────────────────────
section("Revenue Impact vs Pre-Ban Baseline", "📋")
baseline_rev = dfs["S1: Compounded (Pre-Ban Baseline)"]["Revenue"].sum()
summary_rows = []
for name, df in dfs.items():
    total_rev  = df["Revenue"].sum()
    total_gp   = df["Gross_Profit"].sum()
    avg_gm     = total_gp / total_rev if total_rev > 0 else 0
    delta      = total_rev - baseline_rev
    final_pts  = int(df.iloc[-1]["Patients"])
    summary_rows.append({
        "Scenario": name,
        "Total Revenue": f"${total_rev/1e6:.2f}M",
        "Total Gross Profit": f"${total_gp/1e6:.2f}M",
        "Avg Gross Margin": f"{avg_gm:.1%}",
        "vs Baseline": f"{'▲' if delta >= 0 else '▼'} ${abs(delta)/1e6:.2f}M",
        "Final Patient Count": f"{final_pts:,}",
    })
st.dataframe(pd.DataFrame(summary_rows).set_index("Scenario"), use_container_width=True)

# ── Employer partnership section ──────────────────────────────────────────────
st.divider()
section("HealthJoy Employer Partnership — GLP-1 Opportunity", "🏢")
eligible_members = int(employer_members * employer_glp1_pct / 100)
conversion_rates = [0.5, 1.0, 2.0, 3.0, 5.0]

hj_rows = []
for cr in conversion_rates:
    enrolled = int(eligible_members * cr / 100)
    for sname, scfg in [("Branded", {"p": branded_price, "gm": 1 - branded_cogs_pct/100}),
                         ("Alt Peptide", {"p": alt_peptide_price, "gm": 1 - alt_cogs_pct/100})]:
        monthly_rev = enrolled * scfg["p"]
        annual_rev  = monthly_rev * 12
        annual_gp   = annual_rev * scfg["gm"]
        hj_rows.append({
            "Conversion Rate": f"{cr}%",
            "Program": sname,
            "Enrolled Members": f"{enrolled:,}",
            "Monthly Revenue": f"${monthly_rev/1e3:.0f}K",
            "Annual Revenue": f"${annual_rev/1e6:.2f}M",
            "Annual Gross Profit": f"${annual_gp/1e6:.2f}M",
        })

st.caption(f"Based on {employer_members:,} HealthJoy members · {eligible_members:,} eligible ({employer_glp1_pct}%) · Varies by employer benefits design")
st.dataframe(pd.DataFrame(hj_rows), use_container_width=True, hide_index=True)

# ── CFO Insight ───────────────────────────────────────────────────────────────
st.divider()
section("CFO Takeaways", "🎯")
s2_12m = dfs["S2: Branded Only (Current State)"][dfs["S2: Branded Only (Current State)"].Month <= 12]["Revenue"].sum()
s1_12m = dfs["S1: Compounded (Pre-Ban Baseline)"][dfs["S1: Compounded (Pre-Ban Baseline)"].Month <= 12]["Revenue"].sum()
s3_12m = dfs["S3: Alt Peptide Pivot"][dfs["S3: Alt Peptide Pivot"].Month <= 12]["Revenue"].sum()
revenue_gap = s1_12m - s2_12m

branded_gm  = (1 - branded_cogs_pct/100)
compound_gm = (1 - compound_cogs_pct/100)

kpi_row([
    kpi_card(
        f"${revenue_gap/1e6:.2f}M",
        "Revenue Gap (Branded vs Baseline)",
        f"{(s2_12m-s1_12m)/s1_12m:.1%} vs pre-ban",
        trend=f"{(s2_12m-s1_12m)/s1_12m:.1%}",
        trend_good=False,
        color="red",
    ),
    kpi_card(
        f"${(s3_12m-s2_12m)/1e6:.2f}M",
        "Alt Peptide Closes Gap By",
        f"{(s3_12m-s2_12m)/revenue_gap:.0%} of gap recovered" if revenue_gap > 0 else "N/A",
        color="blue",
    ),
    kpi_card(
        f"{branded_gm:.0%} vs {compound_gm:.0%}",
        "Gross Margin Shift",
        f"{(branded_gm-compound_gm)*100:+.0f} ppt vs compounded",
        color="green",
    ),
])

alert(
    f"<strong>Key finding:</strong> The FDA ban reduced patient volume by an estimated {price_dropout:.0f}% due to price shock "
    f"(${compounded_price}/mo → ${branded_price}/mo). However, remaining patients generate "
    f"{branded_gm/compound_gm:.1f}x higher gross margin per patient. "
    f"An alt-peptide pivot at ${alt_peptide_price}/mo retains more volume but compresses margins. "
    f"The HealthJoy channel ({employer_members:,} members) represents a significant acquisition opportunity "
    f"regardless of which pricing path is chosen.",
    level="info",
)
