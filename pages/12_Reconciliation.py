"""
CareValidate — Intelligent Payment Reconciliation Engine
Port 8512 | Synthetic data only | HIPAA Safe Harbor
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

from carevalidate_shared.theme import (
    GLOBAL_CSS, render_header, kpi_card, kpi_row, section, alert, sidebar_nav,
    BG, CARD, BLUE, GREEN, YELLOW, RED, PURPLE, TEAL, MUTED,
)

# ── Page config (must be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="CareValidate · Reconciliation",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
sidebar_nav("recon")

# ── Plotly base layout ───────────────────────────────────────────────────────
_PLOT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, system-ui, sans-serif", color="#94a3b8", size=12),
    margin=dict(l=8, r=8, t=32, b=8),
)

_LEGEND_BASE = dict(
    bgcolor="rgba(0,0,0,0)",
    bordercolor="rgba(255,255,255,0.07)",
    borderwidth=1,
    font=dict(size=11, color="#94a3b8"),
)

_AXIS_STYLE = dict(
    gridcolor="rgba(255,255,255,0.05)",
    linecolor="rgba(255,255,255,0.07)",
    tickfont=dict(size=11, color="#64748b"),
    showgrid=True,
    zeroline=False,
)

# ── Synthetic data ───────────────────────────────────────────────────────────
@st.cache_data
def generate_transactions() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 480
    today = pd.Timestamp("2026-05-20")
    start = today - pd.Timedelta(days=29)
    dates = pd.to_datetime(
        rng.choice(pd.date_range(start, today, freq="D"), size=n, replace=True)
    )

    payer_map = {
        "Employer PMPM":        ["HealthJoy Enterprise", "AccommoCare-A", "AccommoCare-B", "CareGLP Direct", "CareHRT Direct"],
        "Patient Subscription": ["CareGLP Direct", "CareHRT Direct", "White-Label Partner A", "White-Label Partner B"],
        "Pharmacy Outbound":    ["Compounding Pharma B", "Specialty Pharma A"],
        "Lab Outbound":         ["Lab Vendor C"],
        "Platform Fee Inbound": ["HealthJoy Enterprise", "AccommoCare-A", "AccommoCare-B"],
        "White-Label Fee":      ["White-Label Partner A", "White-Label Partner B"],
        "Payroll Outbound":     ["Navigator Payroll"],
        "Infrastructure":       ["Cloud Infra (AWS)"],
    }

    category_weights = [0.22, 0.20, 0.14, 0.10, 0.12, 0.08, 0.08, 0.06]
    categories = rng.choice(list(payer_map.keys()), size=n, p=category_weights)

    payers = [rng.choice(payer_map[c]) for c in categories]

    direction_map = {
        "Employer PMPM":        "Inbound",
        "Patient Subscription": "Inbound",
        "Pharmacy Outbound":    "Outbound",
        "Lab Outbound":         "Outbound",
        "Platform Fee Inbound": "Inbound",
        "White-Label Fee":      "Inbound",
        "Payroll Outbound":     "Outbound",
        "Infrastructure":       "Outbound",
    }
    directions = [direction_map[c] for c in categories]

    # Expected amounts by category
    def expected_amount(cat, payer, r):
        if cat == "Employer PMPM":
            lookup = {
                "HealthJoy Enterprise": 4_200_000,
                "AccommoCare-A":        1_850_000,
                "AccommoCare-B":        2_100_000,
                "CareGLP Direct":       980_000,
                "CareHRT Direct":       760_000,
            }
            base = lookup.get(payer, 800_000)
            return base + r.integers(-50_000, 50_001)
        elif cat == "Patient Subscription":
            return 285.0
        elif cat == "Pharmacy Outbound":
            return float(r.integers(780, 901))
        elif cat == "Lab Outbound":
            return float(r.integers(45, 181))
        elif cat == "Platform Fee Inbound":
            return float(r.integers(6800, 12001))
        elif cat == "White-Label Fee":
            return float(r.integers(8500, 12001))
        elif cat == "Payroll Outbound":
            return float(r.integers(85000, 145001))
        elif cat == "Infrastructure":
            return float(r.integers(12000, 28001))
        return 1000.0

    expected = np.array([expected_amount(c, p, rng) for c, p in zip(categories, payers)], dtype=float)

    # Status assignment: 84% matched, 5% discrepancy, 2% duplicate, 2% failed, 7% pending
    probs = [0.84, 0.05, 0.02, 0.02, 0.07]
    raw_status = rng.choice(
        ["MATCHED", "DISCREPANCY", "DUPLICATE", "FAILED", "PENDING"],
        size=n, p=probs
    )

    actual = expected.copy()
    discrepancy_amt = np.zeros(n)

    for i in range(n):
        s = raw_status[i]
        if s == "DISCREPANCY":
            pct = rng.uniform(0.01, 0.12)
            sign = rng.choice([-1, 1])
            actual[i] = expected[i] * (1 + sign * pct)
            discrepancy_amt[i] = actual[i] - expected[i]
        elif s == "DUPLICATE":
            # exact repeat — same as expected (simulating a re-submission)
            actual[i] = expected[i]
            discrepancy_amt[i] = expected[i]  # full amount is the "exposure"
        elif s == "FAILED":
            actual[i] = 0.0
            discrepancy_amt[i] = -expected[i]
        elif s == "PENDING":
            actual[i] = np.nan
            discrepancy_amt[i] = np.nan
        # MATCHED: actual == expected, discrepancy_amt stays 0

    discrepancy_pct = np.where(
        raw_status == "PENDING",
        np.nan,
        np.where(expected != 0, np.abs(discrepancy_amt) / expected, 0.0),
    )

    days_outstanding = np.where(
        raw_status == "PENDING",
        rng.integers(1, 29, size=n),
        0,
    ).astype(float)
    days_outstanding[days_outstanding == 0] = np.nan

    confidence = rng.uniform(0.88, 0.99, size=n)

    # Priority
    priority = []
    for i in range(n):
        s = raw_status[i]
        d = discrepancy_amt[i] if not np.isnan(discrepancy_amt[i]) else 0
        if (abs(d) > 10_000 and s == "DISCREPANCY") or s in ("DUPLICATE", "FAILED"):
            priority.append("HIGH")
        elif (abs(d) >= 1_000 and s == "DISCREPANCY") or (
            s == "PENDING" and not np.isnan(days_outstanding[i]) and days_outstanding[i] > 14
        ):
            priority.append("MED")
        else:
            priority.append("LOW")

    tx_ids = [f"TX-{i+1:05d}" for i in range(n)]

    df = pd.DataFrame({
        "TxID":             tx_ids,
        "Date":             dates,
        "Payer_Vendor":     payers,
        "Category":         categories,
        "Direction":        directions,
        "Expected_Amount":  expected,
        "Actual_Amount":    actual,
        "Status":           raw_status,
        "Discrepancy_Amt":  discrepancy_amt,
        "Discrepancy_Pct":  discrepancy_pct,
        "Days_Outstanding": days_outstanding,
        "AI_Category":      categories,
        "Confidence":       confidence,
        "Priority":         priority,
    })

    df["Date"] = pd.to_datetime(df["Date"])
    df.sort_values("Date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


@st.cache_data
def compute_daily_stats(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    df2["DateOnly"] = df2["Date"].dt.date
    grouped = df2.groupby(["DateOnly", "Status"]).size().unstack(fill_value=0).reset_index()
    for col in ["MATCHED", "DISCREPANCY", "DUPLICATE", "FAILED", "PENDING"]:
        if col not in grouped.columns:
            grouped[col] = 0
    grouped["Total"] = grouped[["MATCHED", "DISCREPANCY", "DUPLICATE", "FAILED", "PENDING"]].sum(axis=1)
    grouped["MatchRate"] = np.where(
        (grouped["Total"] - grouped["PENDING"]) > 0,
        100.0 * grouped["MATCHED"] / (grouped["Total"] - grouped["PENDING"]),
        0.0,
    )
    return grouped


@st.cache_data
def compute_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cat, grp in df.dropna(subset=["Actual_Amount"]).groupby("Category"):
        vals = grp["Actual_Amount"]
        q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
        iqr = q3 - q1
        median = vals.median()
        std = vals.std() if vals.std() > 0 else 1.0
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        for idx, row in grp.iterrows():
            z = (row["Actual_Amount"] - median) / std
            iqr_flag = row["Actual_Amount"] < lower or row["Actual_Amount"] > upper
            severity = "HIGH" if abs(z) > 2.5 else ("MED" if abs(z) > 1.5 else "LOW")
            rows.append({
                "TxID":      row["TxID"],
                "Vendor":    row["Payer_Vendor"],
                "Category":  cat,
                "Amount":    row["Actual_Amount"],
                "Cat_Median": median,
                "Z_Score":   z,
                "IQR_Flag":  iqr_flag,
                "Severity":  severity,
                "Date":      row["Date"],
            })
    return pd.DataFrame(rows)


# ── Helpers ──────────────────────────────────────────────────────────────────
def fmt_dollar(v) -> str:
    if pd.isna(v):
        return "—"
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"${v:,.0f}"
    return f"${v:.2f}"


def fmt_dollar_full(v) -> str:
    if pd.isna(v):
        return "—"
    sign = "-" if v < 0 else ""
    return f"{sign}${abs(v):,.2f}"


def fmt_signed(v) -> str:
    if pd.isna(v):
        return "—"
    sign = "+" if v > 0 else ""
    return f"{sign}${v:,.2f}"


STATUS_COLORS = {
    "MATCHED":     GREEN,
    "DISCREPANCY": YELLOW,
    "DUPLICATE":   PURPLE,
    "FAILED":      RED,
    "PENDING":     MUTED,
}

PRIORITY_COLORS = {"HIGH": RED, "MED": YELLOW, "LOW": GREEN}

CAT_PALETTE = [BLUE, GREEN, YELLOW, RED, PURPLE, TEAL, "#f97316", "#ec4899"]


# ── Main ─────────────────────────────────────────────────────────────────────
render_header(
    "Intelligent Payment Reconciliation Engine",
    "Auto-match · discrepancy detection · duplicate flagging · exception queue · anomaly detection",
    badge="Reconciliation",
    badge_color="blue",
)

df = generate_transactions()
daily = compute_daily_stats(df)
anomaly_df = compute_anomalies(df)
today = pd.Timestamp("2026-05-20")

# Pre-compute globals
non_pending = df[df["Status"] != "PENDING"]
matched_ct = (df["Status"] == "MATCHED").sum()
match_rate = 100.0 * matched_ct / max(len(non_pending), 1)
disc_df = df[df["Status"] == "DISCREPANCY"]
total_disc_value = disc_df["Discrepancy_Amt"].abs().sum()
open_exceptions = ((df["Status"].isin(["DISCREPANCY", "DUPLICATE", "FAILED"])) |
                   ((df["Status"] == "PENDING") & (df["Days_Outstanding"] > 14))).sum()
categories_list = sorted(df["Category"].unique().tolist())
payers_list = sorted(df["Payer_Vendor"].unique().tolist())
statuses_list = ["MATCHED", "DISCREPANCY", "DUPLICATE", "FAILED", "PENDING"]

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 BI Overview",
    "📋 Transaction Ledger",
    "🔍 Discrepancy Analysis",
    "📥 Exception Queue",
    "🤖 Anomaly Detection",
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — BI Overview
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    kpi_row([
        kpi_card(f"{len(df):,}", "Total Transactions", "480 tx · 30 days", color="blue"),
        kpi_card(f"{match_rate:.1f}%", "Match Rate", "Excl. pending",
                 trend="+2.1% vs prior period", trend_good=True, color="green"),
        kpi_card(fmt_dollar(total_disc_value), "Total Discrepancy Value",
                 f"{len(disc_df)} discrepant tx", color="yellow"),
        kpi_card(f"{open_exceptions:,}", "Open Exceptions",
                 "Requiring human review", color="red"),
        kpi_card("2.3 days", "Avg Days to Resolve",
                 "Vs. 4.1 days industry avg", trend="-44% vs benchmark", trend_good=True, color="teal"),
    ])

    # ── Charts row 1 ────────────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        section("Daily Transaction Volume by Status", "📅")
        # Stacked bar
        fig_vol = go.Figure()
        status_cfg = [
            ("MATCHED",     GREEN,  "Matched"),
            ("DISCREPANCY", YELLOW, "Discrepancy"),
            ("DUPLICATE",   PURPLE, "Duplicate"),
            ("FAILED",      RED,    "Failed"),
            ("PENDING",     MUTED,  "Pending"),
        ]
        x_dates = daily["DateOnly"].astype(str).tolist()
        for col_name, color, label in status_cfg:
            fig_vol.add_trace(go.Bar(
                x=x_dates,
                y=daily[col_name],
                name=label,
                marker_color=color,
                marker_line_width=0,
                hovertemplate=f"<b>{label}</b><br>Date: %{{x}}<br>Count: %{{y}}<extra></extra>",
            ))
        fig_vol.update_layout(
            **_PLOT_BASE,
            barmode="stack",
            height=300,
            xaxis=dict(**_AXIS_STYLE, title="", tickangle=-30, dtick=4),
            yaxis=dict(**_AXIS_STYLE, title="Transaction Count"),
            legend=dict(**_LEGEND_BASE, orientation="h", x=0, y=1.12),
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    with col_right:
        section("Transaction Count by Category", "🥧")
        cat_counts = df.groupby("Category").size().reset_index(name="Count")
        fig_donut = go.Figure(go.Pie(
            labels=cat_counts["Category"],
            values=cat_counts["Count"],
            hole=0.58,
            marker=dict(colors=CAT_PALETTE, line=dict(color="#07090f", width=2)),
            textinfo="percent",
            textfont=dict(size=11, color="#f1f5f9"),
            hovertemplate="<b>%{label}</b><br>%{value} transactions<br>%{percent}<extra></extra>",
        ))
        fig_donut.update_layout(
            **_PLOT_BASE,
            height=300,
            legend=dict(**_LEGEND_BASE, orientation="v", x=1.0, y=0.5),
            annotations=[dict(
                text=f"<b>{len(df)}</b><br>Total",
                x=0.5, y=0.5, font_size=13, font_color="#f1f5f9",
                showarrow=False,
            )],
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # ── Match rate trend ─────────────────────────────────────────────────────
    section("30-Day Match Rate Trend", "📈")
    rng2 = np.random.default_rng(99)
    # Blend actual daily rate with a natural-looking 82-91% band
    trend_rates = np.clip(
        daily["MatchRate"].values + rng2.normal(0, 1.5, len(daily)),
        82, 91
    )
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=daily["DateOnly"].astype(str),
        y=trend_rates,
        mode="lines+markers",
        line=dict(color=BLUE, width=2.5, shape="spline"),
        marker=dict(size=5, color=BLUE, symbol="circle"),
        fill="tozeroy",
        fillcolor="rgba(59,130,246,0.07)",
        name="Match Rate",
        hovertemplate="<b>%{x}</b><br>Match Rate: %{y:.1f}%<extra></extra>",
    ))
    fig_trend.add_hline(y=85, line_dash="dash", line_color=GREEN, line_width=1,
                         annotation_text="85% target", annotation_font_color=GREEN,
                         annotation_font_size=11)
    fig_trend.update_layout(
        **_PLOT_BASE,
        height=220,
        xaxis=dict(**_AXIS_STYLE, title="", tickangle=-30, dtick=5),
        yaxis=dict(**_AXIS_STYLE, title="Match Rate", ticksuffix="%", range=[75, 95]),
        showlegend=False,
    )
    st.plotly_chart(fig_trend, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — Transaction Ledger
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    section("Transaction Ledger — Full Payment Register", "📋")

    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    with c1:
        sel_status = st.multiselect("Status", statuses_list, default=statuses_list, key="l_status")
    with c2:
        sel_cat = st.multiselect("Category", categories_list, default=categories_list, key="l_cat")
    with c3:
        sel_dir = st.multiselect("Direction", ["Inbound", "Outbound"], default=["Inbound", "Outbound"], key="l_dir")
    with c4:
        date_window = st.radio("Date Range", ["7 days", "14 days", "30 days"], index=2, key="l_date")

    window = int(date_window.split()[0])
    cutoff = today - pd.Timedelta(days=window - 1)

    mask = (
        df["Status"].isin(sel_status) &
        df["Category"].isin(sel_cat) &
        df["Direction"].isin(sel_dir) &
        (df["Date"] >= cutoff)
    )
    filtered = df[mask].copy()

    display = filtered[["TxID", "Date", "Payer_Vendor", "Category", "Direction",
                         "Expected_Amount", "Actual_Amount", "Discrepancy_Amt",
                         "Status", "Priority"]].copy()
    display["Date"] = display["Date"].dt.strftime("%Y-%m-%d")
    display["Expected_Amount"] = display["Expected_Amount"].apply(fmt_dollar_full)
    display["Actual_Amount"]   = display["Actual_Amount"].apply(fmt_dollar_full)
    display["Discrepancy_Amt"] = display["Discrepancy_Amt"].apply(fmt_signed)
    display.columns = ["Tx ID", "Date", "Payer / Vendor", "Category", "Direction",
                        "Expected ($)", "Actual ($)", "Gap ($)", "Status", "Priority"]

    st.dataframe(display, height=420, use_container_width=True)
    st.caption(f"Showing {len(filtered):,} of {len(df):,} transactions · {date_window} window")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — Discrepancy Analysis
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    disc_only = df[df["Status"] == "DISCREPANCY"].copy()
    if len(disc_only) > 0:
        largest_idx = disc_only["Discrepancy_Amt"].abs().idxmax()
        largest_row = disc_only.loc[largest_idx]
        largest_label = f"{fmt_dollar(abs(largest_row['Discrepancy_Amt']))} · {largest_row['Payer_Vendor']}"
        pct_revenue = 100.0 * disc_only["Discrepancy_Amt"].abs().sum() / max(
            df[df["Direction"] == "Inbound"]["Expected_Amount"].sum(), 1
        )
    else:
        largest_label = "—"
        pct_revenue = 0.0

    kpi_row([
        kpi_card(fmt_dollar(total_disc_value), "Total Discrepancy Value",
                 "Abs. value across all discrepant tx", color="yellow"),
        kpi_card(f"{len(disc_only):,}", "Discrepancy Count",
                 f"{100*len(disc_only)/max(len(df),1):.1f}% of transactions", color="red"),
        kpi_card(largest_label, "Largest Single Discrepancy",
                 "Top exposure item", color="red"),
        kpi_card(f"{pct_revenue:.2f}%", "% Revenue Affected",
                 "Inbound revenue base", color="yellow"),
    ])

    col_l, col_r = st.columns([3, 2])

    with col_l:
        section("Discrepancy Exposure by Vendor (Top 8)", "🏢")
        vendor_disc = (
            disc_only.groupby("Payer_Vendor")["Discrepancy_Amt"]
            .apply(lambda x: x.abs().sum())
            .reset_index()
            .sort_values("Discrepancy_Amt", ascending=False)
            .head(8)
        )
        colors_bar = [RED if v > 0 else YELLOW for v in vendor_disc["Discrepancy_Amt"]]
        fig_vbar = go.Figure(go.Bar(
            x=vendor_disc["Discrepancy_Amt"],
            y=vendor_disc["Payer_Vendor"],
            orientation="h",
            marker=dict(color=YELLOW, line=dict(width=0)),
            text=[fmt_dollar(v) for v in vendor_disc["Discrepancy_Amt"]],
            textposition="outside",
            textfont=dict(size=11, color="#94a3b8"),
            hovertemplate="<b>%{y}</b><br>Exposure: %{x:$,.0f}<extra></extra>",
        ))
        fig_vbar.update_layout(
            **_PLOT_BASE,
            height=310,
            showlegend=False,
            xaxis=dict(**_AXIS_STYLE, title="Discrepancy ($)"),
            yaxis=dict(**_AXIS_STYLE, title="", autorange="reversed"),
        )
        st.plotly_chart(fig_vbar, use_container_width=True)

    with col_r:
        section("Discrepancy Root-Cause Mix", "🔎")
        rng3 = np.random.default_rng(7)
        root_causes = ["Over-Billing", "Under-Billing", "Rate Mismatch", "Units Error"]
        root_assigned = rng3.choice(root_causes, size=len(disc_only),
                                     p=[0.35, 0.28, 0.22, 0.15])
        disc_only = disc_only.copy()
        disc_only["Root_Cause"] = root_assigned
        rc_summary = disc_only.groupby("Root_Cause")["Discrepancy_Amt"].agg(
            Total=lambda x: x.abs().sum(),
            Count="count"
        ).reset_index().sort_values("Total", ascending=True)

        fig_wf = go.Figure(go.Bar(
            x=rc_summary["Total"],
            y=rc_summary["Root_Cause"],
            orientation="h",
            marker=dict(
                color=[RED, YELLOW, PURPLE, TEAL][:len(rc_summary)],
                line=dict(width=0),
            ),
            text=[f"${v:,.0f}  ({c} tx)" for v, c in
                  zip(rc_summary["Total"], rc_summary["Count"])],
            textposition="outside",
            textfont=dict(size=10, color="#94a3b8"),
            hovertemplate="<b>%{y}</b><br>Exposure: %{x:$,.0f}<extra></extra>",
        ))
        fig_wf.update_layout(
            **_PLOT_BASE,
            height=310,
            showlegend=False,
            xaxis=dict(**_AXIS_STYLE, title="Total Exposure ($)"),
            yaxis=dict(**_AXIS_STYLE, title=""),
        )
        st.plotly_chart(fig_wf, use_container_width=True)

    # ── Discrepancy detail table ─────────────────────────────────────────────
    section("Discrepancy Detail — Recommended Actions", "⚡")
    action_pool = [
        "Verify contract rate", "Request credit memo", "Escalate to Finance",
        "Audit unit count", "Submit variance report", "Cross-check EOB",
        "Reconcile with EHR billing", "Flag for CFO review",
    ]
    rng4 = np.random.default_rng(13)
    disc_display = disc_only[["TxID", "Date", "Payer_Vendor", "Category",
                               "Expected_Amount", "Actual_Amount",
                               "Discrepancy_Amt", "Discrepancy_Pct", "Priority"]].copy()
    disc_display["Action"] = rng4.choice(action_pool, size=len(disc_display))
    disc_display["Date"] = disc_display["Date"].dt.strftime("%Y-%m-%d")
    disc_display["Expected_Amount"]  = disc_display["Expected_Amount"].apply(fmt_dollar_full)
    disc_display["Actual_Amount"]    = disc_display["Actual_Amount"].apply(fmt_dollar_full)
    disc_display["Discrepancy_Amt"]  = disc_display["Discrepancy_Amt"].apply(fmt_signed)
    disc_display["Discrepancy_Pct"]  = disc_display["Discrepancy_Pct"].apply(
        lambda x: f"{x*100:.1f}%" if not pd.isna(x) else "—"
    )
    disc_display.columns = ["Tx ID", "Date", "Vendor", "Category",
                              "Expected ($)", "Actual ($)", "Gap ($)",
                              "% Dev", "Priority", "Recommended Action"]
    st.dataframe(disc_display, height=360, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — Exception Queue
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    section("Prioritized Exception Queue — Items Requiring Human Review", "📥")

    # Build exception rows: DISCREPANCY + DUPLICATE + FAILED + PENDING>14 days
    exc_mask = (
        df["Status"].isin(["DISCREPANCY", "DUPLICATE", "FAILED"]) |
        ((df["Status"] == "PENDING") & (df["Days_Outstanding"] > 14))
    )
    exc_df = df[exc_mask].copy()

    high_ct = (exc_df["Priority"] == "HIGH").sum()
    alert(
        f"<b>{high_ct} HIGH priority exceptions</b> currently open · "
        f"Estimated resolution time: <b>{high_ct * 45:,} minutes</b> at 45 min avg · "
        f"Assign to available team members before EOD.",
        level="warning",
    )

    rng5 = np.random.default_rng(21)
    assignees = ["Finance Team", "AP Lead", "Compliance", "CFO Review"]
    assignee_weights = [0.40, 0.30, 0.20, 0.10]
    exc_df = exc_df.copy()
    exc_df["Assignee"] = rng5.choice(assignees, size=len(exc_df), p=assignee_weights)

    exc_df["Issue_Type"] = exc_df["Status"].map({
        "DISCREPANCY": "DISCREPANCY",
        "DUPLICATE":   "DUPLICATE",
        "FAILED":      "FAILED",
        "PENDING":     "OVERDUE",
    })

    exc_sorted = exc_df.sort_values(
        ["Priority", "Discrepancy_Amt"],
        key=lambda col: col.map({"HIGH": 0, "MED": 1, "LOW": 2}) if col.name == "Priority"
        else col.abs(),
        ascending=[True, False],
    )

    # Color-coded priority column via HTML
    def priority_badge(p):
        c = PRIORITY_COLORS.get(p, MUTED)
        return f'<span style="background:rgba({",".join(str(int(c.lstrip("#")[i:i+2],16)) for i in (0,2,4))},0.15);color:{c};padding:2px 8px;border-radius:10px;font-size:11px;font-weight:700;">{p}</span>'

    exc_display = exc_sorted[["TxID", "Date", "Payer_Vendor", "Issue_Type",
                               "Expected_Amount", "Discrepancy_Amt",
                               "Days_Outstanding", "Priority", "Assignee"]].copy()
    exc_display["Date"] = exc_display["Date"].dt.strftime("%Y-%m-%d")
    exc_display["Expected_Amount"]  = exc_display["Expected_Amount"].apply(fmt_dollar_full)
    exc_display["Discrepancy_Amt"]  = exc_display["Discrepancy_Amt"].apply(fmt_signed)
    exc_display["Days_Outstanding"]  = exc_display["Days_Outstanding"].apply(
        lambda x: f"{int(x)}d" if not pd.isna(x) else "—"
    )
    exc_display.columns = ["Tx ID", "Date", "Vendor", "Issue Type",
                            "Amount ($)", "Gap ($)", "Days Open", "Priority", "Assignee"]
    st.dataframe(exc_display, height=400, use_container_width=True)

    # ── Exception report text block ─────────────────────────────────────────
    section("Copy-Ready Exception Report", "📄")
    high_exc = exc_sorted[exc_sorted["Priority"] == "HIGH"]
    total_exposure = high_exc["Discrepancy_Amt"].abs().sum(skipna=True) + \
                     high_exc[high_exc["Status"] == "FAILED"]["Expected_Amount"].sum()

    lines = [
        f"EXCEPTION REPORT — {today.strftime('%Y-%m-%d')}",
        "CareValidate Payment Reconciliation Engine",
        "=" * 60,
        f"Generated: {today.strftime('%B %d, %Y')}  |  Report Period: Last 30 Days",
        f"Total Transactions Reviewed: {len(df):,}",
        f"Match Rate: {match_rate:.1f}%",
        f"Open Exceptions (All): {open_exceptions:,}",
        f"HIGH Priority Items: {high_ct}",
        "",
        "HIGH PRIORITY EXCEPTIONS",
        "-" * 60,
    ]
    for _, row in high_exc.head(20).iterrows():
        gap_str = fmt_signed(row["Discrepancy_Amt"]) if not pd.isna(row["Discrepancy_Amt"]) else "N/A"
        lines.append(
            f"  [{row['TxID']}]  {row['Date'].strftime('%Y-%m-%d') if hasattr(row['Date'], 'strftime') else str(row['Date'])[:10]}"
            f"  |  {str(row['Payer_Vendor']):<28}"
            f"  |  {row['Status']:<12}"
            f"  |  Gap: {gap_str:<14}"
            f"  |  Assignee: {row['Assignee']}"
        )
    lines += [
        "",
        "-" * 60,
        f"TOTAL FINANCIAL EXPOSURE (HIGH priority): {fmt_dollar_full(total_exposure)}",
        f"Items shown: {min(20, len(high_exc))} of {len(high_exc)} HIGH exceptions",
        "",
        "HIPAA Safe Harbor · Synthetic payment data only · No real financial records or PHI",
        "Ponemon 2025 · IQVIA pharmacy benchmarks",
    ]
    st.code("\n".join(lines), language=None)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 — Anomaly Detection
# ═══════════════════════════════════════════════════════════════════════════
with tab5:
    section("Statistical Anomaly Detection — IQR-Based Outlier Scoring per Category", "🤖")
    alert(
        "Transactions falling outside <b>1.5 × IQR</b> from category median are flagged. "
        "Z-scores > 2.5 trigger a <b>HIGH severity</b> alert. "
        "All scoring is computed per-category to account for natural price dispersion across service lines.",
        level="info",
    )

    flagged = anomaly_df[anomaly_df["IQR_Flag"]].copy()
    high_anom = flagged[flagged["Severity"] == "HIGH"]
    val_at_risk = flagged["Amount"].sum()

    kpi_row([
        kpi_card(f"{len(flagged):,}", "Total Anomalies Detected",
                 f"{100*len(flagged)/max(len(anomaly_df),1):.1f}% of non-pending tx", color="yellow"),
        kpi_card(f"{len(high_anom):,}", "High-Severity Anomalies",
                 "|Z| > 2.5 · Immediate review", color="red"),
        kpi_card(fmt_dollar(val_at_risk), "Estimated Value at Risk",
                 "Sum of flagged transaction amounts", color="purple"),
        kpi_card(f"{len(anomaly_df['Category'].unique()):,}", "Categories Monitored",
                 "Independent IQR per service line", color="teal"),
    ])

    # ── Scatter: Date vs Amount, size=|z|*3, color=category ─────────────────
    section("Anomaly Scatter — Amount vs Time (Marker Size = |Z-Score|)", "🔬")

    anom_plot = anomaly_df.copy()
    anom_plot["z_size"] = np.clip(anom_plot["Z_Score"].abs() * 3, 4, 40)
    anom_plot["Date_str"] = anom_plot["Date"].dt.strftime("%Y-%m-%d")
    cats_u = sorted(anom_plot["Category"].unique())

    fig_scatter = go.Figure()
    for i, cat in enumerate(cats_u):
        sub = anom_plot[anom_plot["Category"] == cat]
        flag_sub = sub[sub["IQR_Flag"]]
        normal_sub = sub[~sub["IQR_Flag"]]

        color = CAT_PALETTE[i % len(CAT_PALETTE)]

        if len(normal_sub):
            fig_scatter.add_trace(go.Scatter(
                x=normal_sub["Date_str"],
                y=normal_sub["Amount"],
                mode="markers",
                name=cat,
                marker=dict(size=normal_sub["z_size"], color=color, opacity=0.35, line=dict(width=0)),
                hovertemplate=(
                    f"<b>{cat}</b><br>"
                    "Vendor: %{customdata[0]}<br>"
                    "Amount: $%{y:,.0f}<br>"
                    "Z-Score: %{customdata[1]:.2f}<br>"
                    "IQR Flag: Normal<extra></extra>"
                ),
                customdata=np.column_stack([normal_sub["Vendor"], normal_sub["Z_Score"].round(2)]),
                legendgroup=cat,
                showlegend=True,
            ))

        if len(flag_sub):
            fig_scatter.add_trace(go.Scatter(
                x=flag_sub["Date_str"],
                y=flag_sub["Amount"],
                mode="markers",
                name=f"{cat} ⚠",
                marker=dict(
                    size=flag_sub["z_size"] * 1.4,
                    color=color,
                    opacity=0.95,
                    line=dict(color="rgba(255,255,255,0.5)", width=1.5),
                    symbol="diamond",
                ),
                hovertemplate=(
                    f"<b>{cat} — FLAGGED</b><br>"
                    "Vendor: %{customdata[0]}<br>"
                    "Amount: $%{y:,.0f}<br>"
                    "Z-Score: %{customdata[1]:.2f}<br>"
                    "Severity: %{customdata[2]}<extra></extra>"
                ),
                customdata=np.column_stack([
                    flag_sub["Vendor"],
                    flag_sub["Z_Score"].round(2),
                    flag_sub["Severity"],
                ]),
                legendgroup=cat,
                showlegend=False,
            ))

    fig_scatter.update_layout(
        **_PLOT_BASE,
        height=420,
        xaxis=dict(**_AXIS_STYLE, title="", tickangle=-30),
        yaxis=dict(**_AXIS_STYLE, title="Transaction Amount ($)"),
        legend=dict(**_LEGEND_BASE, orientation="v", x=1.01, y=1),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # ── Anomaly table ────────────────────────────────────────────────────────
    section("Flagged Anomaly Detail", "📋")
    anom_table = flagged.sort_values("Z_Score", key=lambda s: s.abs(), ascending=False).head(60)
    anom_disp = anom_table[["TxID", "Vendor", "Amount", "Category", "Cat_Median",
                              "Z_Score", "IQR_Flag", "Severity"]].copy()
    anom_disp["Amount"]     = anom_disp["Amount"].apply(fmt_dollar_full)
    anom_disp["Cat_Median"] = anom_disp["Cat_Median"].apply(fmt_dollar_full)
    anom_disp["Z_Score"]    = anom_disp["Z_Score"].round(3)
    anom_disp["IQR_Flag"]   = anom_disp["IQR_Flag"].map({True: "FLAGGED", False: "Normal"})
    anom_disp.columns = ["Tx ID", "Vendor", "Amount ($)", "Category",
                          "Category Median", "Z-Score", "IQR Flag", "Severity"]
    st.dataframe(anom_disp, height=380, use_container_width=True)


# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="margin-top:48px;padding:16px 0 8px 0;border-top:1px solid rgba(255,255,255,0.05);'
    'text-align:center;font-size:11px;color:#334155;line-height:1.8;">'
    'HIPAA Safe Harbor · Synthetic payment data only · No real financial records or PHI · '
    'Ponemon 2025 · IQVIA pharmacy benchmarks'
    '</div>',
    unsafe_allow_html=True,
)
