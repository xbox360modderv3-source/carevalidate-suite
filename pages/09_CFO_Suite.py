"""
CareValidate CFO Automation Suite
Monthly pack generator · 13-week cash flow · Contract renewal pipeline · Alert engine
Run: streamlit run app.py --server.port 8509
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from carevalidate_shared.theme import (
    GLOBAL_CSS, render_header, kpi_card, kpi_row, section, alert, sidebar_nav,
    BG, CARD, BLUE, GREEN, YELLOW, RED, PURPLE, TEAL, TEXT, MUTED,
)
from carevalidate_shared.auth import check_auth, logout_button
from carevalidate_shared.commentary import build_commentary, render_commentary_ui

st.set_page_config(page_title="CareValidate CFO Suite", layout="wide", page_icon="⚙")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
check_auth()
sidebar_nav("cfo")
logout_button()

render_header(
    "CFO Automation Suite",
    "Monthly pack · 13-week cash flow · Renewal pipeline · Alert engine",
    badge="Automation",
    badge_color="purple",
)

# ── Shared constants (consistent with other dashboards) ───────────────────────
MRR          = 1_240_000
ARR          = MRR * 12
CHURN_MO     = 0.028      # 2.8% monthly churn
GM_RATE      = 0.67
COMPLIANCE_RISK_MO = 87_000
HIGH_RISK_PATIENTS = 17
RUNWAY_MO    = 18
NRR          = 1.18
LTV_CAC      = 4.2
TODAY        = date.today()

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Executive Summary",
    "📋 Monthly CFO Pack",
    "💵 13-Week Cash Flow",
    "🤝 Contract Renewal Pipeline",
    "🚨 Alert Engine",
    "📉 Stress Test",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 0 — EXECUTIVE FINANCE COMMENTARY
# ══════════════════════════════════════════════════════════════════════════════
with tab0:
    _exec_metrics = {
        "mrr_current":        MRR,
        "mrr_prev":           1_050_000,
        "gross_margin":       GM_RATE,
        "gross_margin_prev":  GM_RATE - 0.014,
        "cash_runway_mo":     RUNWAY_MO,
        "cash_on_hand_m":     8.4,
        "denial_rate":        0.082,
        "dso_days":           27,
        "nrr":                NRR,
        "churn_rate_mo":      CHURN_MO,
        "ltv_cac":            LTV_CAC,
        "payback_months":     14,
        "compliance_risk_k":  COMPLIANCE_RISK_MO / 1_000,
        "high_risk_patients": HIGH_RISK_PATIENTS,
        "revenue_at_risk_k":  HIGH_RISK_PATIENTS * 285 * 3 / 1_000,
        "ar_overdue_k":       76.0,
        "at_risk_arr_k":      156.5,
        "report_month":       "May 2026",
    }
    _paras, _action_df, _dl_lines = build_commentary(_exec_metrics)
    render_commentary_ui(_paras, _action_df, _dl_lines, report_month="May 2026")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MONTHLY CFO PACK GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    section("Monthly CFO Pack Generator", "📋")
    st.caption("One-click monthly report for board, investors, and leadership. Copy the text block below into your investor email or Notion doc.")

    c1, c2, c3 = st.columns(3)
    with c1:
        report_month = st.selectbox("Report month", ["May 2026","Apr 2026","Mar 2026","Feb 2026"], index=0)
    with c2:
        prev_mrr = st.number_input("Prior month MRR ($)", value=1_050_000, step=10000)
    with c3:
        starting_cash = st.number_input("Cash on hand ($M)", value=8.4, step=0.1, format="%.1f")

    mrr_growth    = (MRR - prev_mrr) / prev_mrr
    arr_run       = MRR * 12
    gross_profit  = MRR * GM_RATE
    burn_mo       = MRR * GM_RATE - MRR * 0.95   # simplified: OpEx ~ 95% of revenue
    cash_runway   = (starting_cash * 1e6) / max(abs(burn_mo), 1)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    kpi_row([
        kpi_card(f"${MRR/1e3:.0f}K",  "MRR",     f"{mrr_growth:+.1%} vs prior month",
                 trend=f"{mrr_growth:+.1%}", trend_good=True, color="green"),
        kpi_card(f"${arr_run/1e6:.1f}M", "ARR Run Rate", "Annualized",
                 trend="+112% YoY", trend_good=True, color="blue"),
        kpi_card(f"{int(NRR*100)}%",    "NRR",     "Net Revenue Retention", color="green"),
        kpi_card(f"{LTV_CAC:.1f}x",    "LTV:CAC", "Blended", color="blue"),
        kpi_card(f"${COMPLIANCE_RISK_MO/1e3:.0f}K", "Compliance Risk",
                 "Monthly exposure", color="red"),
        kpi_card(f"{RUNWAY_MO}mo",     "Runway",   f"${starting_cash:.1f}M cash",
                 color="yellow" if RUNWAY_MO < 15 else "green"),
    ])

    section("MRR Waterfall — Month over Month", "")
    rng = np.random.default_rng(42)
    new_mrr       = int(MRR * 0.12)
    expansion_mrr = int(MRR * 0.04)
    churn_mrr     = int(prev_mrr * CHURN_MO)
    contraction   = int(prev_mrr * 0.005)

    fig_wf = go.Figure(go.Waterfall(
        name="MRR", orientation="v",
        measure=["absolute","relative","relative","relative","relative","total"],
        x=["Prior MRR","New Business","Expansion","Churn","Contraction","Current MRR"],
        y=[prev_mrr, new_mrr, expansion_mrr, -churn_mrr, -contraction, 0],
        text=[f"${prev_mrr/1e3:.0f}K", f"+${new_mrr/1e3:.0f}K",
              f"+${expansion_mrr/1e3:.0f}K", f"-${churn_mrr/1e3:.0f}K",
              f"-${contraction/1e3:.0f}K", f"${MRR/1e3:.0f}K"],
        textposition="outside",
        increasing=dict(marker_color=GREEN),
        decreasing=dict(marker_color=RED),
        totals=dict(marker_color=BLUE),
        connector=dict(line=dict(color="rgba(255,255,255,0.1)")),
    ))
    fig_wf.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        height=300, margin=dict(l=0,r=0,t=10,b=0),
        yaxis=dict(title="MRR ($)", gridcolor="rgba(255,255,255,0.04)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        showlegend=False,
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    section("Copy-Paste Investor Update", "📧")
    pack_text = f"""CAREVALIDATE — MONTHLY INVESTOR UPDATE
{report_month} | Confidential

━━ HEADLINE METRICS ━━━━━━━━━━━━━━━━━━━━━━━━━━
MRR:              ${MRR:,}   ({mrr_growth:+.1%} MoM)
ARR Run Rate:     ${arr_run:,}
NRR:              {int(NRR*100)}%
LTV:CAC:          {LTV_CAC:.1f}x
Gross Margin:     {int(GM_RATE*100)}%
Cash:             ${starting_cash:.1f}M
Runway:           {RUNWAY_MO} months

━━ MRR BRIDGE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Prior month MRR:  ${prev_mrr:,}
  + New business: +${new_mrr:,}
  + Expansion:    +${expansion_mrr:,}
  − Churn:        −${churn_mrr:,}
  − Contraction:  −${contraction:,}
Current MRR:      ${MRR:,}

━━ OPERATIONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Active patients:  850
High churn risk:  {HIGH_RISK_PATIENTS} patients (${HIGH_RISK_PATIENTS*285*3/1e3:.0f}K 90-day revenue at risk)
Compliance risk:  ${COMPLIANCE_RISK_MO:,}/month identified and being addressed
GLP-1 program:    3,200 patients, {int(GM_RATE*100)}% gross margin

━━ HIGHLIGHTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• HealthJoy employer channel CAC: $42 (vs $380 paid digital)
• Employer channel retention: 77% at 12 months (vs 60% DTC)
• AWP renegotiation in progress — targeting $70K/month margin recovery
• Series A process: ongoing, data room complete

━━ RISKS & MITIGATIONS ━━━━━━━━━━━━━━━━━━━━━━━
• FDA compounded GLP-1 ban: S2 (branded pivot) scenario projects ${20.71:.2f}M 12-mo revenue
• Pharmacy overcharge: ${COMPLIANCE_RISK_MO/1e3:.0f}K/month — AWP contract renegotiation initiated
• {HIGH_RISK_PATIENTS} high-risk churn patients: proactive outreach program active

Next update: {(datetime.strptime(report_month, '%b %Y') + timedelta(days=32)).strftime('%b %Y')}
— CareValidate Finance Team
"""
    st.text_area("Monthly investor update (copy → paste into email/Notion):", pack_text, height=480)
    alert("This report is generated from the synthetic dashboard inputs above. In production, update inputs from your actual MRR and cash position before sending.", level="info")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — 13-WEEK ROLLING CASH FLOW FORECAST
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    section("13-Week Rolling Cash Flow Forecast", "💵")
    st.caption("Auto-updates from contracted MRR, expected churn, and cost structure. Adjust assumptions in the sidebar to model scenarios.")

    cf_c1, cf_c2 = st.columns([1, 2], gap="large")
    with cf_c1:
        st.markdown('<div style="font-size:12px;font-weight:700;color:#475569;margin-bottom:10px;">ASSUMPTIONS</div>', unsafe_allow_html=True)
        cf_scenario  = st.radio("Scenario", ["Base", "Optimistic", "Conservative"],
                                horizontal=True, key="cf_scen")
        cash_start   = st.number_input("Starting cash ($M)", value=8.4, step=0.1, format="%.1f") * 1e6
        mrr_input    = st.number_input("Current MRR ($)", value=MRR, step=10000)
        churn_wk     = st.slider("Weekly churn rate (%)", 0.2, 2.0, 0.65, 0.05) / 100
        cogs_pct     = st.slider("COGS as % of revenue", 20, 60, 33) / 100
        payroll_mo   = st.number_input("Monthly payroll ($)", value=380_000, step=10000)
        vendor_mo    = st.number_input("Vendor payments (monthly $)", value=75_000, step=5000,
                                       help="Pharmacy, platform, and vendor contracts")
        marketing_mo = st.number_input("Monthly marketing ($)", value=85_000, step=5000)
        other_opex   = st.number_input("Other monthly OpEx ($)", value=20_000, step=5000)
        settlement_delay = st.slider("Payment settlement delay (days)", 0, 14, 0,
                                     help="Days added to collection timing — delays near-term cash inflows")
        one_off      = st.number_input("One-time items this period ($)", value=0, step=10000,
                                       help="Positive = inflow (e.g. fundraise), Negative = outflow")

    with cf_c2:
        weeks      = np.arange(1, 14)
        week_dates = [TODAY + timedelta(weeks=int(w)-1) for w in weeks]
        week_labels = [d.strftime("%b %d") for d in week_dates]

        # Scenario parameters
        _scen_params = {
            "Base":         (1.00,  0.000,  0.00,  0),
            "Optimistic":   (1.10, -0.001, -0.02,  0),
            "Conservative": (0.90,  0.003,  0.04,  5),
        }
        _rev_m, _ch_adj, _cogs_adj, _set_adj = _scen_params[cf_scenario]

        settle_factor = max(0.0, 1 - (settlement_delay + _set_adj) / 90)
        adj_cogs      = min(cogs_pct + _cogs_adj, 0.85)
        adj_churn     = max(churn_wk + _ch_adj, 0.001)
        wk_rev_base   = mrr_input / 4.33 * _rev_m * settle_factor
        wk_payroll    = payroll_mo / 4.33
        wk_vendor     = vendor_mo  / 4.33
        wk_mkt        = marketing_mo / 4.33
        wk_other      = other_opex / 4.33
        total_fixed_wk = wk_payroll + wk_vendor + wk_mkt + wk_other

        revenues, cogs_list, opex_list, vendor_list, net_flows, balances = [], [], [], [], [], []
        balance = cash_start
        for i in range(13):
            rev  = wk_rev_base * (1 - adj_churn) ** i
            cogs = rev * adj_cogs
            add  = one_off if i == 0 else 0
            net  = rev - cogs - total_fixed_wk + add
            balance += net
            revenues.append(rev)
            cogs_list.append(cogs)
            opex_list.append(wk_payroll + wk_mkt + wk_other)
            vendor_list.append(wk_vendor)
            net_flows.append(net)
            balances.append(balance)

        # Three scenario cash balance lines
        def _scen_balances(rev_m, ch_adj, cogs_adj, set_adj):
            sf  = max(0.0, 1 - (settlement_delay + set_adj) / 90)
            wkr = mrr_input / 4.33 * rev_m * sf
            ac  = min(cogs_pct + cogs_adj, 0.85)
            ach = max(churn_wk + ch_adj, 0.001)
            bal = cash_start
            out = []
            for i in range(13):
                r = wkr * (1 - ach) ** i
                bal += r - r * ac - total_fixed_wk
                out.append(bal)
            return out

        bals_opt  = _scen_balances(1.10, -0.001, -0.02, 0)
        bals_base = _scen_balances(1.00,  0.000,  0.00, 0)
        bals_cons = _scen_balances(0.90,  0.003,  0.04, 5)

        weeks_to_zero   = next((i+1 for i, b in enumerate(balances) if b < 0), None)
        cons_zero       = next((i+1 for i, b in enumerate(bals_cons) if b < 0), None)
        net_burn_mo     = (revenues[-1] - cogs_list[-1] - opex_list[-1] - vendor_list[-1]) * 4.33
        ending_runway   = balances[-1] / max(abs(net_burn_mo), 1) if net_burn_mo < 0 else None

        kpi_row([
            kpi_card(f"${cash_start/1e6:.1f}M", "Starting Cash", "Week 0", color="blue"),
            kpi_card(f"${balances[-1]/1e6:.2f}M", f"Ending Cash · {cf_scenario}",
                     "Week 13 at current trajectory",
                     color="green" if balances[-1] > 0 else "red"),
            kpi_card(
                f"${abs(net_burn_mo)/1e3:.0f}K/mo",
                "Net Cash Flow" if net_burn_mo >= 0 else "Monthly Burn",
                "Revenue − COGS − All OpEx",
                color="green" if net_burn_mo >= 0 else "red",
            ),
            kpi_card(
                "Stable" if weeks_to_zero is None else f"Week {weeks_to_zero}",
                "Cash Crisis Point",
                "First week balance goes negative",
                color="green" if weeks_to_zero is None else "red",
            ),
        ])

        # Chart
        fig_cf = go.Figure()
        fig_cf.add_trace(go.Bar(
            x=week_labels, y=[r/1e3 for r in revenues],
            name="Revenue", marker_color=GREEN, opacity=0.75,
        ))
        fig_cf.add_trace(go.Bar(
            x=week_labels, y=[-c/1e3 for c in cogs_list],
            name="COGS", marker_color=YELLOW, opacity=0.75,
        ))
        fig_cf.add_trace(go.Bar(
            x=week_labels, y=[-(o+v)/1e3 for o, v in zip(opex_list, vendor_list)],
            name="OpEx + Vendor", marker_color=RED, opacity=0.75,
        ))
        fig_cf.add_trace(go.Scatter(
            x=week_labels, y=[b/1e6 for b in bals_opt],
            name="Optimistic", yaxis="y2",
            line=dict(color=GREEN, width=1.5, dash="dot"),
            mode="lines",
        ))
        fig_cf.add_trace(go.Scatter(
            x=week_labels, y=[b/1e6 for b in bals_base],
            name="Base", yaxis="y2",
            line=dict(color=BLUE, width=2.5),
            mode="lines+markers", marker=dict(size=5),
        ))
        fig_cf.add_trace(go.Scatter(
            x=week_labels, y=[b/1e6 for b in bals_cons],
            name="Conservative", yaxis="y2",
            line=dict(color=RED, width=1.5, dash="dot"),
            mode="lines",
        ))
        fig_cf.update_layout(
            template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
            barmode="relative", height=360, margin=dict(l=0, r=60, t=10, b=0),
            yaxis=dict(title="Weekly Cash Flow ($K)", gridcolor="rgba(255,255,255,0.04)"),
            yaxis2=dict(title="Cash Balance ($M)", overlaying="y", side="right",
                        showgrid=False, tickformat="$.2f"),
            legend=dict(orientation="h", yanchor="bottom", y=1, bgcolor="rgba(0,0,0,0)",
                        font=dict(size=11)),
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        )
        st.plotly_chart(fig_cf, use_container_width=True)

        # Detailed table
        cf_df = pd.DataFrame({
            "Week":               week_labels,
            "Revenue ($K)":       [f"${r/1e3:.0f}K" for r in revenues],
            "COGS ($K)":          [f"${c/1e3:.0f}K" for c in cogs_list],
            "Payroll+Mktg ($K)":  [f"${o/1e3:.0f}K" for o in opex_list],
            "Vendor ($K)":        [f"${v/1e3:.0f}K" for v in vendor_list],
            "Net Flow ($K)":      [f"{'+'if n>0 else ''}${n/1e3:.0f}K" for n in net_flows],
            "Cash Balance ($M)":  [f"${b/1e6:.2f}M" for b in balances],
        })
        st.dataframe(cf_df.set_index("Week"), use_container_width=True)

        # ── Alerts ────────────────────────────────────────────────────────
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if weeks_to_zero:
            alert(
                f"<strong>Cash crisis in Week {weeks_to_zero}</strong> under the {cf_scenario} scenario. "
                f"Ending balance goes negative — immediate action required.",
                level="error",
            )
        if cons_zero and cf_scenario != "Conservative":
            alert(
                f"Conservative scenario hits negative cash in Week {cons_zero}. "
                f"Model downside risk before the next board meeting.",
                level="warning",
            )
        if ending_runway is not None and ending_runway < 6:
            alert(
                f"Implied runway below 6 months at Week 13 burn rate. "
                f"Initiate bridge financing or OpEx reduction plan.",
                level="error",
            )
        if vendor_mo > (payroll_mo + marketing_mo + other_opex) * 0.40:
            alert(
                f"Vendor payments (${vendor_mo/1e3:.0f}K/mo) represent more than 40% of non-COGS OpEx. "
                f"Review vendor contract terms for flexibility.",
                level="warning",
            )
        if settlement_delay >= 7:
            alert(
                f"Settlement delay of {settlement_delay} days reduces effective weekly collections by "
                f"{(1 - settle_factor)*100:.0f}%. Monitor processor settlement files daily.",
                level="warning",
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CONTRACT RENEWAL PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    section("Contract Renewal Pipeline", "🤝")
    st.caption("Employer contracts sorted by renewal date. Renewal probability scored on outcomes, engagement, and ROI delivered.")

    contracts = pd.DataFrame([
        {"Client":"HealthJoy Enterprise Pool","Type":"PMPM","Lives":1_000_000,
         "Monthly_Rev":12_000,"Start":"2024-06-01","Term_Months":24,
         "Outcomes_Score":88,"Engagement_Score":82,"ROI_Delivered":4.8,
         "Relationship":"Strong"},
        {"Client":"AccommoCare Client A","Type":"PMPM","Lives":18_000,
         "Monthly_Rev":153_000,"Start":"2024-09-01","Term_Months":12,
         "Outcomes_Score":74,"Engagement_Score":61,"ROI_Delivered":3.2,
         "Relationship":"Moderate"},
        {"Client":"AccommoCare Client B","Type":"PMPM","Lives":6_500,
         "Monthly_Rev":59_800,"Start":"2025-01-01","Term_Months":12,
         "Outcomes_Score":81,"Engagement_Score":77,"ROI_Delivered":4.1,
         "Relationship":"Strong"},
        {"Client":"AccommoCare Client C","Type":"PEPM","Lives":22_000,
         "Monthly_Rev":148_500,"Start":"2024-11-01","Term_Months":18,
         "Outcomes_Score":58,"Engagement_Score":49,"ROI_Delivered":2.4,
         "Relationship":"At Risk"},
        {"Client":"White-Label Partner A","Type":"Platform","Lives":0,
         "Monthly_Rev":8_500,"Start":"2025-03-01","Term_Months":12,
         "Outcomes_Score":90,"Engagement_Score":88,"ROI_Delivered":6.1,
         "Relationship":"Strong"},
        {"Client":"White-Label Partner B","Type":"Platform","Lives":0,
         "Monthly_Rev":12_000,"Start":"2024-08-01","Term_Months":24,
         "Outcomes_Score":71,"Engagement_Score":65,"ROI_Delivered":3.8,
         "Relationship":"Moderate"},
        {"Client":"White-Label Partner C","Type":"Platform","Lives":0,
         "Monthly_Rev":6_800,"Start":"2025-02-01","Term_Months":12,
         "Outcomes_Score":45,"Engagement_Score":38,"ROI_Delivered":1.9,
         "Relationship":"At Risk"},
    ])

    contracts["Start_Date"]   = pd.to_datetime(contracts["Start"])
    contracts["Renewal_Date"] = contracts["Start_Date"] + pd.to_timedelta(contracts["Term_Months"]*30, unit="d")
    contracts["Days_To_Renewal"] = (contracts["Renewal_Date"] - pd.Timestamp(TODAY)).dt.days
    contracts["Annual_Rev"]   = contracts["Monthly_Rev"] * 12

    # Renewal probability model
    def renewal_prob(row):
        score = (
            row["Outcomes_Score"]  * 0.35 +
            row["Engagement_Score"]* 0.25 +
            min(row["ROI_Delivered"] / 5 * 100, 100) * 0.25 +
            {"Strong":100,"Moderate":55,"At Risk":20}[row["Relationship"]] * 0.15
        )
        return round(score)

    contracts["Renewal_Prob"] = contracts.apply(renewal_prob, axis=1)
    contracts["Expected_Rev"] = (contracts["Annual_Rev"] * contracts["Renewal_Prob"] / 100).round(0).astype(int)
    contracts["Rev_at_Risk"]  = contracts["Annual_Rev"] - contracts["Expected_Rev"]

    def urgency(row):
        if row["Days_To_Renewal"] < 60:  return "🔴 Immediate"
        if row["Days_To_Renewal"] < 120: return "🟡 Soon"
        return "🟢 On Track"
    contracts["Urgency"] = contracts.apply(urgency, axis=1)

    contracts_sorted = contracts.sort_values("Days_To_Renewal")

    # Summary KPIs
    at_risk_rev = contracts[contracts["Renewal_Prob"] < 70]["Annual_Rev"].sum()
    exp_renewal_rev = contracts["Expected_Rev"].sum()
    contracts_90d = (contracts["Days_To_Renewal"] < 90).sum()

    kpi_row([
        kpi_card(f"{len(contracts)}", "Active Contracts",
                 f"${contracts['Annual_Rev'].sum()/1e6:.1f}M total ARR", color="blue"),
        kpi_card(f"{contracts_90d}", "Renewing in 90 Days",
                 "Require active management", color="red" if contracts_90d > 1 else "yellow"),
        kpi_card(f"${exp_renewal_rev/1e6:.1f}M", "Expected Renewal ARR",
                 "Probability-weighted", color="green"),
        kpi_card(f"${at_risk_rev/1e3:.0f}K", "ARR at Risk",
                 "Renewal prob <70%", color="red" if at_risk_rev > 100000 else "yellow"),
    ])

    # Pipeline table
    display_c = contracts_sorted[[
        "Client","Type","Renewal_Date","Days_To_Renewal",
        "Annual_Rev","Renewal_Prob","Rev_at_Risk","Relationship","Urgency"
    ]].copy()
    display_c["Renewal_Date"]    = display_c["Renewal_Date"].dt.strftime("%b %d, %Y")
    display_c["Days_To_Renewal"] = display_c["Days_To_Renewal"].apply(lambda x: f"{x}d")
    display_c["Annual_Rev"]      = display_c["Annual_Rev"].apply(lambda x: f"${x:,}")
    display_c["Renewal_Prob"]    = display_c["Renewal_Prob"].apply(lambda x: f"{x}%")
    display_c["Rev_at_Risk"]     = display_c["Rev_at_Risk"].apply(lambda x: f"${x:,}")
    st.dataframe(display_c.set_index("Client"), use_container_width=True, height=320)

    # Timeline chart
    section("Renewal Timeline & Revenue at Risk by Quarter", "")
    rc1, rc2 = st.columns(2, gap="medium")

    with rc1:
        fig_tl = go.Figure()
        colors_rel = {"Strong": GREEN, "Moderate": YELLOW, "At Risk": RED}
        for _, row in contracts_sorted.iterrows():
            color = colors_rel.get(row["Relationship"], BLUE)
            fig_tl.add_trace(go.Scatter(
                x=[row["Renewal_Date"]],
                y=[row["Client"]],
                mode="markers+text",
                marker=dict(size=row["Annual_Rev"]/8000, color=color, opacity=0.85),
                text=[f"${row['Annual_Rev']/1e3:.0f}K"],
                textposition="middle right",
                textfont=dict(size=10, color="#94a3b8"),
                name=row["Relationship"],
                showlegend=False,
            ))
        _window_x = str(TODAY + timedelta(days=90))
        fig_tl.add_shape(type="line", x0=_window_x, x1=_window_x, y0=0, y1=1,
                         xref="x", yref="paper",
                         line=dict(dash="dash", color=YELLOW, width=1))
        fig_tl.add_annotation(x=_window_x, y=1, text="90-day window",
                               showarrow=False, yref="paper", yanchor="bottom",
                               font=dict(size=10, color=YELLOW), bgcolor="rgba(0,0,0,0)")
        fig_tl.update_layout(
            template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
            height=300, margin=dict(l=0,r=80,t=10,b=0),
            xaxis=dict(title="Renewal Date", gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        )
        st.plotly_chart(fig_tl, use_container_width=True)

    with rc2:
        contracts["Qtr"] = contracts["Renewal_Date"].dt.to_period("Q").astype(str)
        qtr_risk = contracts.groupby("Qtr").agg(
            Total_ARR=("Annual_Rev","sum"),
            At_Risk=("Rev_at_Risk","sum"),
        ).reset_index()
        fig_qr = go.Figure()
        fig_qr.add_trace(go.Bar(x=qtr_risk["Qtr"], y=qtr_risk["Total_ARR"]/1e3,
                                name="Total ARR renewing", marker_color=BLUE, opacity=0.7))
        fig_qr.add_trace(go.Bar(x=qtr_risk["Qtr"], y=qtr_risk["At_Risk"]/1e3,
                                name="ARR at risk", marker_color=RED, opacity=0.85))
        fig_qr.update_layout(
            template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
            barmode="overlay", height=300, margin=dict(l=0,r=0,t=10,b=0),
            yaxis=dict(title="ARR ($K)", gridcolor="rgba(255,255,255,0.04)"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            legend=dict(orientation="h", yanchor="bottom", y=1, bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        )
        st.plotly_chart(fig_qr, use_container_width=True)

    at_risk_clients = contracts[contracts["Renewal_Prob"] < 70]["Client"].tolist()
    if at_risk_clients:
        alert(
            f"<strong>Action required:</strong> {', '.join(at_risk_clients)} have renewal probability below 70%. "
            f"Recommend scheduling QBR and delivering outcomes report 60+ days before renewal. "
            f"Combined at-risk ARR: ${at_risk_rev/1e3:.0f}K.",
            level="warning"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ALERT ENGINE
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    section("Alert Engine — Real-Time Threshold Monitoring", "🚨")
    st.caption("Set thresholds for each metric. Alerts fire when any metric crosses its limit. In production, these push to Slack or email.")

    al1, al2 = st.columns([1, 2], gap="large")

    with al1:
        st.markdown('<div style="font-size:12px;font-weight:700;color:#475569;margin-bottom:12px;">CONFIGURE THRESHOLDS</div>', unsafe_allow_html=True)
        thresh_mrr_growth   = st.slider("MRR growth floor (% MoM)",   0, 20, 10)
        thresh_churn_mo     = st.slider("Monthly churn ceiling (%)",   1, 10, 5)
        thresh_comply_risk  = st.slider("Compliance risk ceiling ($K)", 20, 200, 100)
        thresh_runway       = st.slider("Min cash runway (months)",     6, 24, 12)
        thresh_high_risk    = st.slider("High churn patients ceiling",  10, 100, 50)
        thresh_nrr          = st.slider("NRR floor (%)",               80, 130, 105)
        thresh_ltv_cac      = st.slider("LTV:CAC floor (x)",           1.0, 6.0, 3.0, 0.5)

    with al2:
        # Current metric values vs thresholds
        current_mrr_growth_pct = 18.1
        current_churn_mo_pct   = CHURN_MO * 100
        current_comply_k       = COMPLIANCE_RISK_MO / 1e3
        current_runway         = RUNWAY_MO
        current_high_risk      = HIGH_RISK_PATIENTS
        current_nrr_pct        = NRR * 100
        current_ltv_cac        = LTV_CAC

        alerts_cfg = [
            {
                "metric": "MRR Growth (MoM)",
                "current": f"{current_mrr_growth_pct:.1f}%",
                "threshold": f">{thresh_mrr_growth}%",
                "ok": current_mrr_growth_pct >= thresh_mrr_growth,
                "critical": current_mrr_growth_pct < thresh_mrr_growth * 0.7,
                "value": current_mrr_growth_pct,
                "limit": thresh_mrr_growth,
            },
            {
                "metric": "Monthly Churn Rate",
                "current": f"{current_churn_mo_pct:.1f}%",
                "threshold": f"<{thresh_churn_mo}%",
                "ok": current_churn_mo_pct <= thresh_churn_mo,
                "critical": current_churn_mo_pct > thresh_churn_mo * 1.5,
                "value": current_churn_mo_pct,
                "limit": thresh_churn_mo,
            },
            {
                "metric": "Compliance Risk",
                "current": f"${current_comply_k:.0f}K/mo",
                "threshold": f"<${thresh_comply_risk}K",
                "ok": current_comply_k <= thresh_comply_risk,
                "critical": current_comply_k > thresh_comply_risk * 1.5,
                "value": current_comply_k,
                "limit": thresh_comply_risk,
            },
            {
                "metric": "Cash Runway",
                "current": f"{current_runway}mo",
                "threshold": f">{thresh_runway}mo",
                "ok": current_runway >= thresh_runway,
                "critical": current_runway < thresh_runway * 0.75,
                "value": current_runway,
                "limit": thresh_runway,
            },
            {
                "metric": "High Churn Risk Patients",
                "current": str(current_high_risk),
                "threshold": f"<{thresh_high_risk}",
                "ok": current_high_risk <= thresh_high_risk,
                "critical": current_high_risk > thresh_high_risk * 1.5,
                "value": current_high_risk,
                "limit": thresh_high_risk,
            },
            {
                "metric": "Net Revenue Retention",
                "current": f"{current_nrr_pct:.0f}%",
                "threshold": f">{thresh_nrr}%",
                "ok": current_nrr_pct >= thresh_nrr,
                "critical": current_nrr_pct < thresh_nrr * 0.9,
                "value": current_nrr_pct,
                "limit": thresh_nrr,
            },
            {
                "metric": "LTV:CAC Ratio",
                "current": f"{current_ltv_cac:.1f}x",
                "threshold": f">{thresh_ltv_cac:.1f}x",
                "ok": current_ltv_cac >= thresh_ltv_cac,
                "critical": current_ltv_cac < thresh_ltv_cac * 0.8,
                "value": current_ltv_cac,
                "limit": thresh_ltv_cac,
            },
        ]

        firing = [a for a in alerts_cfg if not a["ok"]]
        ok_count = len([a for a in alerts_cfg if a["ok"]])

        st.markdown(
            f'<div style="display:flex;gap:12px;margin-bottom:16px;">'
            f'<div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.25);'
            f'border-radius:10px;padding:12px 18px;flex:1;text-align:center;">'
            f'<div style="font-size:22px;font-weight:800;color:{GREEN};">{ok_count}</div>'
            f'<div style="font-size:11px;color:#475569;margin-top:3px;">Metrics OK</div>'
            f'</div>'
            f'<div style="background:{"rgba(239,68,68,0.1)" if firing else "rgba(16,185,129,0.08)"};'
            f'border:1px solid {"rgba(239,68,68,0.25)" if firing else "rgba(16,185,129,0.2)"};'
            f'border-radius:10px;padding:12px 18px;flex:1;text-align:center;">'
            f'<div style="font-size:22px;font-weight:800;color:{RED if firing else GREEN};">{len(firing)}</div>'
            f'<div style="font-size:11px;color:#475569;margin-top:3px;">Alerts Firing</div>'
            f'</div></div>',
            unsafe_allow_html=True
        )

        for a in alerts_cfg:
            if a["ok"]:
                dot_color, bg, border = GREEN, "rgba(16,185,129,0.06)", "rgba(16,185,129,0.15)"
                label = "OK"
            elif a["critical"]:
                dot_color, bg, border = RED, "rgba(239,68,68,0.08)", "rgba(239,68,68,0.25)"
                label = "CRITICAL"
            else:
                dot_color, bg, border = YELLOW, "rgba(245,158,11,0.08)", "rgba(245,158,11,0.25)"
                label = "WARNING"

            st.markdown(
                f'<div style="display:flex;align-items:center;gap:12px;padding:10px 14px;'
                f'background:{bg};border:1px solid {border};border-radius:8px;margin-bottom:6px;">'
                f'<span style="width:8px;height:8px;border-radius:50%;background:{dot_color};'
                f'flex-shrink:0;display:inline-block;"></span>'
                f'<span style="font-size:13px;color:#e2e8f0;flex:1;">{a["metric"]}</span>'
                f'<span style="font-size:12px;color:#64748b;">threshold: {a["threshold"]}</span>'
                f'<span style="font-size:13px;font-weight:700;color:{dot_color};min-width:80px;text-align:right;">'
                f'{a["current"]}</span>'
                f'<span style="font-size:10px;font-weight:700;color:{dot_color};'
                f'background:{"rgba(239,68,68,0.12)" if not a["ok"] else "rgba(16,185,129,0.1)"};'
                f'padding:2px 7px;border-radius:6px;min-width:68px;text-align:center;">{label}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

    # Slack/email copy
    section("Copy Alert Summary for Slack / Email", "📨")
    slack_lines = [f"*CareValidate Metric Alert — {TODAY.strftime('%b %d, %Y')}*\n"]
    for a in alerts_cfg:
        icon = "✅" if a["ok"] else ("🚨" if a["critical"] else "⚠️")
        slack_lines.append(f"{icon} {a['metric']}: *{a['current']}* (threshold {a['threshold']})")
    slack_lines.append(f"\n{ok_count}/{len(alerts_cfg)} metrics within target. "
                       f"{'No action required.' if not firing else f'{len(firing)} metric(s) need attention.'}")
    st.text_area("Slack message (paste into #finance channel):", "\n".join(slack_lines), height=260)

st.divider()

# ── MLR Finance Impact Model ───────────────────────────────────────────────────
section("MLR Finance Impact Model — Care Navigation Spend Illustration", "⚖️")
st.markdown(
    '<div style="font-size:12px;color:#475569;margin:-8px 0 14px 0;">'
    '<strong>Illustrative model only.</strong> Under ACA §2718, health plans are subject to MLR requirements. '
    'Certain care navigation or quality improvement activities may be treated differently for MLR purposes '
    'depending on plan structure, documentation, and regulatory review. '
    'This dashboard is a finance scenario tool, not a legal conclusion. '
    'MLR treatment should be confirmed with qualified legal and compliance counsel. '
    'Source assumptions: CMS MLR guidance, AHIP 2024 MLR reporting benchmarks.</div>',
    unsafe_allow_html=True,
)

mlr_c1, mlr_c2 = st.columns(2, gap="large")
with mlr_c1:
    st.markdown('<div style="font-size:11px;color:#64748b;font-weight:600;letter-spacing:.06em;margin-bottom:10px;">HEALTH PLAN INPUTS</div>', unsafe_allow_html=True)
    total_premium    = st.number_input("Total annual premium revenue ($M)", 50, 5000, 850, 50)
    mkt_segment      = st.selectbox("Market segment (determines MLR floor)", ["Medicare Advantage (80%)", "Medicaid MCO (80%)", "Large Group Commercial (85%)", "Small Group Commercial (80%)"])
    current_mlr_pct  = st.slider("Current MLR (%)", 70, 95, 78, 1, format="%d%%")
    nav_spend_annual = st.number_input("Annual care navigation spend ($K)", 50, 10_000, 270, 10,
                                        help="ReferWell avg contract: ~$270K/year")

with mlr_c2:
    _mlr_floor = 0.85 if "Large Group" in mkt_segment else 0.80
    _floor_pct = int(_mlr_floor * 100)
    _premium_m = total_premium * 1e6
    _required_mlr_spend = _premium_m * _mlr_floor
    _current_mlr_spend  = _premium_m * (current_mlr_pct / 100)
    _mlr_gap            = _required_mlr_spend - _current_mlr_spend
    _nav_spend          = nav_spend_annual * 1_000
    _new_mlr_spend      = _current_mlr_spend + _nav_spend
    _new_mlr_pct        = _new_mlr_spend / _premium_m
    _rebate_before      = max(0, _mlr_gap)
    _rebate_after       = max(0, _required_mlr_spend - _new_mlr_spend)
    _rebate_avoided     = _rebate_before - _rebate_after

    kpi_row([
        kpi_card(f"{_floor_pct}%", "MLR Floor",
                 mkt_segment.split("(")[0].strip(), color="blue"),
        kpi_card(f"${_mlr_gap/1e6:.1f}M" if _mlr_gap > 0 else "✓ Met",
                 "MLR Shortfall (Before Nav)",
                 f"Current: {current_mlr_pct}% vs {_floor_pct}% floor",
                 color="red" if _mlr_gap > 0 else "green"),
        kpi_card(f"{_new_mlr_pct:.1%}", "MLR After Nav Spend",
                 f"+{(_new_mlr_pct - current_mlr_pct/100)*100:.1f}pp from navigation fees",
                 color="green" if _new_mlr_pct >= _mlr_floor else "yellow"),
        kpi_card(f"${_rebate_avoided/1e3:.0f}K", "Member Rebate Avoided",
                 "MLR rebates that would otherwise be owed",
                 color="green" if _rebate_avoided > 0 else "blue"),
    ])

# Combined value bridge
st.markdown('<div style="font-size:11px;color:#64748b;font-weight:600;letter-spacing:.06em;margin:16px 0 10px 0;">TOTAL VALUE BRIDGE — CARE NAVIGATION INVESTMENT</div>', unsafe_allow_html=True)
_claims_savings = _nav_spend * 8.7  # ReferWell published 8.7x avg
_stars_uplift   = _nav_spend * 2.1
bridge_items = [
    ("Navigation cost",       -_nav_spend,      RED,    "Annual program fee"),
    ("MLR rebate avoided",     _rebate_avoided,  YELLOW, "No longer owed to members"),
    ("Stars bonus uplift",     _stars_uplift,    TEAL,   "Half-star × members × $54"),
    ("Claims savings (8.7x)", _claims_savings,   GREEN,  "ReferWell published benchmark"),
]
net_val = sum(v for _, v, _, _ in bridge_items)

fig_bridge = go.Figure(go.Bar(
    x=[abs(v) / 1e3 for _, v, _, _ in bridge_items],
    y=[lbl for lbl, _, _, _ in bridge_items],
    orientation="h",
    marker_color=[c for _, _, c, _ in bridge_items],
    text=[f"{'−' if v < 0 else '+'}${abs(v)/1e3:.0f}K  {note}"
          for _, v, _, note in bridge_items],
    textposition="outside",
    textfont=dict(size=11, color="#f1f5f9"),
))
fig_bridge.update_layout(
    template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
    height=220, margin=dict(l=0, r=200, t=10, b=0),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="Value ($K)", tickprefix="$", ticksuffix="K"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
)
st.plotly_chart(fig_bridge, use_container_width=True)

_total_roi = (net_val + _nav_spend) / max(_nav_spend, 1)
alert(
    f"A ${nav_spend_annual}K annual care navigation investment at a {total_premium}M-premium health plan generates "
    f"<strong>${_claims_savings/1e3:.0f}K in claims savings (8.7x ROI)</strong>, "
    f"<strong>${_rebate_avoided/1e3:.0f}K in MLR rebates avoided</strong>, "
    f"and an estimated Stars bonus uplift — "
    f"for a combined net value of <strong>${net_val/1e3:.0f}K</strong>. "
    f"MLR treatment may vary depending on plan structure and regulatory review. "
    f"This model is illustrative and based on public benchmark assumptions. "
    f"Source assumptions: CMS MLR guidance, ReferWell published outcomes, CMS MA Stars 2026.",
    level="success" if net_val > 0 else "info",
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — SCENARIO STRESS TEST
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    section("Scenario Stress Test", "📉")
    st.caption(
        "Move the sliders to stress-test the business model. "
        "All outputs are driven by synthetic assumptions — illustrative only."
    )

    # ── Base constants ────────────────────────────────────────────────────
    _BASE_MRR         = MRR            # $1.24M
    _BASE_GM          = GM_RATE        # 0.67
    _BASE_COGS_PCT    = 1 - GM_RATE    # 0.33
    _BASE_CHURN_MO    = CHURN_MO       # 0.028
    _BASE_RUNWAY      = RUNWAY_MO      # 18
    _BASE_CAC         = 127            # blended CAC $
    _BASE_PAYBACK_MO  = 14
    _BASE_ARPU        = 285            # $/patient/mo
    _BASE_PATIENTS    = 850
    _BASE_OPEX_MO     = 380_000 + 85_000 + 75_000 + 20_000  # payroll+mkt+vendor+other
    _BASE_CASH        = 8.4e6

    st_s1, st_s2 = st.columns([1, 2], gap="large")

    with st_s1:
        st.markdown(
            '<div style="font-size:12px;font-weight:700;color:#475569;margin-bottom:12px;">STRESS LEVERS</div>',
            unsafe_allow_html=True,
        )
        denial_shock      = st.slider("Denial rate increase (pp)",        0, 15,  0, 1,
                                      help="Each +1pp denial reduces effective collections ~0.8%") / 100
        retention_shock   = st.slider("Refill retention decline (pp)",    0, 20,  0, 1,
                                      help="Reduces MRR from existing patients") / 100
        cac_shock         = st.slider("CAC increase (%)",                 0, 50,  0, 5) / 100
        pharma_shock      = st.slider("Pharmacy cost increase (%)",       0, 30,  0, 5,
                                      help="Increases COGS as % of revenue") / 100
        settle_shock_days = st.slider("Settlement delay (additional days)",0, 14,  0, 1,
                                      help="Defers cash collections — reduces near-term runway")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:11px;color:#334155;line-height:1.6;">'
            'Synthetic data only. No PHI. Prototype for discussion. '
            'Outputs are illustrative and should not be treated as financial, '
            'legal, or compliance advice.'
            '</div>',
            unsafe_allow_html=True,
        )

    with st_s2:
        # ── Compute stressed values ───────────────────────────────────────
        # Denial shock: each pp → ~0.8% revenue reduction (denial → A/R delay)
        denial_rev_impact   = denial_shock * 0.8
        # Retention shock: reduces existing patient MRR by that fraction
        retention_rev_impact = retention_shock
        # Combined MRR impact
        stressed_mrr        = _BASE_MRR * (1 - denial_rev_impact - retention_rev_impact)
        mrr_delta           = stressed_mrr - _BASE_MRR

        # COGS: pharmacy cost increase as additional % of revenue
        stressed_cogs_pct   = _BASE_COGS_PCT * (1 + pharma_shock)
        stressed_gm         = 1 - stressed_cogs_pct
        gm_delta_pp         = (stressed_gm - _BASE_GM) * 100

        # Gross profit impact
        base_gp_mo          = _BASE_MRR * _BASE_GM
        stressed_gp_mo      = stressed_mrr * stressed_gm
        gp_delta_mo         = stressed_gp_mo - base_gp_mo

        # CAC shock → marketing OpEx increases, payback extends
        stressed_cac        = _BASE_CAC * (1 + cac_shock)
        payback_delta_mo    = (stressed_cac - _BASE_CAC) / _BASE_ARPU

        # EBITDA proxy: gross profit − fixed opex
        ebitda_base         = base_gp_mo - _BASE_OPEX_MO
        ebitda_stressed     = stressed_gp_mo - _BASE_OPEX_MO * (1 + cac_shock * 0.3)
        ebitda_delta        = ebitda_stressed - ebitda_base

        # Runway impact: stressed monthly burn / cash
        stressed_burn_mo    = max(-ebitda_stressed, 0)
        base_burn_mo        = max(-ebitda_base, 0)
        stressed_runway     = _BASE_CASH / stressed_burn_mo if stressed_burn_mo > 0 else 99
        runway_delta        = stressed_runway - _BASE_RUNWAY

        # Break-even patients: opex / (ARPU × stressed GM)
        stressed_margin_per_pt = _BASE_ARPU * stressed_gm
        breakeven_pts         = int(_BASE_OPEX_MO / max(stressed_margin_per_pt, 1))
        breakeven_delta       = breakeven_pts - int(_BASE_OPEX_MO / max(_BASE_ARPU * _BASE_GM, 1))

        # Settlement delay cash impact (~$K deferred over 13 weeks)
        settle_cash_drag_k  = settle_shock_days * _BASE_MRR / 30 / 1e3

        # ── KPI cards ─────────────────────────────────────────────────────
        kpi_row([
            kpi_card(
                f"${mrr_delta/1e3:+.0f}K/mo",
                "MRR Impact",
                f"Stressed: ${stressed_mrr/1e3:.0f}K",
                color="red" if mrr_delta < 0 else "green",
            ),
            kpi_card(
                f"{gm_delta_pp:+.1f}pp",
                "Gross Margin Impact",
                f"Stressed: {stressed_gm:.1%}",
                color="red" if gm_delta_pp < 0 else "green",
            ),
            kpi_card(
                f"${ebitda_delta/1e3:+.0f}K/mo",
                "EBITDA Impact",
                f"Stressed: ${ebitda_stressed/1e3:+.0f}K/mo",
                color="red" if ebitda_delta < 0 else "green",
            ),
            kpi_card(
                f"{runway_delta:+.1f}mo" if stressed_runway < 99 else "Stable",
                "Runway Impact",
                f"Stressed: {min(stressed_runway, 99):.1f}mo" if stressed_runway < 99 else "Cash flow positive",
                color="red" if runway_delta < -2 else "yellow" if runway_delta < 0 else "green",
            ),
        ])
        kpi_row([
            kpi_card(
                f"{breakeven_pts:,} pts",
                "Break-Even Patient Volume",
                f"Delta: {breakeven_delta:+,} vs. base",
                color="red" if breakeven_delta > 50 else "yellow" if breakeven_delta > 0 else "green",
            ),
            kpi_card(
                f"{_BASE_PAYBACK_MO + payback_delta_mo:.1f}mo",
                "CAC Payback (Stressed)",
                f"Base: {_BASE_PAYBACK_MO}mo · +{payback_delta_mo:.1f}mo",
                color="red" if payback_delta_mo > 3 else "yellow" if payback_delta_mo > 0 else "green",
            ),
            kpi_card(
                f"−${settle_cash_drag_k:.0f}K",
                "Settlement Cash Drag",
                f"{settle_shock_days}d delay × ${_BASE_MRR/30/1e3:.0f}K/day",
                color="red" if settle_cash_drag_k > 50 else "yellow" if settle_cash_drag_k > 0 else "green",
            ),
            kpi_card(
                f"${gp_delta_mo/1e3:+.0f}K/mo",
                "Gross Profit Impact",
                f"Stressed GP: ${stressed_gp_mo/1e3:.0f}K/mo",
                color="red" if gp_delta_mo < 0 else "green",
            ),
        ])

        # ── Tornado chart — sensitivity by lever ─────────────────────────
        section("Sensitivity: EBITDA Impact by Lever", "")

        _levers = []
        if denial_shock > 0:
            _d = -denial_shock * 0.8 * _BASE_MRR * _BASE_GM / 1e3
            _levers.append(("Denial rate +" + f"{denial_shock*100:.0f}pp", _d))
        if retention_shock > 0:
            _r = -retention_shock * _BASE_MRR * _BASE_GM / 1e3
            _levers.append(("Retention −" + f"{retention_shock*100:.0f}pp", _r))
        if pharma_shock > 0:
            _p = -pharma_shock * _BASE_COGS_PCT * _BASE_MRR / 1e3
            _levers.append(("Pharmacy cost +" + f"{pharma_shock*100:.0f}%", _p))
        if cac_shock > 0:
            _c = -cac_shock * 0.3 * _BASE_OPEX_MO / 1e3
            _levers.append(("CAC +" + f"{cac_shock*100:.0f}%", _c))
        if settle_shock_days > 0:
            _s = -settle_cash_drag_k
            _levers.append((f"Settlement +{settle_shock_days}d", _s))

        if _levers:
            _levers.sort(key=lambda x: x[1])
            lever_names, lever_vals = zip(*_levers)
            bar_colors = [RED if v < -20 else YELLOW if v < 0 else GREEN for v in lever_vals]
            fig_tornado = go.Figure(go.Bar(
                x=list(lever_vals),
                y=list(lever_names),
                orientation="h",
                marker_color=bar_colors,
                text=[f"${v:+.0f}K/mo" for v in lever_vals],
                textposition="outside",
                textfont=dict(size=11, color="#f1f5f9"),
            ))
            fig_tornado.update_layout(
                template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
                height=max(180, len(_levers) * 52),
                margin=dict(l=0, r=100, t=10, b=0),
                xaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="EBITDA Impact ($K/mo)",
                           tickprefix="$", ticksuffix="K", zeroline=True,
                           zerolinecolor="rgba(255,255,255,0.15)", zerolinewidth=1),
                yaxis=dict(showgrid=False, tickfont=dict(size=11)),
                showlegend=False,
            )
            st.plotly_chart(fig_tornado, use_container_width=True)
        else:
            st.markdown(
                '<div style="background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.18);'
                'border-radius:10px;padding:20px;text-align:center;color:#64748b;font-size:13px;">'
                'Move any slider above to see sensitivity impact.</div>',
                unsafe_allow_html=True,
            )

        # ── Summary table ──────────────────────────────────────────────────
        section("Stress Test Summary", "")
        summary_df = pd.DataFrame([
            {"Metric": "MRR",              "Base": f"${_BASE_MRR/1e3:.0f}K/mo",    "Stressed": f"${stressed_mrr/1e3:.0f}K/mo",      "Delta": f"${mrr_delta/1e3:+.0f}K/mo"},
            {"Metric": "Gross Margin",     "Base": f"{_BASE_GM:.1%}",               "Stressed": f"{stressed_gm:.1%}",                 "Delta": f"{gm_delta_pp:+.1f}pp"},
            {"Metric": "EBITDA",           "Base": f"${ebitda_base/1e3:+.0f}K/mo", "Stressed": f"${ebitda_stressed/1e3:+.0f}K/mo",  "Delta": f"${ebitda_delta/1e3:+.0f}K/mo"},
            {"Metric": "Cash Runway",      "Base": f"{_BASE_RUNWAY}mo",             "Stressed": f"{min(stressed_runway,99):.1f}mo" if stressed_burn_mo > 0 else "Positive", "Delta": f"{runway_delta:+.1f}mo" if stressed_burn_mo > 0 else "—"},
            {"Metric": "Break-even Pts",   "Base": f"{int(_BASE_OPEX_MO / max(_BASE_ARPU*_BASE_GM,1)):,}", "Stressed": f"{breakeven_pts:,}", "Delta": f"{breakeven_delta:+,}"},
            {"Metric": "CAC Payback",      "Base": f"{_BASE_PAYBACK_MO}mo",         "Stressed": f"{_BASE_PAYBACK_MO + payback_delta_mo:.1f}mo", "Delta": f"{payback_delta_mo:+.1f}mo"},
            {"Metric": "Settlement Drag",  "Base": "$0",                            "Stressed": f"−${settle_cash_drag_k:.0f}K",      "Delta": f"−${settle_cash_drag_k:.0f}K"},
        ])
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        # Download stress test summary
        stress_csv = summary_df.to_csv(index=False).encode()
        st.download_button(
            label="⬇ Download Stress Test Summary CSV",
            data=stress_csv,
            file_name="stress_test_summary.csv",
            mime="text/csv",
            key="dl_stress",
        )
