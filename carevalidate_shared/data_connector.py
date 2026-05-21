"""
CareValidate Data Connector
Abstraction layer between dashboards and data sources.

Usage:
    from carevalidate_shared.data_connector import DataConnector
    dc = DataConnector()
    referrals = dc.get_referrals(date_from, date_to)

Modes (set via environment variable or config):
    CV_LIVE_DATA=false  →  synthetic data (default, demo-safe)
    CV_LIVE_DATA=true   →  reads CSVs from CV_DATA_DIR

Production upgrade path:
    1. Set CV_LIVE_DATA=true and CV_DATA_DIR to your data drop folder
    2. Replace CSV loaders with API calls (ReferWell Engage, health plan SFTP)
    3. Add caching with @st.cache_data(ttl=3600) wrappers
"""
import os
import datetime
import numpy as np
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
USE_LIVE_DATA = os.environ.get("CV_LIVE_DATA", "false").lower() == "true"
DATA_DIR      = os.environ.get("CV_DATA_DIR", r"C:\Users\Owner\carevalidate_data")
_SOURCE_LABEL = "Live Data" if USE_LIVE_DATA else "Synthetic · Demo Mode"


class DataConnector:
    """
    Single entry point for all dashboard data.
    Swap USE_LIVE_DATA env var to toggle between synthetic and real data.
    """

    def __init__(self):
        self.live = USE_LIVE_DATA
        self.source = _SOURCE_LABEL

    # ── Source label (display in dashboards) ─────────────────────────────────
    def source_badge(self) -> str:
        if self.live:
            return "🟢 Live Data"
        return "🔵 Synthetic · Demo Mode"

    # ── Date helpers ─────────────────────────────────────────────────────────
    @staticmethod
    def default_date_range(days: int = 30):
        end   = datetime.date.today()
        start = end - datetime.timedelta(days=days)
        return start, end

    # ── Referrals (ReferWell Engage export) ──────────────────────────────────
    def get_referrals(
        self,
        date_from: datetime.date = None,
        date_to:   datetime.date = None,
    ) -> pd.DataFrame:
        if self.live:
            path = os.path.join(DATA_DIR, "referrals.csv")
            df   = pd.read_csv(path, parse_dates=["date"])
            if date_from:
                df = df[df["date"].dt.date >= date_from]
            if date_to:
                df = df[df["date"].dt.date <= date_to]
            return df
        # Synthetic fallback
        rng  = np.random.default_rng(42)
        days = (date_to - date_from).days if (date_from and date_to) else 30
        dates = pd.date_range(end=datetime.date.today(), periods=days, freq="D")
        return pd.DataFrame({
            "date":       dates,
            "scheduled":  rng.integers(40, 60, size=days),
            "confirmed":  rng.integers(35, 55, size=days),
            "completed":  rng.integers(30, 50, size=days),
            "no_show":    rng.integers(3,  10, size=days),
            "rescheduled":rng.integers(2,  8,  size=days),
        })

    # ── Navigator productivity ────────────────────────────────────────────────
    def get_navigator_metrics(
        self,
        date_from: datetime.date = None,
        date_to:   datetime.date = None,
    ) -> pd.DataFrame:
        if self.live:
            path = os.path.join(DATA_DIR, "navigator_metrics.csv")
            df   = pd.read_csv(path, parse_dates=["date"])
            if date_from:
                df = df[df["date"].dt.date >= date_from]
            if date_to:
                df = df[df["date"].dt.date <= date_to]
            return df
        # Synthetic: 15 navigators
        rng = np.random.default_rng(7)
        names = [
            "Maria G.", "James T.", "Anh N.", "Carlos R.", "Fatima A.",
            "Lin W.", "Samuel O.", "Priya K.", "Dmitri V.", "Elena M.",
            "Kwame A.", "Sara J.", "Miguel F.", "Yuki T.", "Amara D.",
        ]
        markets = ["Northeast", "Southeast", "Midwest", "West", "Southwest"]
        return pd.DataFrame({
            "navigator":    names,
            "market":       [markets[i % 5] for i in range(15)],
            "refs_mo":      rng.integers(80, 130, size=15),
            "show_rate":    rng.uniform(0.82, 0.96, size=15).round(3),
            "completion":   rng.uniform(0.74, 0.92, size=15).round(3),
            "csat":         rng.uniform(4.1, 4.9, size=15).round(1),
        })

    # ── HEDIS measure rates ───────────────────────────────────────────────────
    def get_hedis_rates(self) -> pd.DataFrame:
        if self.live:
            path = os.path.join(DATA_DIR, "hedis_rates.csv")
            return pd.read_csv(path)
        return pd.DataFrame({
            "measure":    ["COL-E", "CBP",  "CDC",  "BCS-E", "AWV",  "COA",  "TRC"],
            "rate":       [0.761,   0.683,  0.724,  0.798,   0.841,  0.712,  0.658],
            "ncqa_avg":   [0.681,   0.647,  0.689,  0.741,   0.802,  0.679,  0.632],
            "stars_floor":[0.70,    0.68,   0.71,   0.76,    0.80,   0.70,   0.68],
        })

    # ── Claims / reconciliation ───────────────────────────────────────────────
    def get_transactions(
        self,
        date_from: datetime.date = None,
        date_to:   datetime.date = None,
        n: int = 480,
    ) -> pd.DataFrame:
        if self.live:
            path = os.path.join(DATA_DIR, "transactions.csv")
            df   = pd.read_csv(path, parse_dates=["date"])
            if date_from:
                df = df[df["date"].dt.date >= date_from]
            if date_to:
                df = df[df["date"].dt.date <= date_to]
            return df
        rng = np.random.default_rng(42)
        end  = date_to   or datetime.date.today()
        start= date_from or (end - datetime.timedelta(days=30))
        dates = [start + datetime.timedelta(days=int(d))
                 for d in rng.integers(0, (end - start).days + 1, size=n)]
        statuses = rng.choice(
            ["MATCHED", "DISCREPANCY", "PENDING", "FAILED", "DUPLICATE"],
            size=n, p=[0.84, 0.05, 0.07, 0.02, 0.02],
        )
        return pd.DataFrame({
            "date":     sorted(dates),
            "amount":   rng.uniform(150, 4200, size=n).round(2),
            "status":   statuses,
            "category": rng.choice(
                ["Medicare Advantage", "Medicaid LTSS", "Commercial HMO",
                 "ACO MSSP", "Dual-Eligible", "Employer", "Pharmacy", "Lab"],
                size=n,
            ),
        })

    # ── MRR time series ───────────────────────────────────────────────────────
    def get_mrr_series(
        self,
        date_from: datetime.date = None,
        date_to:   datetime.date = None,
    ) -> pd.DataFrame:
        if self.live:
            path = os.path.join(DATA_DIR, "mrr_series.csv")
            df   = pd.read_csv(path, parse_dates=["month"])
            if date_from:
                df = df[df["month"].dt.date >= date_from]
            if date_to:
                df = df[df["month"].dt.date <= date_to]
            return df
        rng    = np.random.default_rng(42)
        months = pd.date_range(end=datetime.date.today(), periods=13, freq="MS")
        base   = 3_200_000
        mrr    = [int(base * (1 + 0.07) ** i + rng.integers(-40000, 80000))
                  for i in range(13)]
        return pd.DataFrame({"month": months, "mrr": mrr})


# ── CSV template generator ─────────────────────────────────────────────────────
def generate_csv_templates(output_dir: str = DATA_DIR):
    """
    Run once to generate empty CSV templates with correct column headers.
    Fill these with real data to switch to live mode.
    Usage: python -c "from carevalidate_shared.data_connector import generate_csv_templates; generate_csv_templates()"
    """
    os.makedirs(output_dir, exist_ok=True)
    templates = {
        "referrals.csv":          ["date", "scheduled", "confirmed", "completed", "no_show", "rescheduled"],
        "navigator_metrics.csv":  ["date", "navigator", "market", "refs_mo", "show_rate", "completion", "csat"],
        "hedis_rates.csv":        ["measure", "rate", "ncqa_avg", "stars_floor"],
        "transactions.csv":       ["date", "amount", "status", "category"],
        "mrr_series.csv":         ["month", "mrr"],
    }
    for fname, cols in templates.items():
        path = os.path.join(output_dir, fname)
        if not os.path.exists(path):
            pd.DataFrame(columns=cols).to_csv(path, index=False)
            print(f"Created template: {path}")
        else:
            print(f"Exists (skipped): {path}")
