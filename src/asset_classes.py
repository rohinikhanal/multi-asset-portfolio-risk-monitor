"""Canonical asset classes shared by uploads, controls and stress testing."""

from __future__ import annotations


SUPPORTED_ASSET_CLASSES = (
    "Equity",
    "Fixed income",
    "Commodity",
    "Gold",
    "Real estate",
    "Crypto",
    "Cash",
)

_ASSET_CLASS_ALIASES = {
    "equity": "Equity",
    "equities": "Equity",
    "stock": "Equity",
    "stocks": "Equity",
    "fixed income": "Fixed income",
    "fixed-income": "Fixed income",
    "bond": "Fixed income",
    "bonds": "Fixed income",
    "commodity": "Commodity",
    "commodities": "Commodity",
    "gold": "Gold",
    "real estate": "Real estate",
    "real-estate": "Real estate",
    "reit": "Real estate",
    "reits": "Real estate",
    "crypto": "Crypto",
    "cryptocurrency": "Crypto",
    "cash": "Cash",
    "cash equivalent": "Cash",
    "cash equivalents": "Cash",
}


def normalize_asset_class(value: object) -> str:
    """Normalize common upload aliases while retaining unknown values for validation."""

    cleaned = " ".join(str(value).strip().split())
    return _ASSET_CLASS_ALIASES.get(cleaned.casefold(), cleaned)

