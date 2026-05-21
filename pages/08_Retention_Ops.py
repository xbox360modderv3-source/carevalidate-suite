"""
CareValidate Patient Retention Operations Dashboard
Refill gap early-warning, cohort survival curves, engagement scoring, employer outcomes report.
Run: streamlit run app.py --server.port 8508
Sources: IQVIA GLP-1 Adherence 2023, Omada S-1 2024, Calibrate 2023, KFF EHBS 2024
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")
from carevalidate_shared.theme import (
    GLOBAL_CSS, render_header, kpi_card, kpi_row, section, alert, sidebar_nav,
    BG, CARD, BLUE, GREEN, YELLOW, RED, PURPLE, TEAL, MUTED,
)

st.set_page_config(page_title="CareValidate Retention Ops", layout="wide", page_icon="🔄")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
sidebar_nav("retain")

render_header(
    "Patient Retention Operations",
    "Refill gap alerts · Cohort survival · Engagement scores · Employer outcomes",
    badge="Retention",
    badge_color="teal",
)

alert(
    "<strong>Disclaimer:</strong> Synthetic patient data modeled on IQVIA GLP-1 Adherence 2023, "
    "Omada S-1 2024, and Calibrate 2023 outcomes. No real PHI. In production, "
    "this dashboard connects to the EHR/pharmacy feed and updates in real time.",
    level="warning",
)

# ── Generate synthetic patient cohort ────────────────────────────────────────
@st.cache_data
def generate_patients(n=850, seed=42):
    rng = np.random.default_rng(seed)
    products  = rng.choice(["CareGLP","CareHRT","CareDERM","AccommoCare"],
                           n, p=[0.52, 0.25, 0.15, 0.08])
    channels  = rng.choice(["Employer","DTC Organic","Paid Digital","Direct"],
                           n, p=[0.42, 0.28, 0.20, 0.10])
    employers = rng.choice(
        ["HealthJoy Enterprise","AccommoCare A","AccommoCare B","AccommoCare C","Self-Pay"],
        n, p=[0.35, 0.15, 0.12, 0.10, 0.28]
    )
    months_enrolled = rng.integers(1, 25, n)
    arpu = np.where(products=="CareGLP", rng.integers(280,420,n),
           np.where(products=="CareHRT", rng.integers(120,200,n),
           np.where(products=="CareDERM", rng.integers(90,160,n), 8)))
    days_since_refill  = rng.integers(0, 45, n)
    payment_failures   = rng.choice([0,1,2,3], n, p=[0.70,0.18,0.08,0.04])
    app_logins_30d     = rng.integers(0, 25, n)
    coaching_sessions  = rng.integers(0, 8, n)
    weight_loss_pct    = rng.normal(6, 4, n).clip(0, 20).round(1)
    outcome_plateau    = ((weight_loss_pct < 2) & (months_enrolled > 3)).astype(int)
    insurance_change   = rng.random(n) < 0.06

    # Engagement score (0-100): composite of behavioral signals
    eng_score = (
        np.clip(app_logins_30d / 20, 0, 1) * 30 +
        np.clip(coaching_sessions / 6, 0, 1) * 25 +
        np.where(days_since_refill < 25, 25, np.where(days_since_refill < 35, 10, 0)) +
        np.where(payment_failures == 0, 20, np.where(payment_failures == 1, 10, 0))
    ).round(0).astype(int)

    # Churn probability (simplified)
    churn_raw = (
        0.04 * days_since_refill +
        0.40 * payment_failures +
        -0.008 * app_logins_30d +
        -0.015 * coaching_sessions +
        0.20 * outcome_plateau +
        0.15 * insurance_change.astype(float)
    )
    churn_prob = 1 / (1 + np.exp(-churn_raw + 1.2))
    churn_prob = np.clip(churn_prob, 0.02, 0.97)
    risk_tier  = np.where(churn_prob >= 0.65, "High",
                 np.where(churn_prob >= 0.35, "Medium", "Low"))

    # Days until expected refill (30-day cycle assumed)
    days_to_refill = np.clip(30 - days_since_refill, 0, 30)

    df = pd.DataFrame({
        "Patient_ID":        [f"CV-{10000+i}" for i in range(n)],
        "Product":           products,
        "Channel":           channels,
        "Employer":          employers,
        "Months_Enrolled":   months_enrolled,
        "ARPU":              arpu,
        "Days_Since_Refill": days_since_refill,
        "Days_To_Refill":    days_to_refill,
        "Payment_Failures":  payment_failures,
        "App_Logins_30d":    app_logins_30d,
        "Coaching_Sessions": coaching_sessions,
        "Weight_Loss_Pct":   weight_loss_pct,
        "Outcome_Plateau":   outcome_plateau,
        "Insurance_Change":  insurance_change,
        "Engagement_Score":  eng_score,
        "Churn_Probability": churn_prob.round(3),
        "Risk_Tier":         risk_tier,
        "Revenue_at_Risk":   (arpu * churn_prob).round(0).astype(int),
    })
    return df

df = generate_patients()

# ── Summary KPIs ──────────────────────────────────────────────────────────────
section("Retention Health Summary", "🔄")
total_patients   = len(df)
high_risk_n      = (df["Risk_Tier"] == "High").sum()
refill_gap_7d    = (df["Days_To_Refill"] <= 7).sum()
avg_eng          = df["Engagement_Score"].mean()
monthly_rar      = df["Revenue_at_Risk"].sum()
avg_months       = df["Months_Enrolled"].mean()
low_eng_n        = (df["Engagement_Score"] < 30).sum()

kpi_row([
    kpi_card(f"{total_patients:,}", "Active Patients",
             f"Avg {avg_months:.1f}mo enrolled", color="blue"),
    kpi_card(f"{refill_gap_7d}", "Refill Due in 7 Days",
             "Need proactive outreach now",
             color="red" if refill_gap_7d > 30 else "yellow"),
    kpi_card(f"{avg_eng:.0f}/100", "Avg Engagement Score",
             f"{low_eng_n} patients below 30 (at risk)",
             color="green" if avg_eng > 55 else "yellow"),
    kpi_card(f"${monthly_rar/1e3:.0f}K", "Monthly Revenue at Risk",
             f"{high_risk_n} high-risk patients",
             color="red" if monthly_rar > 50000 else "yellow"),
])

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 1 · REFILL GAP EARLY-WARNING SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
section("1 · Refill Gap Early-Warning System", "⏱")
st.caption("Patients approaching the 30-day refill gap — ranked by churn risk × monthly revenue. Act within this window to prevent dropout.")

rg_col1, rg_col2 = st.columns([1, 3], gap="medium")
with rg_col1:
    alert_window = st.slider("Alert window (days to next refill)", 3, 14, 7)
    min_arpu     = st.slider("Min ARPU filter ($)", 0, 400, 0, 50)
    prod_filter  = st.multiselect("Products", ["CareGLP","CareHRT","CareDERM","AccommoCare"],
                                  default=["CareGLP","CareHRT"])

at_risk_refill = df[
    (df["Days_To_Refill"] <= alert_window) &
    (df["ARPU"] >= min_arpu) &
    (df["Product"].isin(prod_filter))
].sort_values(["Risk_Tier", "Revenue_at_Risk"], ascending=[True, False])

with rg_col2:
    rg_kpi_cols = st.columns(4)
    with rg_kpi_cols[0]:
        st.markdown(
            f'<div style="background:{CARD};border:1px solid rgba(255,255,255,0.07);'
            f'border-left:3px solid {RED};border-radius:12px;padding:16px 18px;">'
            f'<div style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;'
            f'letter-spacing:1px;margin-bottom:8px;">Patients in Window</div>'
            f'<div style="font-size:28px;font-weight:800;color:{RED};">{len(at_risk_refill)}</div>'
            f'<div style="font-size:12px;color:#64748b;margin-top:4px;">of {len(df[df.Product.isin(prod_filter)])} filtered</div>'
            f'</div>', unsafe_allow_html=True
        )
    with rg_kpi_cols[1]:
        rev_window = at_risk_refill["Revenue_at_Risk"].sum()
        st.markdown(
            f'<div style="background:{CARD};border:1px solid rgba(255,255,255,0.07);'
            f'border-left:3px solid {YELLOW};border-radius:12px;padding:16px 18px;">'
            f'<div style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;'
            f'letter-spacing:1px;margin-bottom:8px;">Revenue at Risk</div>'
            f'<div style="font-size:28px;font-weight:800;color:{YELLOW};">${rev_window/1e3:.0f}K</div>'
            f'<div style="font-size:12px;color:#64748b;margin-top:4px;">in {alert_window}-day window</div>'
            f'</div>', unsafe_allow_html=True
        )
    with rg_kpi_cols[2]:
        high_in_window = (at_risk_refill["Risk_Tier"] == "High").sum()
        st.markdown(
            f'<div style="background:{CARD};border:1px solid rgba(255,255,255,0.07);'
            f'border-left:3px solid {RED};border-radius:12px;padding:16px 18px;">'
            f'<div style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;'
            f'letter-spacing:1px;margin-bottom:8px;">High-Risk in Window</div>'
            f'<div style="font-size:28px;font-weight:800;color:{RED};">{high_in_window}</div>'
            f'<div style="font-size:12px;color:#64748b;margin-top:4px;">Immediate outreach needed</div>'
            f'</div>', unsafe_allow_html=True
        )
    with rg_kpi_cols[3]:
        intervention_cost = len(at_risk_refill) * 25
        save_rate = 0.40
        rev_saved = rev_window * save_rate
        st.markdown(
            f'<div style="background:{CARD};border:1px solid rgba(255,255,255,0.07);'
            f'border-left:3px solid {GREEN};border-radius:12px;padding:16px 18px;">'
            f'<div style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;'
            f'letter-spacing:1px;margin-bottom:8px;">Est. Recoverable</div>'
            f'<div style="font-size:28px;font-weight:800;color:{GREEN};">${rev_saved/1e3:.0f}K</div>'
            f'<div style="font-size:12px;color:#64748b;margin-top:4px;">at 40% intervention success</div>'
            f'</div>', unsafe_allow_html=True
        )

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

def color_risk_tier(val):
    if val == "High":   return "color:#ef4444;font-weight:700"
    if val == "Medium": return "color:#f59e0b;font-weight:600"
    return "color:#10b981"

def action_for_row(row):
    if row["Payment_Failures"] > 0:     return "📞 Payment recovery call"
    if row["Risk_Tier"] == "High":      return "🚨 Urgent refill outreach"
    if row["Engagement_Score"] < 30:    return "💬 Re-engagement message"
    return "📱 Automated refill reminder"

at_risk_refill["Recommended_Action"] = at_risk_refill.apply(action_for_row, axis=1)

display_rg = at_risk_refill[[
    "Patient_ID","Product","Employer","Days_To_Refill","ARPU",
    "Risk_Tier","Churn_Probability","Revenue_at_Risk","Recommended_Action"
]].head(50).copy()
display_rg["ARPU"]              = display_rg["ARPU"].apply(lambda x: f"${x:,}/mo")
display_rg["Churn_Probability"] = display_rg["Churn_Probability"].apply(lambda x: f"{x:.1%}")
display_rg["Revenue_at_Risk"]   = display_rg["Revenue_at_Risk"].apply(lambda x: f"${x:,}")
display_rg["Days_To_Refill"]    = display_rg["Days_To_Refill"].apply(lambda x: f"{x}d")

st.dataframe(
    display_rg.set_index("Patient_ID").style.map(color_risk_tier, subset=["Risk_Tier"]),
    use_container_width=True, height=320
)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 2 · COHORT RETENTION / SURVIVAL CURVES
# ══════════════════════════════════════════════════════════════════════════════
section("2 · Cohort Retention Analysis", "📉")
st.caption("Kaplan-Meier style retention curves by product and channel. Based on IQVIA GLP-1 Adherence 2023, Omada S-1 2024.")

months = np.arange(0, 25)

# Retention curves per product (calibrated to published benchmarks)
retention_curves = {
    "CareGLP (Branded)":   np.exp(-0.042 * months),
    "CareGLP (Employer)":  np.exp(-0.022 * months),
    "CareHRT":             np.exp(-0.028 * months),
    "CareDERM":            np.exp(-0.055 * months),
    "AccommoCare (B2B)":   np.exp(-0.010 * months),
}
curve_colors = [BLUE, GREEN, PURPLE, YELLOW, TEAL]

surv_col1, surv_col2 = st.columns([2, 1], gap="medium")

with surv_col1:
    fig_surv = go.Figure()
    for (name, curve), color in zip(retention_curves.items(), curve_colors):
        fig_surv.add_trace(go.Scatter(
            x=months, y=curve * 100, name=name,
            line=dict(color=color, width=2.5),
            hovertemplate=f"<b>{name}</b><br>Month %{{x}}: %{{y:.1f}}% retained<extra></extra>",
        ))
    fig_surv.add_hline(y=70, line_dash="dot", line_color="rgba(255,255,255,0.15)",
                       annotation_text="70% retention target", annotation_font_color="#475569",
                       annotation_position="bottom right")
    fig_surv.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        height=340, margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(title="Months Enrolled", gridcolor="rgba(255,255,255,0.04)", dtick=3),
        yaxis=dict(title="% Patients Retained", gridcolor="rgba(255,255,255,0.04)",
                   range=[0, 105]),
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )
    st.plotly_chart(fig_surv, use_container_width=True)

with surv_col2:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section("12-Month Retention by Product", "")
    benchmarks = [
        ("CareGLP — Employer", f"{retention_curves['CareGLP (Employer)'][12]*100:.0f}%", GREEN),
        ("CareHRT", f"{retention_curves['CareHRT'][12]*100:.0f}%", PURPLE),
        ("CareGLP — DTC", f"{retention_curves['CareGLP (Branded)'][12]*100:.0f}%", BLUE),
        ("AccommoCare (B2B)", f"{retention_curves['AccommoCare (B2B)'][12]*100:.0f}%", TEAL),
        ("CareDERM", f"{retention_curves['CareDERM'][12]*100:.0f}%", YELLOW),
        ("Industry DTC avg", "~48%", MUTED),
    ]
    for name, pct, color in benchmarks:
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:9px 12px;border-bottom:1px solid rgba(255,255,255,0.04);">'
            f'<span style="font-size:12px;color:#94a3b8;">{name}</span>'
            f'<span style="font-size:13px;font-weight:700;color:{color};">{pct}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    st.markdown(
        '<div style="font-size:11px;color:#334155;margin-top:12px;line-height:1.5;">'
        'Sources: IQVIA GLP-1 Adherence 2023<br>Omada S-1 2024 · Calibrate 2023</div>',
        unsafe_allow_html=True
    )

alert(
    f"Employer-sponsored GLP-1 patients retain at <strong>"
    f"{retention_curves['CareGLP (Employer)'][12]*100:.0f}%</strong> at 12 months vs "
    f"<strong>{retention_curves['CareGLP (Branded)'][12]*100:.0f}%</strong> DTC — a "
    f"{(retention_curves['CareGLP (Employer)'][12]/retention_curves['CareGLP (Branded)'][12]-1)*100:.0f}% "
    f"retention advantage. Every percentage point of patient mix shifted to employer channel "
    f"reduces monthly churn cost. Source: Omada Health S-1 2024.",
    level="info",
)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 3 · ENGAGEMENT SCORE DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
section("3 · Patient Engagement Score Board", "📱")
st.caption("Composite score (0–100) from app logins, coaching sessions, refill cadence, and payment history. Scores below 30 are leading churn indicators.")

eng_col1, eng_col2 = st.columns([2, 1], gap="medium")

with eng_col1:
    # Engagement distribution histogram
    fig_eng = go.Figure()
    fig_eng.add_trace(go.Histogram(
        x=df["Engagement_Score"], nbinsx=25,
        marker_color=BLUE, opacity=0.85,
        name="All patients",
    ))
    fig_eng.add_trace(go.Histogram(
        x=df[df["Risk_Tier"]=="High"]["Engagement_Score"], nbinsx=15,
        marker_color=RED, opacity=0.75,
        name="High-risk patients",
    ))
    fig_eng.add_vline(x=30, line_dash="dash", line_color=YELLOW,
                      annotation_text="Action threshold (30)",
                      annotation_font_color=YELLOW)
    fig_eng.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        barmode="overlay", height=280, margin=dict(l=0,r=0,t=10,b=0),
        xaxis=dict(title="Engagement Score", gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(title="Patients", gridcolor="rgba(255,255,255,0.04)"),
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )
    st.plotly_chart(fig_eng, use_container_width=True)

with eng_col2:
    eng_tiers = [
        ("Highly Engaged (70+)",  (df["Engagement_Score"] >= 70).sum(), GREEN),
        ("Engaged (50-69)",       ((df["Engagement_Score"] >= 50) & (df["Engagement_Score"] < 70)).sum(), BLUE),
        ("At Risk (30-49)",       ((df["Engagement_Score"] >= 30) & (df["Engagement_Score"] < 50)).sum(), YELLOW),
        ("Disengaged (<30)",      (df["Engagement_Score"] < 30).sum(), RED),
    ]
    for label, count, color in eng_tiers:
        pct = count / len(df) * 100
        st.markdown(
            f'<div style="margin-bottom:10px;">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:4px;">'
            f'<span style="font-size:12px;color:#94a3b8;">{label}</span>'
            f'<span style="font-size:12px;font-weight:700;color:{color};">{count} ({pct:.0f}%)</span>'
            f'</div>'
            f'<div style="height:6px;background:rgba(255,255,255,0.06);border-radius:4px;">'
            f'<div style="height:6px;width:{pct}%;background:{color};border-radius:4px;"></div>'
            f'</div></div>',
            unsafe_allow_html=True
        )

# Engagement by product
section("Avg Engagement Score by Product & Channel", "")
eng_by_prod = df.groupby("Product")["Engagement_Score"].mean().sort_values(ascending=True)
eng_by_chan = df.groupby("Channel")["Engagement_Score"].mean().sort_values(ascending=True)

ec1, ec2 = st.columns(2, gap="medium")
with ec1:
    fig_ep = go.Figure(go.Bar(
        x=eng_by_prod.values, y=eng_by_prod.index,
        orientation="h", marker_color=[YELLOW, PURPLE, BLUE, GREEN],
        text=[f"{v:.1f}" for v in eng_by_prod.values],
        textposition="outside", textfont=dict(color="#f1f5f9", size=12),
    ))
    fig_ep.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        height=220, margin=dict(l=0,r=40,t=10,b=0),
        xaxis=dict(title="Avg Score", gridcolor="rgba(255,255,255,0.04)", range=[0,85]),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    )
    st.plotly_chart(fig_ep, use_container_width=True)

with ec2:
    fig_ec = go.Figure(go.Bar(
        x=eng_by_chan.values, y=eng_by_chan.index,
        orientation="h", marker_color=[RED, YELLOW, BLUE, GREEN],
        text=[f"{v:.1f}" for v in eng_by_chan.values],
        textposition="outside", textfont=dict(color="#f1f5f9", size=12),
    ))
    fig_ec.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        height=220, margin=dict(l=0,r=40,t=10,b=0),
        xaxis=dict(title="Avg Score", gridcolor="rgba(255,255,255,0.04)", range=[0,85]),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    )
    st.plotly_chart(fig_ec, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 4 · EMPLOYER HEALTH OUTCOMES REPORT
# ══════════════════════════════════════════════════════════════════════════════
section("4 · Employer Quarterly Outcomes Report", "🏢")
st.caption("Auto-generate a renewal-ready employer brief. Select an employer to view their population's health outcomes and claims savings estimate.")

employer_choice = st.selectbox(
    "Select employer",
    ["HealthJoy Enterprise","AccommoCare A","AccommoCare B","AccommoCare C"]
)

emp_df = df[df["Employer"] == employer_choice].copy()
report_quarter = "Q2 2026"

if len(emp_df) == 0:
    st.warning("No patients in this employer group for the current population sample.")
else:
    enrolled      = len(emp_df)
    eligible_est  = int(enrolled / 0.08)   # assume 8% enrollment rate
    enroll_rate   = enrolled / eligible_est
    avg_wl        = emp_df["Weight_Loss_Pct"].mean()
    avg_eng_emp   = emp_df["Engagement_Score"].mean()
    high_eng_pct  = (emp_df["Engagement_Score"] >= 50).mean()
    avg_months    = emp_df["Months_Enrolled"].mean()
    # ADA 2022: $2,800/yr claims savings per enrolled GLP-1 member (prorated by weight loss)
    claims_savings_per = 2800 * (avg_wl / 7.5)   # normalize to ~7.5% expected loss
    total_claims_savings = enrolled * claims_savings_per
    # Productivity: ~$600/yr per enrolled member (NEJM SELECT trial: 20% CV risk reduction)
    productivity_savings = enrolled * 600
    total_employer_value = total_claims_savings + productivity_savings
    pmpm_paid = emp_df["ARPU"].mean()
    employer_roi = total_employer_value / max(enrolled * pmpm_paid * 12, 1)

    er1, er2 = st.columns([2, 1], gap="medium")

    with er1:
        kpi_row([
            kpi_card(f"{enrolled}", "Enrolled Members",
                     f"{enroll_rate:.0%} of ~{eligible_est:,} eligible", color="blue"),
            kpi_card(f"{avg_wl:.1f}%", "Avg Weight Loss",
                     f"{report_quarter} cohort", color="green"),
            kpi_card(f"${total_claims_savings/1e3:.0f}K", "Est. Claims Savings",
                     "Based on ADA 2022 benchmarks", color="green"),
            kpi_card(f"{employer_roi:.1f}x", "Employer ROI",
                     "Program cost vs total value", color="purple"),
        ])

        # Weight loss distribution
        fig_wl = go.Figure()
        fig_wl.add_trace(go.Histogram(
            x=emp_df["Weight_Loss_Pct"], nbinsx=15,
            marker_color=GREEN, opacity=0.85, name="Weight loss %",
        ))
        fig_wl.add_vline(x=5, line_dash="dash", line_color=YELLOW,
                         annotation_text="5% clinical threshold",
                         annotation_font_color=YELLOW)
        fig_wl.update_layout(
            template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
            height=220, margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(title="Weight Loss (%)", gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(title="Members", gridcolor="rgba(255,255,255,0.04)"),
        )
        st.plotly_chart(fig_wl, use_container_width=True)

    with er2:
        st.markdown(
            f'<div style="background:{CARD};border:1px solid rgba(255,255,255,0.07);'
            f'border-radius:14px;padding:20px 18px;margin-top:4px;">'
            f'<div style="font-size:12px;font-weight:700;color:#3b82f6;'
            f'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:14px;">'
            f'{employer_choice} · {report_quarter}</div>'
            f'<div style="font-size:11px;color:#475569;margin-bottom:14px;">Program Summary</div>',
            unsafe_allow_html=True
        )
        rows = [
            ("Enrolled members", f"{enrolled}"),
            ("Eligible population (est.)", f"~{eligible_est:,}"),
            ("Enrollment rate", f"{enroll_rate:.0%}"),
            ("Avg months enrolled", f"{avg_months:.1f} mo"),
            ("Avg weight loss", f"{avg_wl:.1f}%"),
            ("Highly engaged (50+)", f"{high_eng_pct:.0%}"),
            ("Claims savings (est.)", f"${total_claims_savings:,.0f}"),
            ("Productivity value", f"${productivity_savings:,.0f}"),
            ("Total employer value", f"${total_employer_value:,.0f}"),
            ("Program cost (est.)", f"${enrolled*pmpm_paid*12:,.0f}/yr"),
            ("Employer ROI", f"{employer_roi:.1f}x"),
        ]
        for label, val in rows:
            bold = "font-weight:700;color:#f1f5f9;" if label in ("Total employer value","Employer ROI") else ""
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:7px 0;'
                f'border-bottom:1px solid rgba(255,255,255,0.04);">'
                f'<span style="font-size:12px;color:#64748b;">{label}</span>'
                f'<span style="font-size:12px;{bold}">{val}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # Exportable text brief
    section("Shareable Employer Brief", "📄")
    brief = f"""CAREVALIDATE — {employer_choice.upper()} OUTCOMES BRIEF
{report_quarter} · Confidential

ENROLLMENT
  Active members:          {enrolled}
  Eligible population:     ~{eligible_est:,}
  Enrollment rate:         {enroll_rate:.0%}
  Avg program tenure:      {avg_months:.1f} months

CLINICAL OUTCOMES
  Average weight loss:     {avg_wl:.1f}%
  Members ≥5% weight loss: {(emp_df.Weight_Loss_Pct >= 5).sum()} ({(emp_df.Weight_Loss_Pct >= 5).mean():.0%})
  Highly engaged (≥50):    {int(high_eng_pct*enrolled)} members ({high_eng_pct:.0%})

FINANCIAL VALUE TO {employer_choice.upper()}
  Est. claims savings:     ${total_claims_savings:,.0f}
  Productivity savings:    ${productivity_savings:,.0f}
  Total estimated value:   ${total_employer_value:,.0f}
  Program cost (est.):     ${enrolled*pmpm_paid*12:,.0f}/year
  Employer ROI:            {employer_roi:.1f}x

Methodology: Claims savings modeled on ADA 2022 ($2,800/member/yr for GLP-1 programs,
prorated by weight loss outcome). Productivity savings from NEJM SELECT 2023 (20% CV
event reduction × avg productivity cost). Actual results vary; full actuarial analysis
recommended before contract renewal.

Built by Connor Savenas — CareValidate CFO Analyst Interview · May 2026
Sources: ADA 2022 · NEJM SELECT 2023 · KFF EHBS 2024
"""
    st.text_area("Copy and paste into employer renewal email or QBR deck:", brief, height=340)

alert(
    f"<strong>Renewal trigger:</strong> Employers who receive a quarterly outcomes report "
    f"with documented ROI renew at 3-4x the rate of those who don't. "
    f"This report auto-generates in seconds and requires no manual analysis — "
    f"send it 60 days before contract renewal to anchor the conversation on outcomes, not cost. "
    f"Source: Advisory Board Company 2022 employer wellness program renewal analysis.",
    level="success",
)
