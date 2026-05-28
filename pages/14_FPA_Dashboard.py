"""
CareValidate FP&A Dashboard
Budget vs. actuals, variance waterfall, rolling forecast, department burn, headcount model.
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta
from carevalidate_shared.theme import (
    GLOBAL_CSS, render_header, kpi_card, kpi_row, section, alert, sidebar_nav,
    BG, CARD, BLUE, GREEN, YELLOW, RED, PURPLE, TEAL, MUTED, TEXT,
)
from carevalidate_shared.auth import check_auth, logout_button

st.set_page_config(page_title="CareValidate FP&A Dashboard", layout="wide", page_icon="📋")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
check_auth()
sidebar_nav("fpa")
logout_button()

render_header(
    "FP&A Dashboard",
    "Budget vs. actuals · rolling forecast · department burn · headcount model",
    badge="FP&A",
    badge_color="blue",
)

# ── Constants ─────────────────────────────────────────────────────────────────
rng = np.random.default_rng(42)
REPORT_MONTH = "May 2026"
TODAY = date.today()

# Budget assumptions (annual, then monthly)
BUD_MRR        = 1_180_000   # budgeted MRR for May
ACT_MRR        = 1_240_000   # actual MRR
BUD_COGS_PCT   = 0.35
ACT_COGS_PCT   = 0.33        # favorable — pharmacy cost savings
BUD_OPEX       = 920_000
ACT_OPEX       = 956_000     # slight overage — headcount hire ahead of plan
BUD_GM         = BUD_MRR * (1 - BUD_COGS_PCT)
ACT_GM         = ACT_MRR * (1 - ACT_COGS_PCT)
BUD_EBITDA     = BUD_GM - BUD_OPEX
ACT_EBITDA     = ACT_GM - ACT_OPEX

REV_VAR        = ACT_MRR - BUD_MRR
REV_VAR_PCT    = REV_VAR / BUD_MRR * 100
OPEX_VAR       = ACT_OPEX - BUD_OPEX       # positive = over budget
OPEX_VAR_PCT   = OPEX_VAR / BUD_OPEX * 100
EBITDA_VAR     = ACT_EBITDA - BUD_EBITDA
EBITDA_VAR_PCT = EBITDA_VAR / abs(BUD_EBITDA) * 100

DEPARTMENTS = ["Engineering", "Operations", "Sales & Mktg", "Finance", "G&A"]
HC_BUD   = [24, 31, 18, 7, 5]
HC_ACT   = [26, 30, 19, 7, 5]
COST_BUD = [390_000, 280_000, 155_000, 65_000, 30_000]
COST_ACT = [412_000, 275_000, 161_000, 63_000, 45_000]

# ── KPI strip ─────────────────────────────────────────────────────────────────
kpi_row([
    kpi_card(f"${ACT_MRR/1e3:,.0f}K", "Revenue (Actual)",
             f"Budget ${BUD_MRR/1e3:,.0f}K · {REV_VAR_PCT:+.1f}% vs plan",
             trend=f"{REV_VAR_PCT:+.1f}% vs budget", trend_good=True, color="green"),
    kpi_card(f"{ACT_GM/ACT_MRR:.1%}", "Gross Margin",
             f"Budget {BUD_GM/BUD_MRR:.1%} · +{(ACT_GM/ACT_MRR - BUD_GM/BUD_MRR)*10000:.0f}bps",
             trend="+140bps vs budget", trend_good=True, color="green"),
    kpi_card(f"${ACT_OPEX/1e3:,.0f}K", "Total OpEx",
             f"Budget ${BUD_OPEX/1e3:,.0f}K · {OPEX_VAR_PCT:+.1f}% over",
             trend=f"{OPEX_VAR_PCT:+.1f}% over budget", trend_good=False, color="yellow"),
    kpi_card(f"${ACT_EBITDA/1e3:,.0f}K", "EBITDA",
             f"Budget ${BUD_EBITDA/1e3:,.0f}K · {EBITDA_VAR_PCT:+.1f}% vs plan",
             trend=f"{EBITDA_VAR_PCT:+.1f}% vs budget", trend_good=EBITDA_VAR > 0, color="blue"),
])

tab0, tab1, tab2, tab3 = st.tabs([
    "📊 Budget vs. Actuals",
    "📈 Rolling Forecast",
    "👥 Headcount & Burn",
    "📝 Variance Commentary",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 0 — BUDGET VS. ACTUALS
# ══════════════════════════════════════════════════════════════════════════════
with tab0:
    section("P&L Bridge — Budget to Actual", "🌉")
    st.caption(f"Month: {REPORT_MONTH}  ·  Favorable variances shown in green, unfavorable in red")

    # Waterfall chart
    waterfall_labels = [
        "Budget Revenue", "Revenue Beat",
        "Budget COGS", "COGS Savings",
        "Budget Gross Profit",
        "Actual Gross Profit",
        "Budget OpEx", "OpEx Over",
        "Budget EBITDA", "Actual EBITDA",
    ]
    wf_x = [
        "Budget Revenue", "+ Revenue Beat",
        "Budget COGS Relief", "+ COGS Savings",
        "→ Budget GP", "→ Actual GP",
        "Budget OpEx", "OpEx Overage",
        "→ Budget EBITDA", "→ Actual EBITDA",
    ]
    wf_measure = ["absolute", "relative", "absolute", "relative",
                  "absolute", "absolute",
                  "absolute", "relative",
                  "absolute", "absolute"]
    wf_y = [
        BUD_MRR, REV_VAR,
        -BUD_MRR * BUD_COGS_PCT, (BUD_COGS_PCT - ACT_COGS_PCT) * ACT_MRR,
        BUD_GM, ACT_GM,
        -BUD_OPEX, -OPEX_VAR,
        BUD_EBITDA, ACT_EBITDA,
    ]
    wf_colors = ["#3b82f6", "#10b981", "#ef4444", "#10b981",
                 "#3b82f6", "#3b82f6",
                 "#ef4444", "#f59e0b",
                 "#8b5cf6", "#8b5cf6"]

    fig_wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=wf_measure,
        x=wf_x,
        y=[v / 1000 for v in wf_y],
        text=[f"${v/1000:+,.0f}K" for v in wf_y],
        textposition="outside",
        connector={"line": {"color": "rgba(255,255,255,0.1)", "width": 1, "dash": "dot"}},
        increasing={"marker": {"color": "#10b981"}},
        decreasing={"marker": {"color": "#ef4444"}},
        totals={"marker": {"color": "#3b82f6"}},
    ))
    fig_wf.update_layout(
        height=420, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "family": "Inter, sans-serif", "size": 11},
        yaxis={"title": "$K", "gridcolor": "rgba(255,255,255,0.06)", "zeroline": True,
               "zerolinecolor": "rgba(255,255,255,0.15)"},
        xaxis={"tickangle": -20},
        margin={"l": 40, "r": 20, "t": 20, "b": 80},
        showlegend=False,
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    # Monthly variance table
    section("Monthly P&L — Budget vs. Actuals Detail", "📋")
    line_items = [
        ("Revenue",         BUD_MRR,              ACT_MRR,              True),
        ("  COGS",          -BUD_MRR*BUD_COGS_PCT, -ACT_MRR*ACT_COGS_PCT, False),
        ("Gross Profit",    BUD_GM,               ACT_GM,               True),
        ("  Engineering",   -COST_BUD[0],         -COST_ACT[0],         False),
        ("  Operations",    -COST_BUD[1],         -COST_ACT[1],         False),
        ("  Sales & Mktg",  -COST_BUD[2],         -COST_ACT[2],         False),
        ("  Finance",       -COST_BUD[3],         -COST_ACT[3],         False),
        ("  G&A",           -COST_BUD[4],         -COST_ACT[4],         False),
        ("Total OpEx",      -BUD_OPEX,            -ACT_OPEX,            False),
        ("EBITDA",          BUD_EBITDA,           ACT_EBITDA,           True),
    ]
    rows = []
    for label, bud, act, fav_positive in line_items:
        var = act - bud
        var_pct = var / abs(bud) * 100 if bud != 0 else 0
        favorable = (var > 0) if fav_positive else (var < 0)
        rag = "🟢" if favorable and abs(var_pct) > 1 else ("🔴" if not favorable and abs(var_pct) > 3 else "🟡")
        rows.append({
            "Line Item":    label,
            "Budget ($K)":  f"${bud/1000:,.0f}",
            "Actual ($K)":  f"${act/1000:,.0f}",
            "Variance ($K)":f"${var/1000:+,.0f}",
            "Var %":        f"{var_pct:+.1f}%",
            "Status":       rag,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=380)

    alert(
        f"Revenue beat of ${REV_VAR/1e3:,.0f}K ({REV_VAR_PCT:+.1f}%) driven by employer channel outperformance and higher NRR. "
        f"OpEx overage of ${OPEX_VAR/1e3:,.0f}K reflects one Engineering hire pulled forward into May. "
        f"Net EBITDA impact: ${EBITDA_VAR/1e3:+,.0f}K vs. budget.",
        level="success" if EBITDA_VAR > 0 else "warning",
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ROLLING FORECAST
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    section("Rolling 12-Month Forecast — Revenue & EBITDA", "📈")

    _months = pd.date_range(end=TODAY, periods=6, freq="MS").tolist() + \
              pd.date_range(start=TODAY + timedelta(days=32), periods=6, freq="MS").tolist()
    _labels = [d.strftime("%b %y") for d in _months]
    _actuals_rev = [
        890_000, 940_000, 985_000, 1_040_000, 1_150_000, 1_240_000,
        None, None, None, None, None, None,
    ]
    _forecast_rev = [
        None, None, None, None, None, 1_240_000,
        1_298_000, 1_358_000, 1_421_000, 1_487_000, 1_556_000, 1_628_000,
    ]
    _budget_rev = [
        860_000, 910_000, 960_000, 1_010_000, 1_090_000, 1_180_000,
        1_250_000, 1_320_000, 1_390_000, 1_460_000, 1_535_000, 1_610_000,
    ]
    _actuals_ebitda = [
        -62_000, -48_000, -31_000, 12_000, 44_000, 83_000,
        None, None, None, None, None, None,
    ]
    _forecast_ebitda = [
        None, None, None, None, None, 83_000,
        101_000, 121_000, 144_000, 169_000, 196_000, 226_000,
    ]
    _budget_ebitda = [
        -55_000, -40_000, -22_000, 18_000, 52_000, 95_000,
        112_000, 132_000, 155_000, 180_000, 207_000, 237_000,
    ]

    fig_fc = go.Figure()
    fig_fc.add_trace(go.Bar(
        x=_labels, y=[v/1000 if v else None for v in _actuals_rev],
        name="Actual Revenue", marker_color=BLUE, opacity=0.85,
    ))
    fig_fc.add_trace(go.Bar(
        x=_labels, y=[v/1000 if v else None for v in _forecast_rev],
        name="Forecast Revenue", marker_color="#3b82f640",
        marker_line_color=BLUE, marker_line_width=1.5,
    ))
    fig_fc.add_trace(go.Scatter(
        x=_labels, y=[v/1000 for v in _budget_rev],
        name="Budget", mode="lines+markers",
        line={"color": YELLOW, "width": 2, "dash": "dot"},
        marker={"size": 5},
    ))
    fig_fc.add_trace(go.Scatter(
        x=_labels, y=[v/1000 if v is not None else None for v in _actuals_ebitda],
        name="Actual EBITDA", mode="lines+markers",
        line={"color": GREEN, "width": 2},
        marker={"size": 6}, yaxis="y2",
    ))
    fig_fc.add_trace(go.Scatter(
        x=_labels, y=[v/1000 if v is not None else None for v in _forecast_ebitda],
        name="Forecast EBITDA", mode="lines+markers",
        line={"color": GREEN, "width": 2, "dash": "dash"},
        marker={"size": 5, "symbol": "circle-open"}, yaxis="y2",
    ))
    fig_fc.add_vline(
        x=5.5, line_width=1, line_dash="solid",
        line_color="rgba(255,255,255,0.2)",
        annotation_text="Forecast →",
        annotation_font_color="#64748b",
        annotation_font_size=10,
    )
    fig_fc.update_layout(
        height=420, barmode="overlay",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "family": "Inter, sans-serif", "size": 11},
        yaxis={"title": "Revenue ($K)", "gridcolor": "rgba(255,255,255,0.06)"},
        yaxis2={"title": "EBITDA ($K)", "overlaying": "y", "side": "right",
                "gridcolor": "rgba(255,255,255,0)", "zeroline": True,
                "zerolinecolor": "rgba(255,255,255,0.1)"},
        legend={"orientation": "h", "y": -0.15, "x": 0},
        margin={"l": 50, "r": 50, "t": 20, "b": 60},
    )
    st.plotly_chart(fig_fc, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        section("Forecast Assumptions", "⚙")
        assump = pd.DataFrame([
            ("MoM Revenue Growth", "4.7%", "Budget: 5.1%", "🟡 Slightly below plan"),
            ("Gross Margin Trend", "67.0%→67.8%", "COGS efficiency improvement", "🟢 Favorable"),
            ("OpEx Growth", "2.1%/mo", "One Q3 engineering hire in plan", "🟡 Watch"),
            ("EBITDA Breakeven", "Already positive", "2 months ahead of budget", "🟢 Ahead"),
            ("12-Month FY Rev", "$16.2M", "Budget: $15.9M · +1.9%", "🟢 Above plan"),
        ], columns=["Assumption", "Value", "Note", "Status"])
        st.dataframe(assump, use_container_width=True, hide_index=True)
    with col_b:
        section("Scenario Sensitivity — FY Revenue", "🎛")
        sensit = pd.DataFrame([
            ("Bear (-1pp growth/mo)",  "$14.9M", "-6.3% vs base"),
            ("Base (4.7%/mo)",         "$16.2M", "—"),
            ("Bull (+1pp growth/mo)",  "$17.6M", "+8.6% vs base"),
            ("Upside (GLP-1 rebound)", "$18.1M", "+11.7% vs base"),
        ], columns=["Scenario", "FY Revenue", "vs Base"])
        st.dataframe(sensit, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — HEADCOUNT & BURN
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    section("Headcount by Department — Budget vs. Actual", "👥")

    hc_df = pd.DataFrame({
        "Department":       DEPARTMENTS,
        "HC Budget":        HC_BUD,
        "HC Actual":        HC_ACT,
        "HC Variance":      [a - b for a, b in zip(HC_ACT, HC_BUD)],
        "Cost Budget ($K)": [f"${c/1000:,.0f}" for c in COST_BUD],
        "Cost Actual ($K)": [f"${c/1000:,.0f}" for c in COST_ACT],
        "Cost Var ($K)":    [f"${(a-b)/1000:+,.0f}" for a, b in zip(COST_ACT, COST_BUD)],
        "Loaded $/HC":      [f"${a/h/1000:.0f}K" for a, h in zip(COST_ACT, HC_ACT)],
    })
    st.dataframe(hc_df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        fig_hc = go.Figure()
        fig_hc.add_trace(go.Bar(name="Budget HC", x=DEPARTMENTS, y=HC_BUD,
                                marker_color=BLUE, opacity=0.6))
        fig_hc.add_trace(go.Bar(name="Actual HC", x=DEPARTMENTS, y=HC_ACT,
                                marker_color=GREEN, opacity=0.85))
        fig_hc.update_layout(
            height=320, barmode="group", title_text="Headcount: Budget vs. Actual",
            title_font_color="#94a3b8", title_font_size=12,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#94a3b8", "size": 11},
            yaxis={"gridcolor": "rgba(255,255,255,0.06)"},
            legend={"orientation": "h", "y": -0.2},
            margin={"l": 30, "r": 10, "t": 40, "b": 60},
        )
        st.plotly_chart(fig_hc, use_container_width=True)

    with col2:
        fig_cost = go.Figure()
        fig_cost.add_trace(go.Bar(name="Budget Cost", x=DEPARTMENTS,
                                  y=[c/1000 for c in COST_BUD],
                                  marker_color=BLUE, opacity=0.6))
        fig_cost.add_trace(go.Bar(name="Actual Cost", x=DEPARTMENTS,
                                  y=[c/1000 for c in COST_ACT],
                                  marker_color=YELLOW, opacity=0.85))
        fig_cost.update_layout(
            height=320, barmode="group", title_text="Dept Cost ($K): Budget vs. Actual",
            title_font_color="#94a3b8", title_font_size=12,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#94a3b8", "size": 11},
            yaxis={"title": "$K", "gridcolor": "rgba(255,255,255,0.06)"},
            legend={"orientation": "h", "y": -0.2},
            margin={"l": 40, "r": 10, "t": 40, "b": 60},
        )
        st.plotly_chart(fig_cost, use_container_width=True)

    section("Burn Rate & Cash Efficiency", "🔥")
    total_hc_bud = sum(HC_BUD)
    total_hc_act = sum(HC_ACT)
    total_cost_act = sum(COST_ACT)
    rev_per_hc = ACT_MRR / total_hc_act
    burn_per_hc = total_cost_act / total_hc_act

    kpi_row([
        kpi_card(f"{total_hc_act}", "Total Headcount",
                 f"Budget: {total_hc_bud} · +{total_hc_act - total_hc_bud} vs plan",
                 color="blue"),
        kpi_card(f"${rev_per_hc:,.0f}", "Revenue per HC",
                 "Monthly MRR / total headcount", color="green"),
        kpi_card(f"${burn_per_hc:,.0f}", "Loaded Cost per HC",
                 "Total OpEx / headcount", color="yellow"),
        kpi_card(f"{ACT_MRR / total_cost_act:.2f}x", "Revenue / OpEx",
                 "Efficiency ratio · target >1.3x", color="purple"),
    ])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — VARIANCE COMMENTARY
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    section("FP&A Variance Narrative", "📝")

    _aud_col, _tone_col, _ = st.columns([1, 1, 2])
    with _aud_col:
        _aud = st.selectbox("Audience", ["Board", "Finance Team", "Investors"],
                            index=0, key="fpa_audience")
    with _tone_col:
        _tone = st.selectbox("Tone", ["Executive", "Detailed"],
                             index=0, key="fpa_tone")

    _badge_color = {"Board": "#3b82f6", "Investors": "#8b5cf6", "Finance Team": "#10b981"}.get(_aud, "#3b82f6")
    _tone_label = "Concise" if _tone == "Executive" else "Full narrative"

    # Build variance narrative based on audience and tone
    _rev_narrative = {
        ("Board", "Executive"):
            f"Revenue beat of ${REV_VAR/1e3:,.0f}K ({REV_VAR_PCT:+.1f}%) vs. plan. Employer channel outperformed; GLP-1 NRR held above 115%.",
        ("Board", "Detailed"):
            f"May revenue of ${ACT_MRR/1e3:,.0f}K exceeded the ${BUD_MRR/1e3:,.0f}K budget by ${REV_VAR/1e3:,.0f}K ({REV_VAR_PCT:+.1f}%). "
            f"The beat was driven by two employer contracts activating one month ahead of schedule and stronger-than-expected GLP-1 refill retention (NRR 118% vs. budgeted 112%). "
            f"DTC channel performed in line with plan. No material one-time items.",
        ("Investors", "Executive"):
            f"NRR 118% · Revenue {REV_VAR_PCT:+.1f}% above plan · EBITDA positive ${ACT_EBITDA/1e3:,.0f}K · 2mo ahead of profitability budget.",
        ("Investors", "Detailed"):
            f"Unit economics strengthened in May: NRR of 118% and a revenue beat of {REV_VAR_PCT:+.1f}% signal durable installed-base expansion. "
            f"EBITDA turned positive at ${ACT_EBITDA/1e3:,.0f}K, two months ahead of the budget timeline — a key Series A milestone. "
            f"CAC payback remains 14 months with LTV:CAC of 4.2x, both within target range.",
        ("Finance Team", "Executive"):
            f"Rev: ${ACT_MRR/1e3:,.0f}K actual vs ${BUD_MRR/1e3:,.0f}K budget (+${REV_VAR/1e3:,.0f}K). OpEx: ${ACT_OPEX/1e3:,.0f}K vs ${BUD_OPEX/1e3:,.0f}K (+${OPEX_VAR/1e3:,.0f}K). Net: ${EBITDA_VAR/1e3:+,.0f}K EBITDA vs budget.",
        ("Finance Team", "Detailed"):
            f"Revenue favorable ${REV_VAR/1e3:,.0f}K driven by employer channel pull-forward and refill rate above plan. "
            f"COGS rate improved 140bps to 33.0% on pharmacy AWP renegotiation savings — ${(BUD_COGS_PCT - ACT_COGS_PCT)*ACT_MRR/1e3:,.0f}K favorable. "
            f"OpEx unfavorable ${OPEX_VAR/1e3:,.0f}K due to one Engineering FTE hire in May vs. June plan — run-rate impact ${COST_ACT[0]/HC_ACT[0]/1e3:.0f}K/mo. "
            f"Net EBITDA variance ${EBITDA_VAR/1e3:+,.0f}K favorable to plan.",
    }
    _opex_narrative = {
        ("Board", "Executive"):
            f"OpEx ${OPEX_VAR/1e3:,.0f}K over budget — one Engineering hire pulled forward. Full-year OpEx plan unchanged.",
        ("Board", "Detailed"):
            f"Total OpEx of ${ACT_OPEX/1e3:,.0f}K was ${OPEX_VAR/1e3:,.0f}K ({OPEX_VAR_PCT:+.1f}%) above the ${BUD_OPEX/1e3:,.0f}K budget. "
            f"The variance is fully explained by one senior Engineering hire activated in May rather than June. "
            f"All other departments are at or below budget. Full-year OpEx guidance is unchanged; the hire was planned, not incremental.",
        ("Investors", "Executive"):
            f"OpEx ${OPEX_VAR_PCT:+.1f}% above budget on one planned Engineering hire. Efficiency ratio {ACT_MRR/ACT_OPEX:.2f}x revenue-to-OpEx.",
        ("Investors", "Detailed"):
            f"OpEx overage of ${OPEX_VAR/1e3:,.0f}K reflects a single planned Engineering hire accelerated into May. "
            f"This is a timing item, not a budget expansion. Revenue-to-OpEx efficiency of {ACT_MRR/ACT_OPEX:.2f}x remains well above the 1.3x target, "
            f"supporting the narrative that the business is scaling efficiently ahead of Series A.",
        ("Finance Team", "Executive"):
            f"OpEx over ${OPEX_VAR/1e3:,.0f}K — Engineering +2 HC vs budget, offset by Ops -1 HC. Reforecast Q3 run rate: ${(ACT_OPEX*1.021)/1e3:,.0f}K/mo.",
        ("Finance Team", "Detailed"):
            f"Engineering: ${COST_ACT[0]/1e3:,.0f}K actual vs ${COST_BUD[0]/1e3:,.0f}K budget — 2 HC above plan (26 vs. 24 budgeted). "
            f"Operations: ${COST_ACT[1]/1e3:,.0f}K actual vs ${COST_BUD[1]/1e3:,.0f}K budget — 1 HC below plan, ${(COST_BUD[1]-COST_ACT[1])/1e3:.0f}K favorable. "
            f"G&A: ${COST_ACT[4]/1e3:,.0f}K vs ${COST_BUD[4]/1e3:,.0f}K — one-time legal fee for contract review. "
            f"Q3 OpEx reforecast: ${ACT_OPEX*1.021/1e3:,.0f}K/mo assuming 2.1% MoM headcount cost growth.",
    }

    _key = (_aud, _tone)
    _rev_text = _rev_narrative.get(_key, _rev_narrative[("Board", "Executive")])
    _opex_text = _opex_narrative.get(_key, _opex_narrative[("Board", "Executive")])

    st.markdown(
        f'<div style="background:linear-gradient(135deg,rgba(59,130,246,0.08) 0%,rgba(139,92,246,0.06) 100%);'
        f'border:1px solid rgba(59,130,246,0.18);border-radius:12px;padding:16px 20px;margin-bottom:16px;">'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'<span style="font-size:18px;">📋</span>'
        f'<div style="flex:1;">'
        f'<div style="font-size:13px;font-weight:700;color:#f1f5f9;">FP&A Variance Commentary — {REPORT_MONTH}</div>'
        f'<div style="font-size:11px;color:#475569;margin-top:2px;">Rules-based narrative · synthetic data · not financial advice</div>'
        f'</div>'
        f'<div style="display:flex;gap:6px;">'
        f'<span style="background:{_badge_color}22;border:1px solid {_badge_color}44;color:{_badge_color};'
        f'font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;">{_aud.upper()}</span>'
        f'<span style="background:rgba(100,116,139,0.15);border:1px solid rgba(100,116,139,0.3);color:#94a3b8;'
        f'font-size:10px;font-weight:600;padding:2px 8px;border-radius:20px;">{_tone_label.upper()}</span>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )

    for icon, label, color, bg, border, text in [
        ("📈", "REVENUE", GREEN, "rgba(16,185,129,0.08)", "rgba(16,185,129,0.22)", _rev_text),
        ("💸", "OPEX", YELLOW, "rgba(245,158,11,0.08)", "rgba(245,158,11,0.22)", _opex_text),
        ("✅", "EBITDA SUMMARY", PURPLE, "rgba(139,92,246,0.08)", "rgba(139,92,246,0.22)",
         f"Net EBITDA of ${ACT_EBITDA/1e3:,.0f}K vs. ${BUD_EBITDA/1e3:,.0f}K budget — "
         f"${EBITDA_VAR/1e3:+,.0f}K favorable. Revenue beat more than offset the OpEx timing variance. "
         f"Business is EBITDA positive two months ahead of plan. "
         + ("Series A data room should highlight this milestone." if _aud == "Investors" else
            "Recommend flagging at next board meeting as a positive inflection." if _aud == "Board" else
            "Update rolling forecast model to carry +$15K/mo EBITDA floor assumption into Q3.")),
    ]:
        st.markdown(
            f'<div style="background:{bg};border:1px solid {border};border-left:3px solid {color};'
            f'border-radius:10px;padding:14px 16px;margin-bottom:10px;">'
            f'<div style="font-size:10px;font-weight:700;letter-spacing:.07em;color:{color};margin-bottom:6px;">'
            f'{icon} {label}</div>'
            f'<div style="font-size:13px;color:#cbd5e1;line-height:1.65;">{text}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Download
    _dl_text = f"""CAREVALIDATE — FP&A VARIANCE REPORT
{REPORT_MONTH} · Audience: {_aud} · Tone: {_tone}
{'='*60}

REVENUE VARIANCE
{_rev_text}

OPEX VARIANCE
{_opex_text}

EBITDA SUMMARY
Net EBITDA ${ACT_EBITDA/1e3:,.0f}K vs. ${BUD_EBITDA/1e3:,.0f}K budget — ${EBITDA_VAR/1e3:+,.0f}K favorable.
Business is EBITDA positive two months ahead of plan.

{'='*60}
BUDGET VS. ACTUALS SUMMARY ({REPORT_MONTH})
{'='*60}
Revenue:      Budget ${BUD_MRR/1e3:,.0f}K  |  Actual ${ACT_MRR/1e3:,.0f}K  |  Variance ${REV_VAR/1e3:+,.0f}K ({REV_VAR_PCT:+.1f}%)
Gross Margin: Budget {BUD_GM/BUD_MRR:.1%}    |  Actual {ACT_GM/ACT_MRR:.1%}    |  +140bps
OpEx:         Budget ${BUD_OPEX/1e3:,.0f}K  |  Actual ${ACT_OPEX/1e3:,.0f}K  |  Variance ${OPEX_VAR/1e3:+,.0f}K ({OPEX_VAR_PCT:+.1f}%)
EBITDA:       Budget ${BUD_EBITDA/1e3:,.0f}K   |  Actual ${ACT_EBITDA/1e3:,.0f}K   |  Variance ${EBITDA_VAR/1e3:+,.0f}K

{'='*60}
DISCLAIMER
Synthetic data only. No PHI. Prototype for discussion purposes only.
Generated: {date.today().strftime('%B %d, %Y')}
"""
    st.download_button(
        label="⬇  Download FP&A Variance Report",
        data=_dl_text.encode("utf-8"),
        file_name=f"fpa_variance_{REPORT_MONTH.replace(' ', '_').lower()}.txt",
        mime="text/plain",
        key="dl_fpa_variance",
    )

st.markdown(
    '<div style="font-size:11px;color:#1e293b;margin-top:16px;">'
    'Synthetic data only · No PHI · Prototype · FP&A model for discussion purposes · '
    'Not financial, legal, or accounting advice.'
    '</div>',
    unsafe_allow_html=True,
)
