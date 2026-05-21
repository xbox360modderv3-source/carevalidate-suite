"""
CareValidate Security & Compliance Readiness Center
RBAC matrix, audit trail, BAA vendor tracker, breach cost model,
de-identification pipeline, HITRUST control reference.
Prototype  |  Synthetic/illustrative data only — no real PHI or credentials
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import random
from carevalidate_shared.theme import (
    GLOBAL_CSS, render_header, kpi_card, kpi_row, section, alert, sidebar_nav,
    BG, CARD, BLUE, GREEN, YELLOW, RED, PURPLE, TEAL, MUTED,
)
from carevalidate_shared.auth import check_auth, logout_button

st.set_page_config(page_title="Security & Compliance Readiness Center", layout="wide", page_icon="🔒")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
check_auth()
sidebar_nav("sec")
logout_button()

render_header(
    "Security & Compliance Readiness Center",
    "RBAC · Audit trail · BAA tracker · Breach cost model · HITRUST control reference · De-identification pipeline",
    badge="Prototype View",
    badge_color="red",
)

alert(
    "<strong>Prototype compliance posture dashboard.</strong> All data is synthetic. "
    "No real credentials, PHI, employee records, or audit events are used or stored. "
    "This dashboard demonstrates controls that a production healthcare analytics platform may need. "
    "It does not certify compliance. Production deployment requires legal, security, and compliance review.",
    level="warning",
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🛡️ Security Posture",
    "🔑 Access Control (RBAC)",
    "📋 Audit Trail",
    "📄 BAA Vendor Tracker",
    "🔬 De-identification Pipeline",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SECURITY POSTURE
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    section("Overall Security Posture", "🛡️")
    kpi_row([
        kpi_card("94 / 100", "HITRUST CSF Score",
                 "r2 assessment · 19 domains · last audit Jan 2026",
                 trend="+6 pts YoY", trend_good=True, color="green"),
        kpi_card("$0", "PHI Breach Cost (YTD)",
                 "0 incidents · Ponemon 2025 avg: $7.42M per breach",
                 trend="Clean record", trend_good=True, color="green"),
        kpi_card("100%", "Audit Log Coverage",
                 "Every ePHI-adjacent access logged · 6-yr retention",
                 color="green"),
        kpi_card("14 / 15", "BAA Agreements Current",
                 "1 renewal due in 14 days · flagged below",
                 color="yellow"),
    ])

    st.divider()
    sec_col1, sec_col2 = st.columns([3, 2], gap="medium")

    with sec_col1:
        section("HITRUST CSF — 19 Control Domains", "")
        domains = [
            ("Information Protection Program",     96, "Compliant"),
            ("Endpoint Protection",                92, "Compliant"),
            ("Portable Media Security",            88, "Compliant"),
            ("Mobile Device Security",             91, "Compliant"),
            ("Wireless Protection",                89, "Compliant"),
            ("Configuration Management",           94, "Compliant"),
            ("Vulnerability Management",           87, "Compliant"),
            ("Network Protection",                 95, "Compliant"),
            ("Transmission Protection",            98, "Compliant"),
            ("Password Management",                93, "Compliant"),
            ("Access Control",                     96, "Compliant"),
            ("Audit Logging & Monitoring",         97, "Compliant"),
            ("Education, Training & Awareness",    84, "At Risk"),
            ("Third Party Assurance",              80, "At Risk"),
            ("Incident Management",                91, "Compliant"),
            ("Business Continuity & DR",           88, "Compliant"),
            ("Risk Management",                    93, "Compliant"),
            ("Physical & Environmental Security",  86, "Compliant"),
            ("Data Protection & Privacy",          95, "Compliant"),
        ]
        dom_df = pd.DataFrame(domains, columns=["Domain","Score","Status"])
        colors = [GREEN if s >= 90 else (YELLOW if s >= 80 else RED) for s in dom_df["Score"]]
        fig_h = go.Figure(go.Bar(
            y=dom_df["Domain"], x=dom_df["Score"],
            orientation="h",
            marker_color=colors,
            text=[f"{s}" for s in dom_df["Score"]],
            textposition="outside",
            textfont=dict(size=10, color="#f1f5f9"),
        ))
        fig_h.add_vline(x=90, line_width=1, line_dash="dash",
                        line_color="rgba(16,185,129,0.45)")
        fig_h.add_annotation(x=90, y=18, text="90 threshold",
                              showarrow=False, font=dict(size=10, color=GREEN), xshift=35)
        fig_h.update_layout(
            template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
            height=520, margin=dict(l=0, r=50, t=10, b=0),
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)", range=[0, 110]),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10)),
        )
        st.plotly_chart(fig_h, use_container_width=True)

    with sec_col2:
        section("Breach Cost Financial Model", "💥")
        st.markdown(
            '<div style="font-size:12px;color:#475569;margin:-6px 0 12px 0;">'
            'Ponemon Institute 2025 · IBM Cost of a Data Breach Report</div>',
            unsafe_allow_html=True
        )
        records_sl  = st.slider("Records potentially affected", 100, 500000, 10000, 100)
        detect_days = st.slider("Days to detect breach", 30, 280, 120, 10)

        cost_per_rec   = 429          # Ponemon 2025 healthcare avg
        base_cost      = records_sl * cost_per_rec
        detect_penalty = base_cost * (detect_days / 200) * 0.25
        ocr_fine       = min(records_sl * 100, 1_900_000)   # OCR tiered penalty
        litigation_est = max(records_sl * 50, 500_000)
        notif_cost     = records_sl * 12                     # notification + credit monitoring
        total_breach   = base_cost + detect_penalty + ocr_fine + litigation_est + notif_cost

        kpi_row([
            kpi_card(f"${total_breach/1e6:.2f}M", "Estimated Total Breach Cost",
                     f"{records_sl:,} records · {detect_days}-day MTTD",
                     color="red"),
            kpi_card(f"${ocr_fine/1e3:.0f}K", "OCR Civil Penalty",
                     "HIPAA tiered penalty structure", color="red"),
        ])

        items  = ["Per-record cost", "Late detection", "OCR fine", "Litigation", "Notification"]
        values = [base_cost, detect_penalty, ocr_fine, litigation_est, notif_cost]
        fig_b  = go.Figure(go.Pie(
            labels=items, values=values, hole=0.5,
            marker=dict(colors=[RED, "#dc2626", "#b91c1c", "#991b1b", YELLOW],
                        line=dict(color=BG, width=2)),
            textfont=dict(size=10),
        ))
        fig_b.update_layout(
            paper_bgcolor=BG, height=260, margin=dict(l=0, r=0, t=10, b=0),
            annotations=[dict(text=f"${total_breach/1e6:.1f}M", x=0.5, y=0.5,
                              font=dict(size=13, color="#f1f5f9"), showarrow=False)],
            legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig_b, use_container_width=True)

        section("Safeguard ROI", "")
        annual_invest   = 185_000   # HIPAA compliance program cost (illustrative)
        breach_prob_raw = 0.28      # 28% annual breach probability — IBM 2025
        breach_prob_sec = 0.07      # with controls in place
        expected_loss_raw = total_breach * breach_prob_raw
        expected_loss_sec = total_breach * breach_prob_sec
        risk_reduction    = expected_loss_raw - expected_loss_sec
        security_roi      = (risk_reduction - annual_invest) / annual_invest
        kpi_row([
            kpi_card(f"${risk_reduction/1e3:.0f}K", "Annual Expected Loss Reduction",
                     f"From {breach_prob_raw:.0%} → {breach_prob_sec:.0%} breach probability",
                     color="green"),
            kpi_card(f"{security_roi:.1f}x", "Security Program ROI",
                     f"${annual_invest/1e3:.0f}K annual investment",
                     trend="Pure risk management return", trend_good=True, color="green"),
        ])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — RBAC ACCESS CONTROL
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    section("Role-Based Access Control (RBAC) Matrix", "🔑")
    st.markdown(
        '<div style="font-size:12px;color:#475569;margin:-8px 0 14px 0;">'
        'HIPAA §164.312(a)(1) — Unique user identification · access authorization · automatic logoff. '
        'HITRUST Control 01.a. All access to ePHI-adjacent data requires MFA and is logged immutably.</div>',
        unsafe_allow_html=True
    )

    roles = ["CFO / Finance", "Care Navigator", "Care Coordinator", "Payer Account Mgr", "Data Analyst", "System Admin"]
    categories = [
        "Financial Reports\n(No PHI)",
        "Navigator KPIs\n(De-identified)",
        "Aggregate Quality\nMetrics (De-id)",
        "Individual Member\nRecords (PHI★)",
        "Audit Logs\n(Internal)",
        "System Config\n(Admin)",
        "BAA / Contracts\n(Confidential)",
    ]

    # Access matrix: R=read, W=write, N=none, A=admin
    matrix = [
        # CFO
        ["R/W", "R",   "R",   "N",   "R",   "N",   "R/W"],
        # Navigator
        ["N",   "R",   "R",   "R★",  "N",   "N",   "N"  ],
        # Coordinator
        ["N",   "R",   "R/W", "R★",  "N",   "N",   "N"  ],
        # Payer Acct Mgr
        ["R",   "R",   "R",   "N",   "N",   "N",   "R"  ],
        # Data Analyst
        ["R",   "R",   "R",   "N",   "R",   "N",   "N"  ],
        # System Admin
        ["R",   "R",   "R",   "N",   "R/W", "R/W", "R"  ],
    ]

    def access_color(val):
        if val == "R/W":   return "#10b981"
        if val == "R":     return "#3b82f6"
        if val == "R★":   return "#f59e0b"
        if val == "A":     return "#8b5cf6"
        return "#1e293b"

    def access_text_color(val):
        return "#0f172a" if val == "N" else "#f8fafc"

    rbac_html = '<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:12px;">'
    rbac_html += '<thead><tr><th style="padding:10px 14px;text-align:left;color:#475569;border-bottom:1px solid rgba(255,255,255,0.08);min-width:160px;">Role</th>'
    for cat in categories:
        label = cat.replace("\n", "<br>")
        rbac_html += f'<th style="padding:10px 10px;text-align:center;color:#475569;border-bottom:1px solid rgba(255,255,255,0.08);font-size:10px;line-height:1.4;">{label}</th>'
    rbac_html += '</tr></thead><tbody>'
    for i, role in enumerate(roles):
        rbac_html += f'<tr><td style="padding:10px 14px;font-weight:600;color:#f1f5f9;border-bottom:1px solid rgba(255,255,255,0.04);">{role}</td>'
        for j, val in enumerate(matrix[i]):
            bg   = access_color(val)
            fc   = access_text_color(val)
            note = " (MFA req)" if "★" in val else ""
            rbac_html += (
                f'<td style="padding:8px 10px;text-align:center;border-bottom:1px solid rgba(255,255,255,0.04);">'
                f'<span style="background:{bg};color:{fc};padding:3px 10px;border-radius:6px;'
                f'font-size:10px;font-weight:700;white-space:nowrap;">{val}{note}</span></td>'
            )
        rbac_html += '</tr>'
    rbac_html += '</tbody></table></div>'
    rbac_html += (
        '<div style="margin-top:12px;font-size:10px;color:#334155;line-height:1.8;">'
        '★ PHI access requires: Active BAA · Phishing-resistant MFA (FIDO2) · Session logged · '
        'Auto-logoff after 15 min inactivity · AES-256 at rest · TLS 1.3 in transit</div>'
    )
    st.markdown(rbac_html, unsafe_allow_html=True)

    st.divider()
    section("Session & Authentication Policy", "")
    pol_c1, pol_c2, pol_c3 = st.columns(3, gap="medium")
    policies = [
        ("MFA Requirement",           "FIDO2 / Authenticator App",         "All users — HIPAA 2026 §164.312(d)"),
        ("Password Policy",           "16-char min · no expiry w/ MFA",    "NIST SP 800-63B Rev 4"),
        ("Session Timeout",           "15 min inactivity (PHI) / 60 min",  "HIPAA addressable safeguard"),
        ("Encryption at Rest",        "AES-256 · envelope keyed per org",  "HIPAA §164.312(a)(2)(iv)"),
        ("Encryption in Transit",     "TLS 1.3 · HSTS · cert pinning",     "HIPAA §164.312(e)(2)(ii)"),
        ("Audit Log Retention",       "6 years · immutable · off-site",    "HIPAA §164.312(b)"),
    ]
    for col, chunk in zip([pol_c1, pol_c2, pol_c3], [policies[:2], policies[2:4], policies[4:]]):
        with col:
            for name, val, ref in chunk:
                st.markdown(
                    f'<div style="padding:12px 14px;background:{CARD};border:1px solid rgba(255,255,255,0.07);'
                    f'border-left:3px solid {GREEN};border-radius:10px;margin-bottom:8px;">'
                    f'<div style="font-size:11px;font-weight:700;color:#f1f5f9;margin-bottom:4px;">{name}</div>'
                    f'<div style="font-size:12px;color:{TEAL};font-weight:600;margin-bottom:3px;">{val}</div>'
                    f'<div style="font-size:10px;color:#334155;">{ref}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AUDIT TRAIL
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    section("Immutable Audit Trail", "📋")
    st.markdown(
        '<div style="font-size:12px;color:#475569;margin:-8px 0 14px 0;">'
        'HIPAA §164.312(b) — Activity review. Every access to ePHI-adjacent data is logged with '
        'timestamp, user, action, resource, and outcome. Logs are write-once and retained 6 years. '
        '<strong>Synthetic events only — no real access records shown.</strong></div>',
        unsafe_allow_html=True
    )

    @st.cache_data
    def build_audit_log(seed=42):
        rng = np.random.default_rng(seed)
        users = [
            ("u001","Sarah Chen","Care Navigator"),
            ("u002","Maria Rodriguez","Care Navigator"),
            ("u003","David Kim","Care Coordinator"),
            ("u004","Aisha Hassan","Care Navigator"),
            ("u005","CFO_Connor","CFO / Finance"),
            ("u006","analyst_01","Data Analyst"),
            ("u007","admin_sys","System Admin"),
            ("u008","payer_mgr_A","Payer Account Mgr"),
        ]
        actions = [
            ("VIEW_MEMBER_RECORD",    "Member Record",      "R★",  "PHI-adjacent"),
            ("SCHEDULE_APPOINTMENT",  "Scheduling Queue",   "W",   "De-identified"),
            ("EXPORT_QUALITY_REPORT", "Quality Metrics",    "R",   "De-identified"),
            ("LOGIN",                 "Auth System",        "Auth","System"),
            ("VIEW_DASHBOARD",        "Finance Dashboard",  "R",   "No PHI"),
            ("LOGOUT",                "Auth System",        "Auth","System"),
            ("EXPORT_FINANCIAL_RPT",  "Financial Reports",  "R",   "No PHI"),
            ("UPDATE_BAA",            "Contract System",    "W",   "Confidential"),
            ("VIEW_AUDIT_LOG",        "Audit System",       "R",   "Internal"),
            ("CONFIG_RBAC",           "RBAC System",        "W",   "Admin"),
        ]
        outcomes = ["SUCCESS"] * 45 + ["FAILED_AUTH"] * 3 + ["PERMISSION_DENIED"] * 2
        rng.shuffle(outcomes)

        now = datetime.now()
        rows = []
        for i in range(50):
            ts_offset = timedelta(hours=rng.integers(0, 168))
            ts        = now - ts_offset
            user      = users[rng.integers(0, len(users))]
            action    = actions[rng.integers(0, len(actions))]
            outcome   = outcomes[i]
            rows.append({
                "Timestamp":     ts.strftime("%Y-%m-%d %H:%M:%S"),
                "User ID":       user[0],
                "User Name":     user[1],
                "Role":          user[2],
                "Action":        action[0],
                "Resource":      action[1],
                "Data Class":    action[3],
                "Outcome":       outcome,
                "IP (masked)":   f"10.{rng.integers(0,255)}.x.x",
                "Session ID":    f"ses_{rng.integers(100000,999999)}",
            })
        df = pd.DataFrame(rows).sort_values("Timestamp", ascending=False).reset_index(drop=True)
        return df

    audit_df = build_audit_log()

    at_c1, at_c2, at_c3, at_c4 = st.columns(4, gap="small")
    with at_c1:
        filter_role = st.selectbox("Filter by role", ["All"] + sorted(audit_df["Role"].unique().tolist()))
    with at_c2:
        filter_action = st.selectbox("Filter by action", ["All"] + sorted(audit_df["Action"].unique().tolist()))
    with at_c3:
        filter_outcome = st.selectbox("Filter by outcome", ["All"] + sorted(audit_df["Outcome"].unique().tolist()))
    with at_c4:
        filter_class = st.selectbox("Filter by data class", ["All"] + sorted(audit_df["Data Class"].unique().tolist()))

    display_df = audit_df.copy()
    if filter_role    != "All": display_df = display_df[display_df["Role"]       == filter_role]
    if filter_action  != "All": display_df = display_df[display_df["Action"]     == filter_action]
    if filter_outcome != "All": display_df = display_df[display_df["Outcome"]    == filter_outcome]
    if filter_class   != "All": display_df = display_df[display_df["Data Class"] == filter_class]

    failures = (display_df["Outcome"] != "SUCCESS").sum()
    phi_access = (display_df["Data Class"] == "PHI-adjacent").sum()
    kpi_row([
        kpi_card(f"{len(display_df)}", "Events Shown", f"of {len(audit_df)} total (7-day window)", color="blue"),
        kpi_card(f"{failures}", "Auth Failures / Denials",
                 "Investigate if > 5 in 24 hrs", color="red" if failures > 3 else "yellow"),
        kpi_card(f"{phi_access}", "PHI-Adjacent Accesses",
                 "All require MFA + audit review", color="yellow"),
        kpi_card("Immutable", "Log Integrity",
                 "SHA-256 hash chain · write-once · off-site backup", color="green"),
    ])

    def color_outcome(val):
        if val == "SUCCESS":          return "color: #10b981"
        if val == "FAILED_AUTH":      return "color: #ef4444"
        if val == "PERMISSION_DENIED": return "color: #f59e0b"
        return ""

    st.dataframe(
        display_df.drop(columns=["Session ID"]).set_index("Timestamp"),
        use_container_width=True, height=320,
    )

    st.markdown(
        '<div style="font-size:10px;color:#334155;margin-top:8px;">'
        'Log hash: <span style="font-family:monospace;color:#475569;">'
        'sha256:a3f9c2...e841b7 (illustrative) · Logs are tamper-evident via append-only storage. '
        'In production: CloudWatch / Splunk SIEM with real-time alerting on FAILED_AUTH spikes.</span></div>',
        unsafe_allow_html=True
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — BAA VENDOR TRACKER
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    section("Business Associate Agreement (BAA) Tracker", "📄")
    st.markdown(
        '<div style="font-size:12px;color:#475569;margin:-8px 0 14px 0;">'
        'HIPAA §164.308(b)(1) — Business associate contracts required before any vendor '
        'handles, transmits, or stores PHI or ePHI. Failure to maintain active BAAs = '
        'material HIPAA violation. OCR fine range: $100–$50,000 per violation.</div>',
        unsafe_allow_html=True
    )

    today = date.today()
    vendors = [
        ("Cloud Hosting (AWS GovCloud)",  "Infrastructure",    True,  "Active", (today + timedelta(days=365)).isoformat(), "AES-256 · HITRUST · FedRAMP Mod", "Low",      95),
        ("EHR Integration (Epic-style)",  "Clinical Data",     True,  "Active", (today + timedelta(days=180)).isoformat(), "HL7 FHIR R4 · SOC 2 Type II",    "Low",      91),
        ("Telephony / Outreach",          "Communications",    True,  "Active", (today + timedelta(days=14)).isoformat(),  "TLS 1.3 · call recording secure", "Medium",   76),
        ("Translation Services",          "Multi-lingual Nav", True,  "Active", (today + timedelta(days=90)).isoformat(),  "NDA + BAA · human translators",   "Medium",   82),
        ("Data Warehouse (Snowflake)",    "Analytics",         True,  "Active", (today + timedelta(days=280)).isoformat(), "SOC 2 · column-level encryption",  "Low",      88),
        ("Medical Coding Vendor",         "Revenue Cycle",     True,  "Active", (today + timedelta(days=210)).isoformat(), "CMS-certified · AHIMA aligned",   "Low",      90),
        ("Payment Processor",             "Finance",           False, "N/A",    "N/A",                                     "PCI-DSS Level 1 · no PHI",        "None",    100),
        ("AI/LLM Provider",               "Analytics / ML",    True,  "Pending",(today + timedelta(days=30)).isoformat(),  "Zero-retention BAA required",     "High",     55),
        ("Background Check Vendor",       "HR",                False, "N/A",    "N/A",                                     "FCRA compliant · no PHI",         "None",     98),
        ("Scheduling Subprocessor",       "Ops",               True,  "Active", (today + timedelta(days=320)).isoformat(), "SOC 2 Type II · BAA executed",    "Low",      93),
    ]
    vdf = pd.DataFrame(vendors, columns=[
        "Vendor","Category","PHI_Access","BAA_Status","BAA_Expiry","Security_Controls","Risk_Level","Risk_Score"
    ])
    vdf["Days_Until_Expiry"] = vdf["BAA_Expiry"].apply(
        lambda x: (date.fromisoformat(x) - today).days if x != "N/A" else None
    )
    vdf["Flag"] = vdf.apply(
        lambda r: "🔴 Urgent" if (r["Days_Until_Expiry"] is not None and r["Days_Until_Expiry"] < 30)
        else ("⚠️ Review" if (r["Days_Until_Expiry"] is not None and r["Days_Until_Expiry"] < 90) or r["BAA_Status"] == "Pending"
        else "✅ OK"), axis=1
    )

    kpi_row([
        kpi_card(f"{vdf['PHI_Access'].sum()}", "Vendors with PHI Access",
                 "All require executed BAA", color="blue"),
        kpi_card(f"{(vdf['BAA_Status']=='Active').sum()}", "Active BAAs",
                 f"of {vdf['PHI_Access'].sum()} required", color="green"),
        kpi_card(f"{(vdf['Risk_Level']=='High').sum()}", "High-Risk Vendors",
                 "Require enhanced due diligence", color="red"),
        kpi_card(f"{(vdf['Days_Until_Expiry'].dropna() < 30).sum()}", "Renewals Due < 30 Days",
                 "Telephony vendor flagged — renew now", color="yellow"),
    ])

    disp_v = vdf[["Vendor","Category","BAA_Status","BAA_Expiry","Security_Controls","Risk_Level","Flag"]].copy()
    disp_v.columns = ["Vendor","Category","BAA Status","Expiry","Security Controls","Risk","Flag"]
    st.dataframe(disp_v.set_index("Vendor"), use_container_width=True, height=350)

    alert(
        "AI/LLM Provider BAA is in <strong>Pending</strong> status — this is a HIGH-risk item. "
        "Before using any AI provider to process or analyze PHI-adjacent data, a fully executed BAA with "
        "a <strong>Zero-Retention clause</strong> (AI model not trained on your data) is required under "
        "HIPAA 2026 guidance. Do not send PHI to any AI API until the BAA is executed and reviewed by legal. "
        "Current CareValidate suite sends zero PHI to any external API — all data is synthetic.",
        level="warning",
    )

    section("Vendor Risk Scoring Matrix", "")
    fig_v = go.Figure(go.Bar(
        y=vdf["Vendor"], x=vdf["Risk_Score"],
        orientation="h",
        marker_color=[GREEN if s >= 90 else (YELLOW if s >= 75 else RED) for s in vdf["Risk_Score"]],
        text=[f"{s}" for s in vdf["Risk_Score"]], textposition="outside",
        textfont=dict(size=11, color="#f1f5f9"),
    ))
    fig_v.add_vline(x=80, line_width=1, line_dash="dash", line_color="rgba(245,158,11,0.5)")
    fig_v.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=CARD,
        height=300, margin=dict(l=0, r=50, t=10, b=0),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", range=[0, 110], title="Vendor Risk Score"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10)),
    )
    st.plotly_chart(fig_v, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — DE-IDENTIFICATION PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    section("HIPAA Safe Harbor De-identification Pipeline", "🔬")
    st.markdown(
        '<div style="font-size:12px;color:#475569;margin:-8px 0 14px 0;">'
        'HIPAA §164.514(b) Safe Harbor Method — 18 identifier categories must be removed or masked '
        'before data can be used for analytics, dashboards, or ML. This pipeline documents the '
        'transformation applied before any data reaches CareValidate dashboards.</div>',
        unsafe_allow_html=True
    )

    identifiers = [
        ("Names",                          "Full suppression",      "Replace with synthetic name",      True),
        ("Geographic data (< state)",      "Generalize to state",   "State-level only · no ZIP",        True),
        ("All dates (except year)",        "Year-only retention",   "DOB → birth year · visit → month", True),
        ("Phone numbers",                  "Full suppression",      "Removed — not needed for analytics",True),
        ("Fax numbers",                    "Full suppression",      "Removed",                          True),
        ("Email addresses",                "Full suppression",      "Removed",                          True),
        ("Social Security numbers",        "Full suppression",      "Never ingested",                   True),
        ("Medical record numbers",         "Tokenization",          "Replaced with rotating token",     True),
        ("Health plan beneficiary numbers","Tokenization",          "Replaced with rotating token",     True),
        ("Account numbers",                "Full suppression",      "Removed",                          True),
        ("Certificate / license numbers",  "Full suppression",      "Removed",                          True),
        ("Vehicle identifiers (VIN)",      "N/A",                   "Not in scope",                     True),
        ("Device identifiers / serial #s", "N/A",                   "Not in scope",                     True),
        ("URLs / Web addresses",           "Full suppression",      "Removed",                          True),
        ("IP addresses",                   "Masking",               "Last 2 octets zeroed: x.x.0.0",   True),
        ("Biometric identifiers",          "N/A",                   "Not collected",                    True),
        ("Full-face photographs",          "N/A",                   "Not collected",                    True),
        ("Any unique identifying number",  "Tokenization",          "All IDs rotated every 90 days",    True),
    ]

    id_df = pd.DataFrame(identifiers, columns=["Identifier","Method","Implementation","Status"])
    id_df["Status"] = id_df["Status"].map({True: "✅ Handled", False: "🔴 Gap"})

    pipeline_html = (
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;">'
    )
    for _, row in id_df.iterrows():
        color = GREEN if "✅" in row["Status"] else RED
        pipeline_html += (
            f'<div style="padding:12px 14px;background:{CARD};border:1px solid rgba(255,255,255,0.06);'
            f'border-left:3px solid {color};border-radius:10px;">'
            f'<div style="font-size:11px;font-weight:700;color:#f1f5f9;margin-bottom:4px;">{row["Identifier"]}</div>'
            f'<div style="font-size:11px;color:{TEAL};margin-bottom:3px;">{row["Method"]}</div>'
            f'<div style="font-size:10px;color:#475569;">{row["Implementation"]}</div>'
            f'<div style="font-size:10px;margin-top:5px;">{row["Status"]}</div>'
            f'</div>'
        )
    pipeline_html += '</div>'
    st.markdown(pipeline_html, unsafe_allow_html=True)

    kpi_row([
        kpi_card("18 / 18", "Safe Harbor Identifiers Handled",
                 "100% HIPAA §164.514(b) coverage", color="green"),
        kpi_card("0", "PHI Identifiers in Analytics Layer",
                 "Zero PHI passes through to dashboards", color="green"),
        kpi_card("90-day", "Token Rotation Cycle",
                 "Medical record / beneficiary tokens rotated quarterly", color="blue"),
        kpi_card("Expert Det.", "Secondary Method",
                 "Expert Determination available for edge cases · §164.514(b)(1)", color="purple"),
    ])

    st.divider()
    section("Data Flow Architecture — PHI Firewall", "")
    flow_html = (
        '<div style="font-family:monospace;font-size:12px;color:#64748b;line-height:2.2;'
        'padding:20px 24px;background:#0a0d14;border:1px solid rgba(255,255,255,0.06);'
        'border-radius:12px;overflow-x:auto;">'
        '<span style="color:#475569;">// PHI BOUNDARY — nothing crosses right without de-identification</span><br><br>'
        '<span style="color:#ef4444;font-weight:700;">[ PHI Zone ]</span>  '
        '<span style="color:#334155;">EHR / Payer System</span>  →  '
        '<span style="color:#f59e0b;">De-id Pipeline</span>  →  '
        '<span style="color:#10b981;font-weight:700;">[ Safe Zone ]</span>  '
        '<span style="color:#334155;">CareValidate Analytics</span><br><br>'
        '&nbsp;&nbsp;&nbsp;<span style="color:#94a3b8;">│</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        '<span style="color:#94a3b8;">│</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        '<span style="color:#94a3b8;">│</span><br>'
        '&nbsp;&nbsp;&nbsp;<span style="color:#ef4444;">PHI</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        '<span style="color:#f59e0b;">18-field Safe Harbor</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        '<span style="color:#10b981;">Synthetic / De-id Only</span><br>'
        '&nbsp;&nbsp;&nbsp;<span style="color:#ef4444;">Names, DOB, SSN,</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        '<span style="color:#f59e0b;">Suppression · Tokenization</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        '<span style="color:#10b981;">Dashboards · ML Models</span><br>'
        '&nbsp;&nbsp;&nbsp;<span style="color:#ef4444;">MRN, ZIP+4, etc.</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        '<span style="color:#f59e0b;">Generalization · Masking</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        '<span style="color:#10b981;">CFO Reports · HEDIS</span><br><br>'
        '<span style="color:#334155;">Encryption:&nbsp;</span><span style="color:#3b82f6;">AES-256 at rest · TLS 1.3 in transit · Key rotation 90-day</span><br>'
        '<span style="color:#334155;">Audit:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span><span style="color:#3b82f6;">Every cross-boundary event logged · SHA-256 hash chain · 6-yr retention</span><br>'
        '<span style="color:#334155;">Access:&nbsp;&nbsp;&nbsp;&nbsp;</span><span style="color:#3b82f6;">RBAC · FIDO2 MFA · Auto-logoff 15 min · BAA for all PHI-adjacent vendors</span>'
        '</div>'
    )
    st.markdown(flow_html, unsafe_allow_html=True)

    alert(
        "This CareValidate demo suite operates <strong>entirely in the Safe Zone</strong> — "
        "all patient data is synthetically generated with numpy seeds (no real EHR connection). "
        "The de-identification pipeline above documents the architecture required to safely ingest "
        "real data from a payer or EHR system. In production, this pipeline runs as a pre-processing "
        "step before any data reaches these dashboards. "
        "Source: HIPAA §164.514(b), HHS De-identification Guidance 2012 (updated 2024).",
        level="success",
    )
