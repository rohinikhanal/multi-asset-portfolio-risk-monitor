"""Load and normalize portfolio inputs."""

from __future__ import annotations

from pathlib import Path
from typing import IO

import pandas as pd

PORTFOLIO_COLUMNS = {"symbol", "asset_name", "asset_class", "target_weight"}


def read_portfolio(source: str | Path | IO[bytes]) -> pd.DataFrame:
    """Read a portfolio CSV without silently changing its values."""

    return pd.read_csv(source)


def prepare_portfolio(portfolio: pd.DataFrame) -> pd.DataFrame:
    """Normalize portfolio symbols and weights for analytics."""

    missing = PORTFOLIO_COLUMNS - set(portfolio.columns)
    if missing:
        raise ValueError(f"Portfolio is missing required columns: {', '.join(sorted(missing))}")

    result = portfolio.copy()
    result["symbol"] = result["symbol"].astype(str).str.strip().str.upper()
    result["asset_name"] = result["asset_name"].astype(str).str.strip()
    result["asset_class"] = result["asset_class"].astype(str).str.strip()
    result["target_weight"] = pd.to_numeric(result["target_weight"], errors="coerce")
    return result

