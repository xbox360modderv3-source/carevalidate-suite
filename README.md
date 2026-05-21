# CareValidate Finance Suite — Prototype

A 12-dashboard financial analytics prototype for care navigation operations finance.
Built as a skills demonstration for CFO-level review of ReferWell-style platform economics.

> **Synthetic data only. No PHI. No real CareValidate, ReferWell, patient, payer,
> provider, or payment data is used or stored anywhere in this application.**
>
> This is a prototype. It is not production-ready and does not certify HIPAA
> compliance, MLR qualification, CMS Stars eligibility, or any legal or regulatory status.
> Production deployment would require legal, compliance, security, and access-control review.

---

## Dashboards

| # | Name | Description |
|---|------|-------------|
| 01 | Command Center | CFO morning view — KPIs, ReferWell benchmark calibration |
| 02 | GLP-1 Scenarios | FDA compounded semaglutide ban impact modeling |
| 03 | Unit Economics | CAC, LTV, payback, cohort retention, PMPM |
| 04 | Employer ROI | B2B ROI calculator for employer health programs |
| 05 | Churn Engine | Predictive churn flags — illustrative ML model |
| 06 | Series A Data Room | Investor-ready metrics package |
| 07 | Compliance Monitor | Contract billing deviation detection |
| 08 | Retention Ops | Refill gap alerts, cohort survival, engagement scoring |
| 09 | CFO Suite | Monthly pack, 13-week cash flow, MLR finance scenario model |
| 10 | Navigator Ops | FTE productivity, capacity planning, per-FTE ROI |
| 11 | Security & Compliance Readiness | RBAC, audit trail, BAA tracker — illustrative controls |
| 12 | Reconciliation Engine | Auto-match, exception queue, SLA aging |

---

## Setup

### Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Configure credentials

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
2. Generate password hashes:
   ```bash
   python -c "import hashlib; print(hashlib.sha256(b'YourPassword').hexdigest())"
   ```
3. Fill in hashes in `secrets.toml`

`secrets.toml` is gitignored and must never be committed.

### Streamlit Cloud deployment

1. Push repo to GitHub
2. Connect at share.streamlit.io
3. Set secrets in app Settings → Secrets (paste the `[credentials]` block)

---

## Tech stack

- Python 3.10+
- Streamlit 1.30+
- Plotly 5.18+
- Pandas / NumPy

---

## Disclaimer

All financial figures, KPIs, benchmarks, and analytics outputs are synthetic and
illustrative. Sources cited (ReferWell published outcomes, NCQA HEDIS, CMS Stars,
Milliman, Rock Health) are public benchmarks used as modeling inputs — not live data.

Not affiliated with CareValidate or ReferWell.
