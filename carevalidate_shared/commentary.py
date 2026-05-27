"""
CareValidate Executive Finance Commentary Generator
Rules-based CFO-style variance narrative. No external API or AI calls.
All logic is deterministic — derived from synthetic dashboard metrics.
"""
import pandas as pd
import streamlit as st
from datetime import date

from carevalidate_shared.theme import (
    CARD, BORDER, BLUE, GREEN, YELLOW, RED, PURPLE, TEAL, MUTED, TEXT,
)


# ── Commentary builder ─────────────────────────────────────────────────────────

def build_commentary(m: dict, audience: str = "Board", tone: str = "Executive") -> tuple[dict, pd.DataFrame, list]:
    """
    Build CFO-style executive commentary and action queue.

    audience: "Board" | "Investors" | "Finance Team"
    tone:     "Executive" | "Detailed"

    m keys:
        mrr_current       float  — current MRR ($)
        mrr_prev          float  — prior month MRR ($)
        gross_margin      float  — gross margin as decimal (0.67)
        gross_margin_prev float  — prior period gross margin
        cash_runway_mo    float  — months of runway
        cash_on_hand_m    float  — cash on hand ($M)
        denial_rate       float  — weighted avg denial rate (0.082)
        dso_days          int    — weighted avg DSO
        nrr               float  — net revenue retention (1.18)
        churn_rate_mo     float  — monthly churn rate (0.028)
        ltv_cac           float  — LTV:CAC ratio
        payback_months    int    — CAC payback months
        compliance_risk_k float  — monthly compliance risk $K
        high_risk_patients int   — patients flagged high churn
        revenue_at_risk_k float  — $K revenue at risk (90-day)
        ar_overdue_k      float  — A/R aging >90 days ($K)
        at_risk_arr_k     float  — ARR with renewal prob <70% ($K)
        report_month      str    — "May 2026"

    Returns (paragraphs_dict, action_queue_df, download_lines)
    """
    mrr       = m["mrr_current"]
    prev_mrr  = m["mrr_prev"]
    gm        = m["gross_margin"]
    gm_prev   = m.get("gross_margin_prev", gm)
    runway    = m["cash_runway_mo"]
    cash_m    = m["cash_on_hand_m"]
    denial    = m["denial_rate"]
    dso       = m["dso_days"]
    nrr       = m["nrr"]
    churn     = m["churn_rate_mo"]
    ltv_cac   = m["ltv_cac"]
    payback   = m["payback_months"]
    comply_k  = m["compliance_risk_k"]
    high_risk = m["high_risk_patients"]
    rev_risk_k= m["revenue_at_risk_k"]
    ar_k      = m.get("ar_overdue_k", 0.0)
    arr_risk_k= m.get("at_risk_arr_k", 0.0)
    month     = m.get("report_month", date.today().strftime("%B %Y"))

    mrr_growth_pct = (mrr - prev_mrr) / prev_mrr * 100
    gm_delta_bps   = (gm - gm_prev) * 10_000

    # ── Revenue ────────────────────────────────────────────────────────────
    if mrr_growth_pct >= 15:
        rev_tone   = "strong"
        rev_driver = "broad-based demand across employer and GLP-1 channels"
    elif mrr_growth_pct >= 8:
        rev_tone   = "solid"
        rev_driver = "continued refill retention and improved payer conversion"
    elif mrr_growth_pct >= 0:
        rev_tone   = "modest"
        rev_driver = "steady engagement from the employer channel, partially offset by softness in DTC"
    else:
        rev_tone   = "negative"
        rev_driver = "elevated churn and lower-than-expected new patient onboarding"

    if nrr > 1.15:
        nrr_note = f" Net revenue retention of {nrr:.0%} reflects strong expansion within the existing patient base."
    elif nrr > 1.05:
        nrr_note = f" Net revenue retention of {nrr:.0%} indicates modest upsell activity alongside stable retention."
    else:
        nrr_note = f" Net revenue retention of {nrr:.0%} suggests limited expansion — review upsell and engagement programs."

    rev_para = (
        f"MRR grew {mrr_growth_pct:+.1f}% month over month to ${mrr/1e3:,.0f}K, "
        f"a {rev_tone} result driven by {rev_driver}.{nrr_note}"
    )

    # ── Margin ─────────────────────────────────────────────────────────────
    if gm_delta_bps > 50:
        margin_move   = f"improved {abs(gm_delta_bps):.0f} bps"
        margin_driver = "lower pharmacy fulfillment costs and a favorable shift toward employer contracts"
    elif gm_delta_bps > -50:
        margin_move   = "was essentially flat"
        margin_driver = "stable pharmacy cost structure with no material shift in payer or program mix"
    elif gm_delta_bps > -150:
        margin_move   = f"declined {abs(gm_delta_bps):.0f} bps"
        margin_driver = "higher pharmacy fulfillment cost per patient and increased navigator labor as a percentage of revenue"
    else:
        margin_move   = f"declined {abs(gm_delta_bps):.0f} bps"
        margin_driver = "a significant step-up in fulfillment costs — review pharmacy AWP contract and patient cohort mix"

    margin_para = (
        f"Gross margin {margin_move} to {gm:.1%}, driven by {margin_driver}. "
        f"At the current rate, each incremental $100K of MRR generates ${gm*100:.0f}K in gross profit."
    )

    # ── Cash ───────────────────────────────────────────────────────────────
    if runway >= 18:
        cash_tone   = f"Runway is healthy at {runway:.0f} months"
        cash_action = "No immediate capital action required; evaluate Series A timing against growth trajectory."
    elif runway >= 12:
        cash_tone   = f"Runway of {runway:.0f} months is adequate but warrants monitoring"
        cash_action = "Accelerate Series A process and review OpEx for near-term optimization opportunities."
    elif runway >= 6:
        cash_tone   = f"Runway of {runway:.0f} months is approaching a critical threshold"
        cash_action = "Initiate bridge financing conversations and implement a near-term burn reduction plan."
    else:
        cash_tone   = f"Runway of {runway:.0f} months is insufficient"
        cash_action = "Immediate fundraising or revenue acceleration required — prepare board update."

    cash_para = (
        f"${cash_m:.1f}M on hand. {cash_tone} at current net burn. {cash_action}"
    )

    # ── Risk ───────────────────────────────────────────────────────────────
    risks = []
    if denial > 0.10:
        risks.append(f"payer denial rate of {denial:.1%} is above the 10% escalation threshold, creating near-term A/R pressure")
    elif denial > 0.07:
        risks.append(f"denial rate of {denial:.1%} is approaching watch territory — monitor by payer and code category")
    if dso > 45:
        risks.append(f"weighted average DSO of {dso} days is elevated relative to the 35-day industry benchmark")
    if ar_k > 50:
        risks.append(f"${ar_k:,.0f}K in A/R is aging past 90 days and requires escalation")
    if high_risk > 30:
        risks.append(f"{high_risk} patients are flagged high churn risk, representing ${rev_risk_k:,.0f}K in 90-day revenue exposure")
    elif high_risk > 10:
        risks.append(f"{high_risk} high-risk patients require proactive outreach to prevent ${rev_risk_k:,.0f}K in potential revenue loss")
    if comply_k > 100:
        risks.append(f"compliance exposure of ${comply_k:,.0f}K/month requires immediate remediation")
    elif comply_k > 50:
        risks.append(f"${comply_k:,.0f}K/month in identified compliance risk — AWP contract review is in progress")
    if arr_risk_k > 100:
        risks.append(f"${arr_risk_k:,.0f}K in ARR has renewal probability below 70% and requires active management")

    if risks:
        risk_bullets = "; ".join(r[0].upper() + r[1:] for r in risks)
        risk_para = f"{risk_bullets}."
    else:
        risk_para = "No critical threshold breaches identified this period. Continue monitoring denial rates, DSO, and churn cohorts on standard cadence."

    # ── Action ─────────────────────────────────────────────────────────────
    actions = []
    if denial > 0.08:
        actions.append("prioritize denial root-cause review by payer and code category")
    if high_risk > 10:
        actions.append(f"activate retention outreach for {high_risk} high-risk patients before 90-day revenue impact crystallizes")
    if ar_k > 30:
        actions.append("escalate A/R collections on aging buckets over 90 days")
    if comply_k > 50:
        actions.append("complete AWP contract renegotiation and close open compliance flags")
    if runway < 15:
        actions.append("accelerate Series A fundraising timeline")
    if arr_risk_k > 100:
        actions.append("schedule QBRs with at-risk employer clients before renewal window closes")
    if not actions:
        actions.append("maintain current operational cadence")
        actions.append("review Series A data room for accuracy ahead of investor discussions")

    action_para = "; ".join(a[0].upper() + a[1:] for a in actions) + "."

    # ── Audience + tone transformations ───────────────────────────────────────
    if tone == "Executive":
        _rev_out = (
            f"MRR {mrr_growth_pct:+.1f}% MoM to ${mrr/1e3:,.0f}K. "
            f"NRR {nrr:.0%} — {'strong expansion' if nrr > 1.15 else 'stable retention'}."
        )
        _margin_out = (
            f"Gross margin {gm:.1%} ({'+' if gm_delta_bps >= 0 else ''}{gm_delta_bps:.0f} bps). "
            f"${gm*100:.0f}K gross profit per $100K MRR."
        )
        _cash_out = f"${cash_m:.1f}M cash · {runway:.0f}mo runway. {cash_action}"
        _risk_out = (risks[0][0].upper() + risks[0][1:] + "." if risks
                     else "No critical threshold breaches this period.")
        _action_out = "; ".join(a[0].upper() + a[1:] for a in actions[:2]) + "."
    else:  # Detailed
        _rev_out    = rev_para
        _margin_out = margin_para
        _cash_out   = cash_para
        _risk_out   = risk_para
        _action_out = action_para

    if audience == "Investors":
        if tone == "Executive":
            _rev_out = (
                f"NRR {nrr:.0%} · MRR {mrr_growth_pct:+.1f}% to ${mrr/1e3:,.0f}K · "
                f"LTV:CAC {ltv_cac:.1f}x · {payback}mo CAC payback."
            )
        else:
            _rev_out = (
                f"Growth efficiency highlight: NRR of {nrr:.0%} signals "
                f"{'strong installed-base expansion' if nrr > 1.15 else 'steady retention'}. "
                + rev_para +
                f" CAC payback of {payback} months with LTV:CAC of {ltv_cac:.1f}x anchors the Series A unit economics narrative."
            )
        _cash_out = (
            f"Series A context: {_cash_out}"
            if tone == "Executive"
            else f"Fundraising context: {_cash_out}"
        )
        _action_out = (
            f"Investor-facing priorities: {_action_out}"
        )

    elif audience == "Board":
        if tone == "Detailed":
            _rev_out = rev_para + (
                f" At current trajectory, the business is on pace to reach "
                f"${mrr * 1.15 / 1e3:,.0f}K MRR within two months."
                if mrr_growth_pct >= 8 else ""
            )
        _action_out = (
            f"Board action items: {_action_out}"
            if tone == "Executive"
            else f"Recommended board actions: {_action_out}"
        )

    else:  # Finance Team
        if tone == "Detailed":
            _rev_out = rev_para + (
                f" Monthly churn of {churn:.1%} equates to ~${churn * mrr / 1e3:,.0f}K "
                f"in gross MRR at risk each period before new patient adds."
            )
            _action_out = action_para + (
                f" DSO of {dso} days vs. 35-day benchmark — "
                f"${(dso - 35) * mrr / 30 / 1e3:,.0f}K cash timing drag to recover."
                if dso > 35 else ""
            )

    paragraphs = {
        "revenue": _rev_out,
        "margin":  _margin_out,
        "cash":    _cash_out,
        "risk":    _risk_out,
        "action":  _action_out,
    }

    # ── Action Queue ───────────────────────────────────────────────────────
    queue = []

    if denial > 0.10:
        queue.append({
            "Priority": "🔴 High",
            "Issue": f"Payer denial rate {denial:.1%} — above 10% escalation threshold",
            "Financial Impact": f"~${denial * mrr * 0.25 / 1e3:,.0f}K delayed cash/month",
            "Recommended Action": "Conduct denial root-cause analysis by payer and procedure code; close documentation gaps",
            "Owner": "Revenue Cycle",
            "Timeframe": "7 days",
        })
    elif denial > 0.07:
        queue.append({
            "Priority": "🟡 Medium",
            "Issue": f"Denial rate {denial:.1%} approaching watch threshold",
            "Financial Impact": f"~${denial * mrr * 0.12 / 1e3:,.0f}K monthly exposure",
            "Recommended Action": "Review payer-specific denial trends; reinforce prior-auth workflow",
            "Owner": "Revenue Cycle",
            "Timeframe": "14 days",
        })

    if high_risk > 10:
        queue.append({
            "Priority": "🔴 High" if high_risk > 30 else "🟡 Medium",
            "Issue": f"{high_risk} patients flagged high churn risk",
            "Financial Impact": f"${rev_risk_k:,.0f}K LTV at risk (90-day window)",
            "Recommended Action": "Launch targeted retention outreach cohort; prioritize navigator touchpoints",
            "Owner": "Operations",
            "Timeframe": "14 days",
        })

    if ar_k > 30:
        queue.append({
            "Priority": "🟡 Medium",
            "Issue": f"${ar_k:,.0f}K in A/R aging past 90 days",
            "Financial Impact": f"${ar_k:,.0f}K settlement timing risk",
            "Recommended Action": "Escalate follow-up with payers on aged claims; validate processor settlement files",
            "Owner": "Payments",
            "Timeframe": "5 days",
        })

    if dso > 40:
        queue.append({
            "Priority": "🟡 Medium",
            "Issue": f"Weighted avg DSO {dso} days (benchmark: 35d)",
            "Financial Impact": f"~${(dso - 35) * mrr / 30 / 1e3:,.0f}K cash timing drag",
            "Recommended Action": "Accelerate collections workflow; review payer-specific payment timelines",
            "Owner": "Revenue Cycle",
            "Timeframe": "30 days",
        })

    if comply_k > 50:
        queue.append({
            "Priority": "🔴 High" if comply_k > 100 else "🟡 Medium",
            "Issue": f"${comply_k:,.0f}K/month compliance exposure",
            "Financial Impact": f"${comply_k * 12 / 1e3:,.0f}K annualized risk",
            "Recommended Action": "Close open compliance flags; finalize AWP contract renegotiation",
            "Owner": "Finance / Legal",
            "Timeframe": "30 days",
        })

    if arr_risk_k > 100:
        queue.append({
            "Priority": "🟡 Medium",
            "Issue": f"${arr_risk_k:,.0f}K ARR with renewal probability <70%",
            "Financial Impact": f"${arr_risk_k:,.0f}K ARR churn risk",
            "Recommended Action": "Schedule QBR with at-risk clients; deliver outcomes report 60+ days before renewal",
            "Owner": "Customer Success",
            "Timeframe": "21 days",
        })

    if runway < 15:
        queue.append({
            "Priority": "🔴 High" if runway < 9 else "🟡 Medium",
            "Issue": f"Cash runway {runway:.0f} months — below 18-month target",
            "Financial Impact": "Series A timing constraint",
            "Recommended Action": "Accelerate investor conversations; finalize data room and financial model",
            "Owner": "CEO / Finance",
            "Timeframe": "30 days",
        })

    if gm < 0.60:
        queue.append({
            "Priority": "🔴 High",
            "Issue": f"Gross margin {gm:.1%} below 60% floor",
            "Financial Impact": f"${(0.60 - gm) * mrr / 1e3:,.0f}K monthly gross profit gap vs. target",
            "Recommended Action": "Review pharmacy fulfillment costs; assess patient cohort mix and program pricing",
            "Owner": "Finance / Operations",
            "Timeframe": "14 days",
        })

    if not queue:
        queue.append({
            "Priority": "🟢 On Track",
            "Issue": "No critical issues identified this period",
            "Financial Impact": "—",
            "Recommended Action": "Maintain monitoring cadence; prepare Series A data room",
            "Owner": "Finance",
            "Timeframe": "Ongoing",
        })

    action_df = pd.DataFrame(queue)

    # ── Download text ──────────────────────────────────────────────────────
    lines = [
        f"CAREVALIDATE — EXECUTIVE FINANCE BRIEF",
        f"{month}",
        "=" * 60,
        "",
        "EXECUTIVE COMMENTARY",
        "-" * 40,
        f"Revenue: {rev_para}",
        "",
        f"Margin: {margin_para}",
        "",
        f"Cash: {cash_para}",
        "",
        f"Risk: {risk_para}",
        "",
        f"Action: {action_para}",
        "",
        "=" * 60,
        "CFO ACTION QUEUE",
        "-" * 40,
    ]
    for row in queue:
        lines.append(
            f"[{row['Priority']}] {row['Issue']}\n"
            f"  Impact:    {row['Financial Impact']}\n"
            f"  Action:    {row['Recommended Action']}\n"
            f"  Owner:     {row['Owner']}  |  Timeframe: {row['Timeframe']}\n"
        )
    lines += [
        "=" * 60,
        "DISCLAIMER",
        "-" * 40,
        "Synthetic data only. No PHI. Prototype for discussion purposes only.",
        "Commentary is generated from illustrative assumptions and should not",
        "be treated as financial, legal, or compliance advice.",
        f"Generated: {date.today().strftime('%B %d, %Y')}",
    ]

    return paragraphs, action_df, lines


# ── Streamlit renderer ─────────────────────────────────────────────────────────

_PARA_CONFIG = {
    "revenue": ("📈", "Revenue",  GREEN,  "rgba(16,185,129,0.08)",  "rgba(16,185,129,0.22)"),
    "margin":  ("📊", "Margin",   YELLOW, "rgba(245,158,11,0.08)",  "rgba(245,158,11,0.22)"),
    "cash":    ("💵", "Cash",     BLUE,   "rgba(59,130,246,0.08)",  "rgba(59,130,246,0.22)"),
    "risk":    ("⚠️", "Risk",     RED,    "rgba(239,68,68,0.08)",   "rgba(239,68,68,0.22)"),
    "action":  ("✅", "Action",   PURPLE, "rgba(139,92,246,0.08)",  "rgba(139,92,246,0.22)"),
}


def render_commentary_ui(paragraphs: dict, action_df: pd.DataFrame, download_lines: list,
                         report_month: str = "", audience: str = "Board", tone: str = "Executive") -> None:
    """Render the full executive commentary UI block in Streamlit."""

    month_label = report_month or date.today().strftime("%B %Y")
    _audience_badge = {"Board": "#3b82f6", "Investors": "#8b5cf6", "Finance Team": "#10b981"}.get(audience, "#3b82f6")
    _tone_label = "Concise" if tone == "Executive" else "Full narrative"

    # Header card
    st.markdown(
        f'<div style="background:linear-gradient(135deg,rgba(59,130,246,0.08) 0%,rgba(139,92,246,0.06) 100%);'
        f'border:1px solid rgba(59,130,246,0.18);border-radius:12px;padding:16px 20px;margin-bottom:20px;">'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'<span style="font-size:20px;">📝</span>'
        f'<div style="flex:1;">'
        f'<div style="font-size:14px;font-weight:700;color:#f1f5f9;">Executive Finance Commentary — {month_label}</div>'
        f'<div style="font-size:11px;color:#475569;margin-top:2px;">'
        f'Rules-based variance narrative · generated from synthetic dashboard data · not financial advice'
        f'</div></div>'
        f'<div style="display:flex;gap:6px;flex-shrink:0;">'
        f'<span style="background:{_audience_badge}22;border:1px solid {_audience_badge}44;'
        f'color:{_audience_badge};font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;">'
        f'{audience.upper()}</span>'
        f'<span style="background:rgba(100,116,139,0.15);border:1px solid rgba(100,116,139,0.3);'
        f'color:#94a3b8;font-size:10px;font-weight:600;padding:2px 8px;border-radius:20px;">'
        f'{_tone_label.upper()}</span>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )

    # Commentary paragraphs — 5 cards in 2 columns
    col_a, col_b = st.columns([1, 1], gap="medium")
    items = list(_PARA_CONFIG.items())
    left_keys  = ["revenue", "margin", "cash"]
    right_keys = ["risk", "action"]

    def _para_card(key: str) -> None:
        icon, label, color, bg, border = _PARA_CONFIG[key]
        text = paragraphs.get(key, "")
        st.markdown(
            f'<div style="background:{bg};border:1px solid {border};'
            f'border-left:3px solid {color};border-radius:10px;'
            f'padding:14px 16px;margin-bottom:10px;">'
            f'<div style="font-size:10px;font-weight:700;letter-spacing:.07em;'
            f'color:{color};margin-bottom:6px;">{icon} {label.upper()}</div>'
            f'<div style="font-size:13px;color:#cbd5e1;line-height:1.65;">{text}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_a:
        for k in left_keys:
            _para_card(k)
    with col_b:
        for k in right_keys:
            _para_card(k)

    # ── CFO Action Queue ───────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:12px;font-weight:700;color:#475569;'
        'letter-spacing:.06em;margin:20px 0 8px 0;">CFO ACTION QUEUE</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(action_df, use_container_width=True, hide_index=True,
                 height=min(56 + len(action_df) * 38, 320))

    # ── Download ───────────────────────────────────────────────────────────
    download_text = "\n".join(download_lines).encode("utf-8")
    fname = f"cfo_brief_{month_label.replace(' ','_').lower()}.txt"
    st.download_button(
        label="⬇  Download Monthly CFO Brief",
        data=download_text,
        file_name=fname,
        mime="text/plain",
        key=f"dl_cfo_brief_{month_label}",
    )

    st.markdown(
        '<div style="font-size:11px;color:#1e293b;margin-top:10px;">'
        'Synthetic data only · No PHI · Prototype for discussion purposes only · '
        'Commentary is generated from illustrative assumptions and should not be treated as '
        'financial, legal, or compliance advice.'
        '</div>',
        unsafe_allow_html=True,
    )
