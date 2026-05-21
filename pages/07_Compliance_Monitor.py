"""
CareValidate Contract Compliance Monitor
Detects billing deviations from contract terms across vendor and employer relationships.
Run: streamlit run app.py --server.port 8507
Sources: Digital health standard contract structures, OIG billing guidance, AHIP 2024
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from carevalidate_shared.theme import (
    GLOBAL_CSS, render_header, kpi_card, kpi_row, section, alert, sidebar_nav,
    BG, CARD, BLUE, GREEN, YELLOW, RED, PURPLE, MUTED,
)

st.set_page_config(page_title="CareValidate Contract Monitor", layout="wide", page_icon="🔍")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
sidebar_nav("comply")

render_header(
    "Contract Compliance Monitor",
    "Catches billing deviations before they become audit findings · Surfaces hidden leakage · Protects margins",
    badge="Compliance",
    badge_color="yellow",
)

alert(
    "<strong>Disclaimer:</strong> Uses synthetic contract and billing data modeled on typical digital health structures "
    "(AHIP 2024, OIG billing guidance, IQVIA pharmacy benchmarks). In production, this tool ingests actual "
    "contract PDFs and billing exports. No real contracts or PHI used here. Requires legal review of "
    "deviation thresholds before operational deployment.",
    level="warning",
)

# ── Generate synthetic contract + billing data ────────────────────────────────
@st.cache_data
def generate_data(seed=42):
    rng = np.random.default_rng(seed)

    # ── Employer contracts ────
    employers = [
        {"Client": "HealthJoy Enterprise Pool",   "Type": "PMPM",    "Contracted_Rate": 12.00, "Lives": 1000000, "Min_Commit": 850000},
        {"Client": "AccommoCare Client A",         "Type": "PMPM",    "Contracted_Rate": 8.50,  "Lives": 18000,   "Min_Commit": 15000},
        {"Client": "AccommoCare Client B",         "Type": "PMPM",    "Contracted_Rate": 9.20,  "Lives": 6500,    "Min_Commit": 5500},
        {"Client": "AccommoCare Client C",         "Type": "PEPM",    "Contracted_Rate": 6.75,  "Lives": 22000,   "Min_Commit": 18000},
        {"Client": "White-Label Partner A",        "Type": "Platform","Contracted_Rate": 8500,  "Lives": 0,       "Min_Commit": 0},
        {"Client": "White-Label Partner B",        "Type": "Platform","Contracted_Rate": 12000, "Lives": 0,       "Min_Commit": 0},
        {"Client": "White-Label Partner C",        "Type": "Platform","Contracted_Rate": 6800,  "Lives": 0,       "Min_Commit": 0},
    ]
    emp_df = pd.DataFrame(employers)
    # Simulate billed vs contracted — inject 3 deviations
    billed_rates = emp_df["Contracted_Rate"].copy().astype(float)
    billed_rates.iloc[1] = 7.90   # billing below contracted rate (under-billing)
    billed_rates.iloc[3] = 7.10   # billing above contracted rate
    billed_rates.iloc[5] = 11400  # billing below contracted (discount given without auth)
    emp_df["Billed_Rate"]     = billed_rates
    emp_df["Rate_Deviation"]  = emp_df["Billed_Rate"] - emp_df["Contracted_Rate"]
    emp_df["Deviation_Pct"]   = emp_df["Rate_Deviation"] / emp_df["Contracted_Rate"]
    emp_df["Monthly_Leakage"] = np.where(
        emp_df["Type"].isin(["PMPM","PEPM"]),
        emp_df["Rate_Deviation"] * emp_df["Lives"],
        emp_df["Rate_Deviation"]
    )
    emp_df["Flag"] = emp_df["Deviation_Pct"].abs().apply(
        lambda x: "🔴 High" if x > 0.08 else "🟡 Medium" if x > 0.02 else "✅ OK"
    )
    emp_df["Lives_Billed"] = (emp_df["Lives"] * rng.uniform(0.88, 1.02, len(emp_df))).astype(int)
    emp_df["Eligibility_Lag_Pct"] = rng.uniform(0.01, 0.06, len(emp_df))

    # ── Pharmacy vendor billing ────
    vendors = [
        {"Vendor": "Specialty Pharma A (GLP-1)",  "Drug": "Semaglutide", "Contract_AWP_Discount": 0.18, "Units_Monthly": 1850},
        {"Vendor": "Specialty Pharma A (GLP-1)",  "Drug": "Tirzepatide", "Contract_AWP_Discount": 0.15, "Units_Monthly": 620},
        {"Vendor": "Compounding Pharmacy B",       "Drug": "HRT Combo",   "Contract_AWP_Discount": 0.22, "Units_Monthly": 1240},
        {"Vendor": "Lab Vendor C",                 "Drug": "Lab Panel",   "Contract_AWP_Discount": 0.25, "Units_Monthly": 3100},
        {"Vendor": "Specialty Pharma D (Derm)",    "Drug": "Topical Rx",  "Contract_AWP_Discount": 0.20, "Units_Monthly": 890},
    ]
    ph_df = pd.DataFrame(vendors)
    awp = np.array([950, 1100, 189, 95, 149])  # $/unit AWP
    ph_df["AWP_Per_Unit"]   = awp
    ph_df["Contracted_Net"] = awp * (1 - ph_df["Contract_AWP_Discount"])
    actual_discount = ph_df["Contract_AWP_Discount"].copy()
    actual_discount.iloc[0] = 0.14   # vendor billing less discount than contracted
    actual_discount.iloc[3] = 0.27   # vendor billing more discount (favorable but flag)
    ph_df["Actual_Discount"]      = actual_discount
    ph_df["Actual_Net"]           = awp * (1 - actual_discount)
    ph_df["Unit_Deviation"]       = ph_df["Actual_Net"] - ph_df["Contracted_Net"]
    ph_df["Monthly_Overcharge"]   = ph_df["Unit_Deviation"] * ph_df["Units_Monthly"]
    ph_df["Flag"] = ph_df["Unit_Deviation"].apply(
        lambda x: "🔴 High" if x > 20 else "🟡 Medium" if x > 5 else "✅ OK" if abs(x) <= 5 else "🟢 Favorable"
    )

    # ── PA / billing compliance ────
    pa_issues = pd.DataFrame({
        "Issue_Type":  ["Prior Auth Not Confirmed Before Ship", "Eligibility Lag — Termed Employee Billed",
                        "Upcoding Risk — Async Visit as Sync", "Split-Bill GLP-1 as Wellness",
                        "Out-of-Network Pharmacy Carve-Out"],
        "Occurrences_Monthly": [rng.integers(3,18), rng.integers(8,35),
                                rng.integers(2,12), rng.integers(1,8), rng.integers(4,20)],
        "Avg_Dollar_Exposure": [680, 142, 95, 297, 310],
        "Regulatory_Risk":     ["High","Medium","High","High","Medium"],
        "Source":             ["OIG Telehealth Guidance", "Eligibility File Lag (AHIP 2024)",
                               "CMS 99213/99214 Definition", "FDA Compounding Guidance",
                               "Network Adequacy Standards"],
    })
    pa_issues["Monthly_Exposure"] = pa_issues["Occurrences_Monthly"] * pa_issues["Avg_Dollar_Exposure"]

    return emp_df, ph_df, pa_issues

emp_df, ph_df, pa_issues = generate_data()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_emp_leakage  = emp_df["Monthly_Leakage"].sum()
total_pharm_over   = ph_df[ph_df["Monthly_Overcharge"] > 0]["Monthly_Overcharge"].sum()
total_pa_exposure  = pa_issues["Monthly_Exposure"].sum()
total_monthly_risk = abs(total_emp_leakage) + total_pharm_over + total_pa_exposure
red_flags          = (emp_df["Flag"].str.contains("🔴").sum() +
                      ph_df["Flag"].str.contains("🔴").sum() +
                      (pa_issues["Regulatory_Risk"] == "High").sum())

section("Monthly Billing Compliance Summary", "🔍")
kpi_row([
    kpi_card(f"{red_flags}", "High-Priority Flags", "Require immediate review", color="red"),
    kpi_card(
        f"${abs(total_emp_leakage)/1e3:.0f}K", "Employer Billing Deviation",
        "Over/under vs contract",
        color="yellow" if abs(total_emp_leakage) > 1000 else "green",
    ),
    kpi_card(
        f"${total_pharm_over/1e3:.0f}K", "Pharmacy Overcharges",
        "Vendor billing above contracted AWP discount",
        color="red" if total_pharm_over > 5000 else "yellow",
    ),
    kpi_card(f"${total_pa_exposure/1e3:.0f}K", "Compliance Exposure",
             "PA / eligibility / billing risk", color="yellow"),
    kpi_card(
        f"${total_monthly_risk/1e3:.0f}K", "Total Monthly Risk",
        f"${total_monthly_risk*12/1e3:.0f}K annualized",
        color="red" if total_monthly_risk > 20000 else "yellow",
    ),
])

st.divider()

# ── Employer billing deviations ───────────────────────────────────────────────
section("1 · Employer Contract vs Actual Billing", "🏢")
st.caption("PMPM/PEPM: compares billed rate to contracted rate · Platform: compares invoice to contract")

emp_display = emp_df[[
    "Client","Type","Contracted_Rate","Billed_Rate",
    "Rate_Deviation","Deviation_Pct","Monthly_Leakage","Flag"
]].copy()
emp_display["Contracted_Rate"] = emp_display.apply(
    lambda r: f"${r['Contracted_Rate']:,.2f}/mo" if r["Type"]=="Platform" else f"${r['Contracted_Rate']:.2f}", axis=1)
emp_display["Billed_Rate"]     = emp_display.apply(
    lambda r: f"${r['Billed_Rate']:,.2f}/mo" if r["Type"]=="Platform" else f"${r['Billed_Rate']:.2f}", axis=1)
emp_display["Rate_Deviation"]  = emp_display["Rate_Deviation"].apply(lambda x: f"${x:+.2f}")
emp_display["Deviation_Pct"]   = emp_display["Deviation_Pct"].apply(lambda x: f"{x:+.1%}")
emp_display["Monthly_Leakage"] = emp_display["Monthly_Leakage"].apply(lambda x: f"${x:+,.0f}")
st.dataframe(emp_display.set_index("Client"), use_container_width=True)

# ── Pharmacy vendor deviations ────────────────────────────────────────────────
section("2 · Pharmacy Vendor — AWP Discount Compliance", "💊")
st.caption("Contracted discount vs actual billed discount · Source: Specialty pharmacy net pricing benchmarks, IQVIA 2023")
ph_display = ph_df[[
    "Vendor","Drug","Contract_AWP_Discount","Actual_Discount",
    "Contracted_Net","Actual_Net","Unit_Deviation","Monthly_Overcharge","Flag"
]].copy()
ph_display["Contract_AWP_Discount"] = ph_display["Contract_AWP_Discount"].apply(lambda x: f"{x:.0%} off AWP")
ph_display["Actual_Discount"]       = ph_display["Actual_Discount"].apply(lambda x: f"{x:.0%} off AWP")
ph_display["Contracted_Net"]        = ph_display["Contracted_Net"].apply(lambda x: f"${x:.2f}")
ph_display["Actual_Net"]            = ph_display["Actual_Net"].apply(lambda x: f"${x:.2f}")
ph_display["Unit_Deviation"]        = ph_display["Unit_Deviation"].apply(lambda x: f"${x:+.2f}/unit")
ph_display["Monthly_Overcharge"]    = ph_display["Monthly_Overcharge"].apply(lambda x: f"${x:+,.0f}")
st.dataframe(ph_display.set_index("Vendor"), use_container_width=True)

# ── Compliance issues ──────────────────────────────────────────────────────────
section("3 · Billing Compliance Issues", "⚠")
st.caption("Common digital health billing risks · Source: OIG Telehealth Guidance, FDA Compounding Rules, CMS Coding Guidelines")
pa_display = pa_issues.copy()
pa_display["Monthly_Exposure"] = pa_display["Monthly_Exposure"].apply(lambda x: f"${x:,.0f}")
pa_display["Avg_Dollar_Exposure"] = pa_display["Avg_Dollar_Exposure"].apply(lambda x: f"${x}")
st.dataframe(pa_display.set_index("Issue_Type"), use_container_width=True)

# ── Risk chart ────────────────────────────────────────────────────────────────
section("4 · Monthly Risk by Category", "📊")
categories = ["Employer Billing", "Pharmacy Overcharges", "PA / Eligibility", "Coding Risk"]
amounts    = [abs(total_emp_leakage), total_pharm_over,
              pa_issues[pa_issues.Regulatory_Risk=="High"]["Monthly_Exposure"].sum(),
              pa_issues[pa_issues.Regulatory_Risk=="Medium"]["Monthly_Exposure"].sum()]
colors_r   = [YELLOW, RED, RED, YELLOW]
fig = go.Figure(go.Bar(
    x=categories, y=[a/1e3 for a in amounts],
    marker_color=colors_r,
    text=[f"${a/1e3:.0f}K" for a in amounts], textposition="outside",
))
fig.update_layout(template="plotly_dark", paper_bgcolor=BG,
                  plot_bgcolor=CARD, yaxis_title="Monthly Risk ($K)",
                  height=300, margin=dict(l=0,r=0,t=10,b=0),
                  xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                  yaxis=dict(gridcolor="rgba(255,255,255,0.04)"))
st.plotly_chart(fig, use_container_width=True)

alert(
    f"<strong>Bottom line:</strong> ${total_monthly_risk/1e3:.0f}K/month (${total_monthly_risk*12/1e3:.0f}K/year) "
    f"in billing deviations and compliance risk identified. "
    f"The pharmacy AWP spread issue and PA-before-ship process are the highest priority fixes. "
    f"A CPA reviewing this monthly catches these before audit. "
    f"Sources: OIG Work Plan 2024 (telehealth billing) · AHIP Pharmacy Pricing Transparency Report 2024.",
    level="warning",
)

# ── AWP Renegotiation Impact Simulator ───────────────────────────────────────
section("5 · AWP Discount Renegotiation Simulator", "💊")
st.caption("Model the margin recovery from renegotiating pharmacy vendor AWP discounts.")

awp_col1, awp_col2 = st.columns(2, gap="large")

with awp_col1:
    st.markdown(
        '<div style="font-size:13px;font-weight:600;color:#94a3b8;margin-bottom:12px;">Current Contracted Discounts</div>',
        unsafe_allow_html=True
    )
    new_discounts = {}
    for _, row in ph_df.iterrows():
        label = f"{row['Drug']} ({row['Vendor'].split(' ')[0]})"
        current = float(row["Contract_AWP_Discount"])
        # slider in integer pct (18 = 18%) to avoid sprintf "%" bug in Streamlit 1.57
        cur_pct = int(round(current * 100))
        max_pct = int(round(min(current + 0.15, 0.40) * 100))
        new_pct = st.slider(
            f"{label} — target discount",
            min_value=cur_pct,
            max_value=max_pct,
            value=cur_pct + 3,
            step=1,
            format="%d%%",
            key=f"awp_{row['Drug']}",
        )
        new_discounts[row["Drug"]] = new_pct / 100.0

with awp_col2:
    renegotiated = ph_df.copy()
    renegotiated["New_Discount"]   = [new_discounts[d] for d in renegotiated["Drug"]]
    renegotiated["New_Net"]        = renegotiated["AWP_Per_Unit"] * (1 - renegotiated["New_Discount"])
    renegotiated["Current_Net"]    = renegotiated["Actual_Net"]
    renegotiated["Savings_Per_Unit"] = renegotiated["Current_Net"] - renegotiated["New_Net"]
    renegotiated["Monthly_Savings"]  = renegotiated["Savings_Per_Unit"] * renegotiated["Units_Monthly"]
    total_monthly_savings = renegotiated["Monthly_Savings"].sum()

    kpi_row([
        kpi_card(f"${max(total_monthly_savings,0)/1e3:.0f}K", "Monthly Margin Recovery",
                 "From renegotiated discounts", color="green" if total_monthly_savings > 0 else "yellow"),
        kpi_card(f"${max(total_monthly_savings,0)*12/1e3:.0f}K", "Annual Margin Recovery",
                 "Run-rate impact", color="green" if total_monthly_savings > 0 else "yellow"),
        kpi_card(f"{(total_monthly_savings / max(total_pharm_over,1) * 100):.0f}%",
                 "Overcharge Eliminated",
                 f"of ${total_pharm_over/1e3:.0f}K/mo baseline issue", color="blue"),
    ])

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    impact_df = renegotiated[["Drug","Contract_AWP_Discount","New_Discount","Savings_Per_Unit","Monthly_Savings"]].copy()
    impact_df["Contract_AWP_Discount"] = impact_df["Contract_AWP_Discount"].apply(lambda x: f"{x:.0%}")
    impact_df["New_Discount"]          = impact_df["New_Discount"].apply(lambda x: f"{x:.0%}")
    impact_df["Savings_Per_Unit"]      = impact_df["Savings_Per_Unit"].apply(lambda x: f"${x:.2f}/unit")
    impact_df["Monthly_Savings"]       = impact_df["Monthly_Savings"].apply(lambda x: f"${x:,.0f}")
    st.dataframe(impact_df.set_index("Drug"), use_container_width=True)

alert(
    f"Renegotiating AWP discounts to the target levels above recovers "
    f"<strong>${max(total_monthly_savings,0)/1e3:.0f}K/month (${max(total_monthly_savings,0)*12/1e3:.0f}K/year)</strong> "
    f"in gross margin — pure finance execution, no product changes required. "
    f"The Specialty Pharma A semaglutide contract is the highest-priority renegotiation target. "
    f"Source: IQVIA Specialty Pharmacy Pricing Benchmarks 2023.",
    level="success" if total_monthly_savings > 0 else "info",
)

# ── HEDIS Stars Quality Measures & Payer Contract Risk ────────────────────────
st.divider()
section("HEDIS Stars Quality Measures — Payer Contract Risk Monitor", "⭐")
st.markdown(
    '<div style="font-size:12px;color:#475569;margin:-8px 0 16px 0;">'
    'NCQA HEDIS 2026 · CMS Medicare Advantage Stars · Low rates trigger contract non-renewal and bonus clawbacks. '
    'Each measure below is a care gap that navigation programs close — directly protecting payer contract revenue.</div>',
    unsafe_allow_html=True
)

hedis_data = [
    {"Measure": "Colorectal Cancer Screening (COL-E)",       "Rate": 0.761, "NCQA_Avg": 0.680, "Stars_Floor": 0.700, "Revenue_Risk_K": 180},
    {"Measure": "Controlling High Blood Pressure (CBP)",      "Rate": 0.683, "NCQA_Avg": 0.630, "Stars_Floor": 0.680, "Revenue_Risk_K": 240},
    {"Measure": "Comprehensive Diabetes Care — A1c (CDC)",    "Rate": 0.724, "NCQA_Avg": 0.690, "Stars_Floor": 0.710, "Revenue_Risk_K": 310},
    {"Measure": "Breast Cancer Screening (BCS-E)",            "Rate": 0.798, "NCQA_Avg": 0.750, "Stars_Floor": 0.760, "Revenue_Risk_K": 95},
    {"Measure": "Annual Wellness Visit — Medicare (AWV)",     "Rate": 0.841, "NCQA_Avg": 0.790, "Stars_Floor": 0.800, "Revenue_Risk_K": 55},
    {"Measure": "Care for Older Adults — Med Review (COA)",   "Rate": 0.712, "NCQA_Avg": 0.670, "Stars_Floor": 0.700, "Revenue_Risk_K": 140},
    {"Measure": "Transitions of Care — Notification (TRC)",   "Rate": 0.658, "NCQA_Avg": 0.640, "Stars_Floor": 0.680, "Revenue_Risk_K": 420},
]
hedis_df = pd.DataFrame(hedis_data)
hedis_df["Above_Floor"] = hedis_df["Rate"] >= hedis_df["Stars_Floor"]
hedis_df["Status"] = hedis_df.apply(
    lambda r: "✅ Passing" if r["Rate"] >= r["Stars_Floor"] + 0.02
    else ("⚠️ At Risk" if r["Rate"] >= r["Stars_Floor"] else "🔴 Below Floor"), axis=1
)

h_col1, h_col2 = st.columns([3, 2], gap="medium")

with h_col1:
    fig_hedis = go.Figure()
    colors = [GREEN if row["Rate"] >= row["Stars_Floor"] + 0.02
              else (YELLOW if row["Rate"] >= row["Stars_Floor"] else RED)
              for _, row in hedis_df.iterrows()]
    fig_hedis.add_trace(go.Bar(
        name="Our Rate", y=hedis_df["Measure"], x=hedis_df["Rate"],
        orientation="h", marker_color=colors,
        text=[f"{v:.1%}" for v in hedis_df["Rate"]], textposition="outside",
        textfont=dict(size=11, color="#f1f5f9"),
    ))
    fig_hedis.add_trace(go.Scatter(
        name="Stars Floor", y=hedis_df["Measure"],
        x=hedis_df["Stars_Floor"],
        mode="markers", marker=dict(symbol="line-ns", size=14, color=RED,
                                    line=dict(color=RED, width=2)),
    ))
    fig_hedis.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        height=300, margin=dict(l=0, r=70, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0,
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickformat=".0%", range=[0, 1.05]),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10)),
    )
    st.plotly_chart(fig_hedis, use_container_width=True)

with h_col2:
    kpi_row([
        kpi_card(
            f"${hedis_df[~hedis_df['Above_Floor']]['Revenue_Risk_K'].sum():,}K",
            "Total Stars Revenue at Risk",
            "From measures below CMS floor",
            color="red"
        ),
        kpi_card(
            f"{(~hedis_df['Above_Floor']).sum()}/{len(hedis_df)}",
            "Measures At/Below Floor",
            "Trigger contract penalties",
            color="yellow"
        ),
    ])
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    disp_df = hedis_df[["Measure","Rate","Stars_Floor","Status","Revenue_Risk_K"]].copy()
    disp_df["Rate"]           = disp_df["Rate"].apply(lambda x: f"{x:.1%}")
    disp_df["Stars_Floor"]    = disp_df["Stars_Floor"].apply(lambda x: f"{x:.1%}")
    disp_df["Revenue_Risk_K"] = disp_df["Revenue_Risk_K"].apply(lambda x: f"${x}K")
    disp_df.columns = ["Measure","Rate","CMS Floor","Status","Revenue at Risk"]
    st.dataframe(disp_df.set_index("Measure"), use_container_width=True)

alert(
    "Transitions of Care (TRC) at 65.8% is <strong>below the CMS Stars floor (68.0%)</strong> — "
    "this is the highest-priority gap, contributing $420K of the total Stars revenue at risk. "
    "CBP (Blood Pressure Control) at 68.3% is 20 basis points above floor — marginal. "
    "Navigation interventions targeting these two measures have the highest ROI per dollar spent. "
    "Source: NCQA HEDIS 2026 Technical Specifications, CMS MA Stars 2026 cut points.",
    level="warning"
)

st.divider()

# ── CMS Stars Financial Impact Calculator ─────────────────────────────────────
section("CMS Stars Financial Impact Calculator", "⭐")
st.markdown(
    '<div style="font-size:12px;color:#475569;margin:-8px 0 14px 0;">'
    'Translates HEDIS quality improvements into CMS Medicare Advantage bonus payment dollars. '
    'Source: CMS MA Stars 2026 quality bonus payment methodology — '
    '$54/member/year per half-star improvement; double bonus for 4.5+ star plans.</div>',
    unsafe_allow_html=True,
)

stars_c1, stars_c2 = st.columns([2, 3], gap="large")
with stars_c1:
    ma_members    = st.number_input("Medicare Advantage enrolled members", 10_000, 2_000_000, 85_000, 5_000)
    current_stars = st.selectbox("Current Star Rating", ["2.5", "3.0", "3.5", "4.0", "4.5"], index=2)
    target_stars  = st.selectbox("Target Star Rating (after gap closure)",
                                  ["3.0", "3.5", "4.0", "4.5", "5.0"], index=2)
    nav_program_cost = st.number_input("Care navigation program cost ($/year)", 100_000, 5_000_000, 270_000, 10_000,
                                        help="ReferWell avg contract ~$270K/year")

with stars_c2:
    _star_vals    = {"2.5":2.5,"3.0":3.0,"3.5":3.5,"4.0":4.0,"4.5":4.5,"5.0":5.0}
    _cur          = _star_vals[current_stars]
    _tgt          = _star_vals[target_stars]
    _half_stars   = max(0, (_tgt - _cur) * 2)

    # CMS bonus: $54/member/year per half-star; 4.5+ plans receive additional quality bonus (~+5%)
    _bonus_base   = _half_stars * 54 * ma_members
    _double_bonus = (50 * ma_members) if _tgt >= 4.5 else 0      # ~$50/member additional for 4.5+ star
    _total_bonus  = _bonus_base + _double_bonus
    _net_benefit  = _total_bonus - nav_program_cost
    _roi_stars    = _total_bonus / max(nav_program_cost, 1)

    kpi_row([
        kpi_card(f"{_half_stars:.0f}", "Half-Star Improvement",
                 f"{current_stars} → {target_stars} Stars", color="blue"),
        kpi_card(f"${_total_bonus/1e6:.2f}M", "CMS Bonus Payment Uplift",
                 f"${54}/member × {_half_stars:.0f} half-stars × {ma_members:,} members",
                 color="green" if _total_bonus > nav_program_cost else "yellow"),
        kpi_card(f"${_net_benefit/1e6:.2f}M", "Net Benefit After Nav Cost",
                 f"${nav_program_cost/1e3:.0f}K navigation investment",
                 color="green" if _net_benefit > 0 else "red"),
        kpi_card(f"{_roi_stars:.1f}x", "Stars Bonus ROI",
                 "CMS payment uplift ÷ navigation cost",
                 color="green" if _roi_stars >= 3 else "yellow"),
    ])

    # Visual: current vs target stars
    _star_labels  = ["2.5★", "3.0★", "3.5★", "4.0★", "4.5★", "5.0★"]
    _star_values  = [2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
    _bar_colors   = []
    for sv in _star_values:
        if sv == _cur:
            _bar_colors.append(YELLOW)
        elif sv == _tgt:
            _bar_colors.append(GREEN)
        elif sv > _cur and sv < _tgt:
            _bar_colors.append("rgba(16,185,129,0.25)")
        else:
            _bar_colors.append("rgba(255,255,255,0.06)")
    _bonus_per_star = [max(0, (sv - _cur) * 2) * 54 * ma_members / 1e6 for sv in _star_values]
    fig_stars = go.Figure()
    fig_stars.add_trace(go.Bar(
        x=_star_labels, y=_bonus_per_star,
        marker_color=_bar_colors,
        text=[f"${v:.2f}M" if v > 0 else "" for v in _bonus_per_star],
        textposition="outside", textfont=dict(size=11, color="#f1f5f9"),
    ))
    fig_stars.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        height=220, margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="CMS Bonus Uplift ($M)"),
        annotations=[
            dict(x=current_stars+"★", y=0, text="Current", showarrow=True, arrowhead=2,
                 arrowcolor=YELLOW, font=dict(size=10, color=YELLOW), ay=-30),
            dict(x=target_stars+"★", y=_tgt > _cur and _bonus_per_star[_star_labels.index(target_stars+"★")] or 0.01,
                 text="Target", showarrow=True, arrowhead=2,
                 arrowcolor=GREEN, font=dict(size=10, color=GREEN), ay=-30),
        ] if _tgt > _cur else [],
    )
    st.plotly_chart(fig_stars, use_container_width=True)

if _net_benefit > 0:
    alert(
        f"At {ma_members:,} enrolled members, improving from {current_stars} to {target_stars} Stars generates "
        f"<strong>${_total_bonus/1e6:.2f}M in CMS bonus payments</strong> — "
        f"a <strong>{_roi_stars:.1f}x return</strong> on the ${nav_program_cost/1e3:.0f}K navigation program investment. "
        f"{'Plans reaching 4.5+ Stars receive an additional ~$50/member/year double bonus from CMS. ' if _tgt >= 4.5 else ''}"
        f"Source: CMS MA Stars 2026 quality bonus payment methodology.",
        level="success",
    )
else:
    alert(
        f"At this member count and star improvement, the ${nav_program_cost/1e3:.0f}K navigation cost "
        f"exceeds the ${_total_bonus/1e3:.0f}K CMS bonus uplift. "
        f"Consider increasing member count or targeting a higher star rating for positive ROI.",
        level="warning",
    )
