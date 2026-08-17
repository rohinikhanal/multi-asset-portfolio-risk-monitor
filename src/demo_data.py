"""Deterministic synthetic portfolio data for the demonstration."""

from __future__ import annotations

import pandas as pd

from .config import ASSET_CATALOG, DEFAULT_PORTFOLIO_PATH, DEFAULT_WEIGHTS


def build_demo_portfolio() -> pd.DataFrame:
    """Return a synthetic institutional strategic-allocation portfolio."""

    rows = []
    for symbol, weight in DEFAULT_WEIGHTS.items():
        metadata = ASSET_CATALOG[symbol]
        rows.append(
            {
                "symbol": symbol,
                "asset_name": metadata["asset_name"],
                "asset_class": metadata["asset_class"],
                "target_weight": weight,
            }
        )
    return pd.DataFrame(rows)


def write_demo_portfolio(path=DEFAULT_PORTFOLIO_PATH) -> None:
    """Write the bundled portfolio when it is not already present."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        build_demo_portfolio().to_csv(path, index=False)

