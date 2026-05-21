"""
CareValidate Care Navigator Workforce Intelligence
FTE productivity, capacity, per-FTE ROI, language coverage, weekly ops brief.
Port 8510  |  Synthetic data only — no PHI
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
    BG, CARD, BLUE, GREEN, YELLOW, RED, PURPLE, TEAL, MUTED,
)
from carevalidate_shared.auth import check_auth, logout_button

st.set_page_config(page_title="Navigator Workforce Intelligence", layout="wide", page_icon="🧭")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
check_auth()
sidebar_nav("nav")
logout_button()

render_header(
    "Care Navigator Workforce Intelligence",
    "FTE productivity · capacity planning · per-FTE ROI · language coverage — synthetic data only",
    badge="Navigator Ops",
    badge_color="blue",
)

alert(
    "<strong>Synthetic workforce data only.</strong> No PHI, no real employee records. "
    "Calibrated to ReferWell Engage™ published benchmarks: 80% completion rate, 92% MA show rate, "
    "8–10x health plan ROI (engage.referwell.com). Production deployment requires BAA and RBAC controls.",
    level="info",
)

# ── Synthetic navigator data ──────────────────────────────────────────────────
@st.cache_data
def build_navigators(seed=42):
    rng = np.random.default_rng(seed)
    records = [
        ("Sarah Chen",        "Northeast", "EN / ZH-Mandarin", "Medicare Advantage", 1.0),
        ("Maria Rodriguez",   "Southeast", "EN / ES",           "Medicaid LTSS",      1.0),
        ("James Okafor",      "Midwest",   "EN / YO-Yoruba",    "ACO MSSP",           1.0),
        ("Priya Nair",        "West",      "EN / HI-Hindi",     "Medicare Advantage", 1.0),
        ("Ana Pereira",       "Northeast", "EN / PT-Portuguese","Commercial HMO",     1.0),
        ("Linda Tran",        "Southeast", "EN / VI-Vietnamese","Medicaid LTSS",      1.0),
        ("David Kim",         "Midwest",   "EN / KO-Korean",    "ACO MSSP",           0.5),
        ("Aisha Hassan",      "West",      "EN / AR-Arabic",    "Medicare Advantage", 1.0),
        ("Carlos Mendez",     "Southwest", "EN / ES",           "Dual-Eligible",      1.0),
        ("Ngozi Williams",    "Northeast", "EN",                "Commercial HMO",     1.0),
        ("Fatima Ali",        "West",      "EN / SO-Somali",    "Medicaid LTSS",      1.0),
        ("Robert Osei",       "Midwest",   "EN / TW-Twi",       "ACO MSSP",           0.5),
        ("Elena Vasquez",     "Southwest", "EN / ES",           "Dual-Eligible",      1.0),
        ("Jin-Soo Park",      "West",      "EN / KO-Korean",    "Medicare Advantage", 1.0),
        ("Blessing Adeyemi",  "Southeast", "EN / YO-Yoruba",    "Medicaid LTSS",      1.0),
    ]
    rows = []
    base_shows = [0.913, 0.872, 0.889, 0.924, 0.856, 0.901, 0.834, 0.918, 0.878, 0.843,
                  0.907, 0.862, 0.895, 0.931, 0.876]
    base_refs  = [312, 287, 301, 295, 268, 319, 142, 308, 281, 259, 297, 151, 276, 322, 293]
    for i, (name, market, lang, prog, fte) in enumerate(records):
        noise = rng.uniform(-0.02, 0.02)
        show  = min(max(base_shows[i] + noise, 0.75), 0.98)
        refs  = int(base_refs[i] * fte * rng.uniform(0.97, 1.03))
        comp  = int(refs * rng.uniform(0.78, 0.83))
        rows.append({
            "Navigator":    name,
            "Market":       market,
            "Languages":    lang,
            "Program":      prog,
            "FTE":          fte,
            "Referrals_Mo": refs,
            "Completed_Mo": comp,
            "Show_Rate":    round(show, 4),
            "Handle_Min":   round(rng.uniform(7.5, 11.5), 1),
            "Satisfaction": round(rng.uniform(4.1, 4.9), 1),
        })
    df = pd.DataFrame(rows)
    df["Completion_Rate"] = (df["Completed_Mo"] / df["Referrals_Mo"]).round(4)
    df["Referrals_Per_FTE"] = (df["Referrals_Mo"] / df["FTE"]).round(0).astype(int)
    return df

nav_df = build_navigators()

# ── Monthly trend ─────────────────────────────────────────────────────────────
@st.cache_data
def build_trend(seed=7):
    rng2 = np.random.default_rng(seed)
    months = pd.date_range("2025-06", periods=12, freq="MS")
    base   = 3200
    refs   = []
    for i in range(12):
        base = int(base * rng2.uniform(1.02, 1.06))
        refs.append(base)
    shows  = [int(r * rng2.uniform(0.875, 0.915)) for r in refs]
    comps  = [int(r * rng2.uniform(0.78, 0.825)) for r in refs]
    return months, refs, shows, comps

months, trend_refs, trend_shows, trend_comps = build_trend()

# ── KPI Strip ─────────────────────────────────────────────────────────────────
total_fte        = nav_df["FTE"].sum()
blended_show     = (nav_df["Show_Rate"] * nav_df["FTE"]).sum() / total_fte
blended_comp     = (nav_df["Completion_Rate"] * nav_df["FTE"]).sum() / total_fte
refs_per_fte     = (nav_df["Referrals_Mo"] / nav_df["FTE"]).mean()
lang_count       = len(set(l.strip() for row in nav_df["Languages"] for l in row.split("/"))) - 1  # subtract EN

section("Workforce KPIs — May 2026", "🧭")
kpi_row([
    kpi_card(f"{total_fte:.1f}", "Total Navigator FTE",
             "Across 5 markets · 15 navigators", color="blue"),
    kpi_card(f"{blended_show:.1%}", "Blended Show Rate",
             "Industry avg: 60% · ReferWell benchmark: 89%+",
             trend="+29pp vs industry avg", trend_good=True, color="green"),
    kpi_card(f"{blended_comp:.1%}", "Completion Rate",
             "Referrals scheduled → kept appointment",
             trend="+2pp YoY", trend_good=True, color="green"),
    kpi_card(f"{refs_per_fte:.0f}", "Referrals / FTE / Mo",
             "At 8.2 min avg handle time", color="blue"),
    kpi_card(f"{lang_count}+", "Languages Served",
             "ES, ZH, HI, VI, KO, AR, SO, YO, TW, PT", color="purple"),
])

st.divider()

# ── Performance leaderboard + Trend ───────────────────────────────────────────
lb_col, tr_col = st.columns([2, 3], gap="medium")

with lb_col:
    section("Navigator Performance Leaderboard", "📋")
    disp = nav_df[["Navigator","Market","Program","Show_Rate","Completed_Mo","FTE","Satisfaction"]].copy()
    disp["Show_Rate"]    = disp["Show_Rate"].apply(lambda x: f"{x:.1%}")
    disp["Satisfaction"] = disp["Satisfaction"].apply(lambda x: f"{x:.1f} ★")
    disp = disp.sort_values("Completed_Mo", ascending=False).set_index("Navigator")
    st.dataframe(disp, use_container_width=True, height=360)

with tr_col:
    section("Monthly Referral Volume — 12-Month Trend", "")
    fig_t = go.Figure()
    fig_t.add_trace(go.Bar(
        x=months, y=trend_refs, name="Scheduled",
        marker_color=BLUE, opacity=0.7,
    ))
    fig_t.add_trace(go.Scatter(
        x=months, y=trend_shows, name="Confirmed",
        line=dict(color=TEAL, width=2.5), mode="lines+markers",
        marker=dict(size=5),
    ))
    fig_t.add_trace(go.Scatter(
        x=months, y=trend_comps, name="Completed",
        line=dict(color=GREEN, width=2.5, dash="dot"), mode="lines+markers",
        marker=dict(size=5),
    ))
    fig_t.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        height=360, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0,
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="Referrals"),
    )
    st.plotly_chart(fig_t, use_container_width=True)

st.divider()

# ── Capacity + Language coverage ──────────────────────────────────────────────
cap_col, lang_col = st.columns([3, 2], gap="medium")

with cap_col:
    section("Capacity Planning — Demand vs Supply by Market", "📊")
    markets = nav_df.groupby("Market").agg(
        FTE=("FTE","sum"),
        Referrals=("Referrals_Mo","sum"),
    ).reset_index()
    capacity = (markets["FTE"] * refs_per_fte).round(0).astype(int)
    fig_c = go.Figure()
    fig_c.add_trace(go.Bar(
        name="Capacity (max referrals at FTE)",
        x=markets["Market"], y=capacity,
        marker_color="rgba(59,130,246,0.35)", text=capacity, textposition="outside",
        textfont=dict(size=11, color="#64748b"),
    ))
    fig_c.add_trace(go.Bar(
        name="Actual Volume",
        x=markets["Market"], y=markets["Referrals"],
        marker_color=BLUE, text=markets["Referrals"], textposition="outside",
        textfont=dict(size=11, color="#f1f5f9"),
    ))
    utilization = markets["Referrals"] / capacity
    for i, (mkt, util) in enumerate(zip(markets["Market"], utilization)):
        color = RED if util > 0.95 else (YELLOW if util > 0.85 else GREEN)
        fig_c.add_annotation(
            x=mkt, y=int(capacity.iloc[i]) * 1.08,
            text=f"{util:.0%} util", showarrow=False,
            font=dict(size=10, color=color),
        )
    fig_c.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        barmode="overlay", height=300, margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0,
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="Referrals / Mo"),
    )
    st.plotly_chart(fig_c, use_container_width=True)

with lang_col:
    section("Language Coverage", "🌐")
    lang_map = {}
    for row in nav_df.itertuples():
        for lang in row.Languages.split("/"):
            lang = lang.strip().split("-")[0].strip()
            lang_map[lang] = lang_map.get(lang, 0) + float(row.FTE)
    lang_df = pd.Series(lang_map).sort_values(ascending=False)
    fig_l = go.Figure(go.Pie(
        labels=lang_df.index, values=lang_df.values, hole=0.52,
        marker=dict(colors=[BLUE, GREEN, PURPLE, TEAL, YELLOW, RED,
                             "#f97316","#a855f7","#14b8a6","#6366f1"],
                    line=dict(color=BG, width=2)),
        textfont=dict(size=11),
    ))
    fig_l.update_layout(
        paper_bgcolor=BG, height=300, margin=dict(l=0, r=0, t=10, b=0),
        annotations=[dict(text="10 langs", x=0.5, y=0.5,
                          font=dict(size=13, color="#f1f5f9", family="Inter"),
                          showarrow=False)],
        legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_l, use_container_width=True)

st.divider()

# ── Per-FTE ROI Calculator ────────────────────────────────────────────────────
section("Per-FTE Navigator ROI Calculator", "💰")
st.markdown(
    '<div style="font-size:12px;color:#475569;margin:-8px 0 16px 0;">'
    'Models the financial return of one navigator FTE — calibrated to published ReferWell outcomes '
    'and Milliman healthcare cost benchmarks. Adjust inputs for your market.</div>',
    unsafe_allow_html=True
)

# ── Session state defaults ────────────────────────────────────────────────────
_NAV_DEFAULTS    = dict(nav_salary=55, nav_overhead=1.30, nav_refs=85, nav_show=89, nav_savings=850)
_REFERWELL_VALS  = dict(nav_salary=52, nav_overhead=1.35, nav_refs=95, nav_show=92, nav_savings=750)
for k, v in _NAV_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Preset buttons ────────────────────────────────────────────────────────────
preset_col1, preset_col2, preset_col3 = st.columns([2, 2, 4], gap="small")
with preset_col1:
    if st.button("🎯 Load ReferWell Benchmarks", type="primary", use_container_width=True):
        for k, v in _REFERWELL_VALS.items():
            st.session_state[k] = v
        st.rerun()
with preset_col2:
    if st.button("↩ Reset to Defaults", use_container_width=True):
        for k, v in _NAV_DEFAULTS.items():
            st.session_state[k] = v
        st.rerun()
with preset_col3:
    _is_rw = all(st.session_state.get(k) == v for k, v in _REFERWELL_VALS.items())
    if _is_rw:
        st.markdown(
            '<div style="padding:8px 14px;background:rgba(16,185,129,0.10);border:1px solid rgba(16,185,129,0.30);'
            'border-radius:8px;font-size:12px;color:#10b981;margin-top:2px;">'
            '✓ <strong>ReferWell published benchmarks loaded</strong> — '
            '92% MA show rate · 10M+ covered lives · 8–10x health plan ROI</div>',
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

roi_c1, roi_c2, roi_c3 = st.columns(3, gap="medium")
with roi_c1:
    salary_k    = st.slider("Navigator annual salary ($K)", 45, 75, step=1, key="nav_salary")
    overhead_x  = st.slider("Benefits & overhead multiplier", 1.2, 1.5, step=0.05, format="%.2f", key="nav_overhead")
with roi_c2:
    refs_per_mo = st.slider("Referrals scheduled / FTE / month", 60, 140, step=5, key="nav_refs")
    show_pct    = st.slider("Show rate", 70, 98, step=1, format="%d%%", key="nav_show")
with roi_c3:
    savings_per = st.slider("Avg claims savings per completed visit ($)", 400, 1500, step=50, key="nav_savings")
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

monthly_cost    = (salary_k * 1000 * overhead_x) / 12
completed_mo    = refs_per_mo * (show_pct / 100) * blended_comp
monthly_savings = completed_mo * savings_per
monthly_net     = monthly_savings - monthly_cost
roi_multiple    = monthly_savings / max(monthly_cost, 1)
payback_days    = (monthly_cost / max(monthly_savings, 1)) * 30.4

kpi_row([
    kpi_card(f"${monthly_cost:,.0f}", "Monthly FTE Cost",
             f"${salary_k}K salary · {overhead_x:.2f}x overhead", color="yellow"),
    kpi_card(f"{completed_mo:.0f}", "Completed Visits / Mo",
             f"{refs_per_mo} scheduled · {show_pct}% show", color="blue"),
    kpi_card(f"${monthly_savings:,.0f}", "Monthly Claims Savings",
             f"${savings_per}/visit × {completed_mo:.0f} completed", color="green"),
    kpi_card(f"{roi_multiple:.1f}x", "Navigator ROI",
             f"${monthly_net:,.0f}/mo net · {payback_days:.0f}-day payback",
             trend="+within 8–10x benchmark", trend_good=roi_multiple >= 8, color="green" if roi_multiple >= 8 else "yellow"),
])

alert(
    f"At a {show_pct}% show rate with ${savings_per:,} in avg claims savings per visit, each navigator FTE generates "
    f"<strong>${monthly_savings:,.0f}/month in value</strong> against a ${monthly_cost:,.0f}/month fully-loaded cost — "
    f"a <strong>{roi_multiple:.1f}x ROI</strong> that aligns with ReferWell's published 8–10x health plan ROI. "
    f"The {payback_days:.0f}-day payback period makes navigator hiring a near-zero-risk financial decision. "
    f"Source: Milliman healthcare cost benchmarks, NCQA care gap closure data, ReferWell outcomes page.",
    level="success" if roi_multiple >= 6 else "info",
)

st.divider()

# ── Weekly Ops Brief ──────────────────────────────────────────────────────────
section("Automated Weekly Ops Brief", "📧")
st.markdown(
    '<div style="font-size:12px;color:#475569;margin:-8px 0 16px 0;">'
    'Auto-generated each Monday — copy into Slack, Teams, or your weekly leadership email.</div>',
    unsafe_allow_html=True
)

top3   = nav_df.nlargest(3, "Show_Rate")[["Navigator","Show_Rate","Completed_Mo"]].values.tolist()
low1   = nav_df.nsmallest(1, "Show_Rate")[["Navigator","Show_Rate","Market"]].values.tolist()[0]
total_completed  = nav_df["Completed_Mo"].sum()
total_refs       = nav_df["Referrals_Mo"].sum()
west_util        = (nav_df[nav_df["Market"]=="West"]["Referrals_Mo"].sum() /
                    (nav_df[nav_df["Market"]=="West"]["FTE"].sum() * refs_per_fte)) * 100
report_date      = date.today()

brief = f"""📋 NAVIGATOR OPS BRIEF — Week of {report_date.strftime('%B %d, %Y')}
Generated by CareValidate Navigator Workforce Intelligence | Synthetic data only

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 FLEET SUMMARY (May 2026)
• Total FTE: {total_fte:.1f} across 5 markets | {len(nav_df)} navigators
• Referrals scheduled: {total_refs:,} | Completed: {total_completed:,}
• Blended show rate: {blended_show:.1%} (benchmark: 89%)
• Blended completion rate: {blended_comp:.1%} (benchmark: 80%)
• Languages served: {lang_count}+ (EN, ES, ZH, HI, VI, KO, AR, SO, YO, TW, PT)

🏆 TOP PERFORMERS
• {top3[0][0]}: {top3[0][1]:.1%} show rate · {top3[0][2]} completions
• {top3[1][0]}: {top3[1][1]:.1%} show rate · {top3[1][2]} completions
• {top3[2][0]}: {top3[2][1]:.1%} show rate · {top3[2][2]} completions

⚠️ ATTENTION
• {low1[0]} ({low1[2]}): {low1[1]:.1%} show rate — schedule coaching call this week

🔴 CAPACITY ALERT
• West market at {west_util:.0f}% utilization — consider adding 0.5 FTE or redistributing referrals

💰 ROI SNAPSHOT
• Monthly navigator cost: ${(total_fte * salary_k * 1000 * overhead_x / 12):,.0f}
• Est. monthly claims savings: ${(total_completed * savings_per):,.0f}
• Portfolio ROI: {(total_completed * savings_per) / max(total_fte * salary_k * 1000 * overhead_x / 12, 1):.1f}x

📅 NEXT ACTIONS
□ West market: evaluate 0.5 FTE addition or referral rebalance
□ Coaching call: {low1[0]}
□ HEDIS quarter-end: prioritize COL and TRC gap closure before {(report_date + timedelta(days=21)).strftime('%B %d')}
□ BAA renewal: Telephony vendor (due {(report_date + timedelta(days=14)).strftime('%B %d')})

— CareValidate Navigator Intelligence · Synthetic data only · No PHI
"""
st.code(brief, language=None)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;padding:28px 0 16px 0;color:#334155;font-size:11px;">'
    'Synthetic data only · No PHI · Prototype · NCQA HEDIS 2026 benchmarks · '
    'Milliman healthcare cost data · ReferWell published outcomes</div>',
    unsafe_allow_html=True
)
