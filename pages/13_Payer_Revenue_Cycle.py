"""
CareValidate Payer Revenue Cycle Dashboard
Claims, denials, DSO, A/R aging, payer mix, net collection rate.
All data is synthetic — no real PHI or payment data.
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from carevalidate_shared.theme import (
    GLOBAL_CSS, render_header, kpi_card, kpi_row, section, alert, sidebar_nav,
    BG, CARD, CARD2, BORDER, BLUE, GREEN, YELLOW, RED, PURPLE, TEAL, MUTED, TEXT,
)
from carevalidate_shared.auth import check_auth, logout_button

st.set_page_config(page_title="Payer Revenue Cycle", layout="wide", page_icon="💳")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
check_auth()
sidebar_nav("payer")
logout_button()

rng = np.random.default_rng(77)

# ── Synthetic data ─────────────────────────────────────────────────────────────

PAYERS = ["UnitedHealth", "Aetna", "BCBS", "Cigna", "Humana", "Medicaid", "Medicare", "Self-Pay"]
PAYER_COLORS = [BLUE, PURPLE, TEAL, GREEN, YELLOW, "#f97316", "#ec4899", MUTED]

# Monthly collections (24 months)
months = pd.date_range("2024-01-01", periods=24, freq="MS")
base_revenue = 180_000
monthly_billed     = base_revenue + rng.integers(-15000, 30000, 24).cumsum() // 4
monthly_collected  = (monthly_billed * rng.uniform(0.83, 0.91, 24)).astype(int)
monthly_denied     = (monthly_billed * rng.uniform(0.06, 0.14, 24)).astype(int)
monthly_adjusted   = monthly_billed - monthly_collected - monthly_denied

# Payer mix — revenue share
payer_revenue = np.array([0.28, 0.17, 0.19, 0.11, 0.08, 0.06, 0.07, 0.04])
payer_revenue = (payer_revenue * monthly_collected[-1]).astype(int)

# Denial rates by payer
denial_rates = np.array([0.072, 0.091, 0.063, 0.085, 0.078, 0.148, 0.052, 0.210])

# DSO by payer (days sales outstanding)
dso_values = np.array([22, 31, 19, 28, 34, 52, 41, 67])

# A/R aging buckets
ar_buckets  = ["0–30 days", "31–60 days", "61–90 days", "91–120 days", ">120 days"]
ar_by_payer = rng.dirichlet(np.ones(5) * 2.5, size=len(PAYERS)) * payer_revenue[:, None] * 0.25
ar_by_payer = ar_by_payer.astype(int)

# Denial reason codes
denial_codes = {
    "Medical Necessity (CO-50)":  0.28,
    "Missing/Incomplete Info (CO-16)": 0.22,
    "Dup Claim (CO-18)":          0.13,
    "Coverage Terminated (CO-27)":0.11,
    "Auth Required (CO-15)":      0.09,
    "Timely Filing (CO-29)":      0.08,
    "Non-Covered Service (CO-96)":0.05,
    "Other":                      0.04,
}
total_denied_ytd = int(monthly_denied[-12:].sum())
denial_code_vals = {k: int(v * total_denied_ytd) for k, v in denial_codes.items()}

# First-pass rate trend
fpr_trend = 82 + rng.uniform(-3, 5, 24).cumsum() * 0.2
fpr_trend = np.clip(fpr_trend, 76, 93)

# ── Sidebar filters ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown(
        '<div style="font-size:11px;color:#64748b;font-weight:600;letter-spacing:.06em;margin-bottom:6px;">FILTERS</div>',
        unsafe_allow_html=True,
    )
    selected_payers = st.multiselect(
        "Payers", PAYERS, default=PAYERS, key="payer_filter"
    )
    ar_view = st.selectbox("A/R View", ["All Payers", "By Payer"], key="ar_view")
    show_targets = st.checkbox("Show industry targets", value=True, key="show_targets")

payer_mask = [p in selected_payers for p in PAYERS]
sel_idx    = [i for i, m in enumerate(payer_mask) if m]

# ── Header ─────────────────────────────────────────────────────────────────
render_header(
    "💳 Payer Revenue Cycle",
    "Claims management, denial tracking, A/R aging, and net collection rate by payer",
)

# ── KPI Row ────────────────────────────────────────────────────────────────
total_billed_ytd    = int(monthly_billed[-12:].sum())
total_collected_ytd = int(monthly_collected[-12:].sum())
total_denied_ytd    = int(monthly_denied[-12:].sum())
ncr                 = total_collected_ytd / total_billed_ytd
avg_dso             = int(np.average(dso_values, weights=payer_revenue))
fpr_now             = float(fpr_trend[-1])
avg_denial          = total_denied_ytd / total_billed_ytd

kpi_row([
    kpi_card("YTD Billed",          f"${total_billed_ytd/1e6:.2f}M", color="blue",   delta="+11% YoY"),
    kpi_card("YTD Collected",       f"${total_collected_ytd/1e6:.2f}M", color="green",  delta="+8% YoY"),
    kpi_card("Net Collection Rate", f"{ncr:.1%}",                    color="green",  delta="+1.4pp YoY"),
    kpi_card("Avg Denial Rate",     f"{avg_denial:.1%}",             color="yellow", delta="-0.8pp YoY"),
    kpi_card("Weighted Avg DSO",    f"{avg_dso}d",                   color="purple", delta="-3d YoY"),
    kpi_card("First-Pass Rate",     f"{fpr_now:.1f}%",               color="teal",   delta="+2.1pp YoY"),
])

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Row 1: Monthly collections trend + First-pass rate ─────────────────────
col1, col2 = st.columns([3, 2], gap="medium")

with col1:
    section("Monthly Collections Trend")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=months, y=monthly_billed,
        name="Billed", marker_color="rgba(59,130,246,0.25)",
        hovertemplate="Billed: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=months, y=monthly_collected,
        name="Collected", marker_color=GREEN,
        hovertemplate="Collected: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=months, y=monthly_denied,
        name="Denied", marker_color=RED,
        hovertemplate="Denied: $%{y:,.0f}<extra></extra>",
    ))
    if show_targets:
        target_ncr_line = monthly_billed * 0.90
        fig.add_trace(go.Scatter(
            x=months, y=target_ncr_line,
            name="90% NCR Target", mode="lines",
            line=dict(color=YELLOW, width=1.5, dash="dot"),
            hovertemplate="Target: $%{y:,.0f}<extra></extra>",
        ))
    fig.update_layout(
        barmode="overlay",
        plot_bgcolor=CARD, paper_bgcolor=CARD,
        font=dict(family="Inter", color=MUTED, size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="transparent", font=dict(size=11)),
        margin=dict(l=0, r=0, t=28, b=0),
        height=280,
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickprefix="$", tickformat=".2s", tickfont=dict(size=10)),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    section("First-Pass Rate (FPR) Trend")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=months, y=fpr_trend,
        mode="lines+markers",
        line=dict(color=TEAL, width=2.5),
        marker=dict(size=4, color=TEAL),
        fill="tozeroy",
        fillcolor="rgba(6,182,212,0.08)",
        name="FPR %",
        hovertemplate="%{y:.1f}%<extra></extra>",
    ))
    if show_targets:
        fig2.add_hline(y=90, line_dash="dot", line_color=GREEN, line_width=1.2,
                       annotation_text="Target 90%", annotation_font_color=GREEN,
                       annotation_font_size=10)
    fig2.update_layout(
        plot_bgcolor=CARD, paper_bgcolor=CARD,
        font=dict(family="Inter", color=MUTED, size=11),
        showlegend=False,
        margin=dict(l=0, r=0, t=28, b=0),
        height=280,
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", ticksuffix="%",
                   range=[70, 100], tickfont=dict(size=10)),
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Row 2: Payer mix + Denial rate by payer ────────────────────────────────
col3, col4 = st.columns([2, 3], gap="medium")

with col3:
    section("Payer Revenue Mix")
    sel_rev   = [payer_revenue[i] for i in sel_idx]
    sel_names = [PAYERS[i]        for i in sel_idx]
    sel_cols  = [PAYER_COLORS[i]  for i in sel_idx]
    fig3 = go.Figure(go.Pie(
        labels=sel_names, values=sel_rev,
        marker=dict(colors=sel_cols, line=dict(color=CARD, width=2)),
        textinfo="label+percent",
        textfont=dict(size=11, family="Inter"),
        hole=0.52,
        hovertemplate="%{label}: $%{value:,.0f}<extra></extra>",
    ))
    fig3.add_annotation(
        text=f"${sum(sel_rev)/1e3:.0f}K<br><span style='font-size:10px'>collected/mo</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=13, color=TEXT, family="Inter"),
    )
    fig3.update_layout(
        plot_bgcolor=CARD, paper_bgcolor=CARD,
        margin=dict(l=0, r=0, t=28, b=0),
        height=280,
        showlegend=False,
        font=dict(family="Inter", color=MUTED),
    )
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with col4:
    section("Denial Rate & DSO by Payer")
    sel_payers_names = [PAYERS[i]       for i in sel_idx]
    sel_denial       = [denial_rates[i] for i in sel_idx]
    sel_dso          = [dso_values[i]   for i in sel_idx]
    sel_bar_cols     = [RED if d > 0.10 else YELLOW if d > 0.07 else GREEN for d in sel_denial]

    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=sel_payers_names, y=[d * 100 for d in sel_denial],
        name="Denial Rate %",
        marker_color=sel_bar_cols,
        text=[f"{d:.1%}" for d in sel_denial],
        textposition="outside",
        textfont=dict(size=10),
        hovertemplate="%{x}<br>Denial: %{y:.1f}%<extra></extra>",
        yaxis="y",
    ))
    fig4.add_trace(go.Scatter(
        x=sel_payers_names, y=sel_dso,
        name="DSO (days)",
        mode="lines+markers",
        line=dict(color=PURPLE, width=2),
        marker=dict(size=6, color=PURPLE),
        hovertemplate="%{x}<br>DSO: %{y}d<extra></extra>",
        yaxis="y2",
    ))
    if show_targets:
        fig4.add_hline(y=8, line_dash="dot", line_color=GREEN, line_width=1,
                       annotation_text="8% target", annotation_font_color=GREEN,
                       annotation_font_size=9, yref="y")
    fig4.update_layout(
        plot_bgcolor=CARD, paper_bgcolor=CARD,
        font=dict(family="Inter", color=MUTED, size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="transparent", font=dict(size=11)),
        margin=dict(l=0, r=0, t=36, b=0),
        height=280,
        yaxis=dict(title="Denial Rate %", gridcolor="rgba(255,255,255,0.04)",
                   ticksuffix="%", tickfont=dict(size=10), titlefont=dict(size=11)),
        yaxis2=dict(title="DSO (days)", overlaying="y", side="right",
                    tickfont=dict(size=10), titlefont=dict(size=11), showgrid=False),
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
    )
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Row 3: A/R Aging + Denial Reason Codes ─────────────────────────────────
col5, col6 = st.columns([3, 2], gap="medium")

with col5:
    section("A/R Aging by Payer")
    ar_colors = [GREEN, TEAL, YELLOW, "#f97316", RED]
    fig5 = go.Figure()
    for b_idx, bucket in enumerate(ar_buckets):
        vals = [ar_by_payer[i, b_idx] for i in sel_idx]
        fig5.add_trace(go.Bar(
            x=sel_payers_names, y=vals,
            name=bucket,
            marker_color=ar_colors[b_idx],
            hovertemplate=f"{bucket}: $%{{y:,.0f}}<extra></extra>",
        ))
    fig5.update_layout(
        barmode="stack",
        plot_bgcolor=CARD, paper_bgcolor=CARD,
        font=dict(family="Inter", color=MUTED, size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="transparent", font=dict(size=11)),
        margin=dict(l=0, r=0, t=36, b=0),
        height=280,
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickprefix="$", tickformat=".2s",
                   tickfont=dict(size=10)),
    )
    st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})

with col6:
    section("Top Denial Reason Codes (YTD)")
    dc_labels = list(denial_code_vals.keys())
    dc_vals   = list(denial_code_vals.values())
    dc_colors_grad = [
        f"rgba(239,68,68,{0.9 - i*0.09})" for i in range(len(dc_labels))
    ]
    fig6 = go.Figure(go.Bar(
        x=dc_vals,
        y=dc_labels,
        orientation="h",
        marker=dict(color=dc_colors_grad),
        text=[f"${v:,.0f}" for v in dc_vals],
        textposition="inside",
        textfont=dict(size=10, color="#fff"),
        hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
    ))
    fig6.update_layout(
        plot_bgcolor=CARD, paper_bgcolor=CARD,
        font=dict(family="Inter", color=MUTED, size=11),
        showlegend=False,
        margin=dict(l=0, r=0, t=28, b=0),
        height=280,
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickprefix="$", tickformat=".2s",
                   tickfont=dict(size=10)),
        yaxis=dict(showgrid=False, tickfont=dict(size=10), autorange="reversed"),
    )
    st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Payer Scorecard Table ───────────────────────────────────────────────────
section("Payer Scorecard")

scorecard_rows = []
for i in sel_idx:
    ncr_p   = 1 - denial_rates[i] - rng.uniform(0.02, 0.06)
    status  = "✅ On Target" if denial_rates[i] < 0.08 and dso_values[i] < 35 else \
              "⚠️ Watch"    if denial_rates[i] < 0.12 and dso_values[i] < 50 else \
              "🔴 Action Required"
    scorecard_rows.append({
        "Payer":              PAYERS[i],
        "YTD Revenue":        f"${payer_revenue[i]:,.0f}",
        "Denial Rate":        f"{denial_rates[i]:.1%}",
        "First-Pass Rate":    f"{(1-denial_rates[i]*0.7):.1%}",
        "Net Collection Rate":f"{ncr_p:.1%}",
        "Avg DSO":            f"{dso_values[i]}d",
        "A/R >90d":           f"${(ar_by_payer[i, 3] + ar_by_payer[i, 4]):,.0f}",
        "Status":             status,
    })

df_scorecard = pd.DataFrame(scorecard_rows)

st.markdown(
    f'<div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;'
    f'padding:0;overflow:hidden;margin-bottom:8px;">',
    unsafe_allow_html=True,
)
st.dataframe(df_scorecard, use_container_width=True, hide_index=True, height=min(40 + len(scorecard_rows) * 36, 340))
st.markdown("</div>", unsafe_allow_html=True)

# download
csv_bytes = df_scorecard.to_csv(index=False).encode()
st.download_button(
    label="⬇ Download Payer Scorecard CSV",
    data=csv_bytes,
    file_name="payer_scorecard.csv",
    mime="text/csv",
    key="dl_scorecard",
)

# ── Alert rail ─────────────────────────────────────────────────────────────
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

high_denial_payers = [PAYERS[i] for i in sel_idx if denial_rates[i] > 0.10]
high_dso_payers    = [PAYERS[i] for i in sel_idx if dso_values[i] > 40]

if high_denial_payers:
    alert(f"High denial rate: {', '.join(high_denial_payers)} — denial rate exceeds 10% threshold. Review auth requirements and coding accuracy.", level="warning")

if high_dso_payers:
    alert(f"Elevated DSO: {', '.join(high_dso_payers)} — average days to payment exceeds 40-day benchmark. Escalate follow-up workflow.", level="error")

if ncr < 0.86:
    alert("Net collection rate below 86% — industry benchmark for care navigation is 88–92%. Review write-off policy and payer contract terms.", level="error")
else:
    alert(f"Net collection rate {ncr:.1%} is within target range (88–92% benchmark). First-pass approval rate trending upward.", level="success")

st.markdown(
    '<div style="margin-top:24px;font-size:11px;color:#334155;text-align:center;">'
    'Synthetic data only — no real payer, patient, or payment information. '
    'Denial rate benchmarks: MGMA 2024. DSO benchmarks: HFMA 2024.'
    '</div>',
    unsafe_allow_html=True,
)
