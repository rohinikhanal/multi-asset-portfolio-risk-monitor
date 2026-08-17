"""Project configuration and the synthetic investment mandate."""

from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PORTFOLIO_PATH = ROOT_DIR / "data" / "portfolio.csv"

DEFAULT_CAPITAL_USD = 1_000_000.0
DEFAULT_START_DATE = "2023-01-01"
VAR_LOOKBACK_DAYS = 90

ASSET_CATALOG = {
    "SPY": {"asset_name": "U.S. large-cap equity", "asset_class": "Equity"},
    "EFA": {"asset_name": "Developed markets ex-U.S.", "asset_class": "Equity"},
    "IEF": {"asset_name": "U.S. Treasury bonds", "asset_class": "Fixed income"},
    "GLD": {"asset_name": "Gold", "asset_class": "Gold"},
    "VNQ": {"asset_name": "U.S. listed real estate", "asset_class": "Real estate"},
    "DBC": {"asset_name": "Broad commodities", "asset_class": "Commodity"},
}

DEFAULT_WEIGHTS = {
    "SPY": 0.30,
    "EFA": 0.20,
    "IEF": 0.20,
    "GLD": 0.10,
    "VNQ": 0.10,
    "DBC": 0.10,
}
