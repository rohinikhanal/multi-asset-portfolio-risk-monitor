"""Deterministic multi-asset stress scenarios."""

from __future__ import annotations

import pandas as pd

SCENARIOS = {
    "Base market": {"SPY": 0.00, "EFA": 0.00, "IEF": 0.00, "GLD": 0.00, "VNQ": 0.00, "DBC": 0.00},
    "Global risk-off": {"SPY": -0.20, "EFA": -0.22, "IEF": 0.05, "GLD": 0.08, "VNQ": -0.18, "DBC": -0.12},
    "Inflation shock": {"SPY": -0.08, "EFA": -0.10, "IEF": -0.12, "GLD": 0.10, "VNQ": -0.15, "DBC": 0.18},
    "Liquidity crisis": {"SPY": -0.25, "EFA": -0.28, "IEF": -0.08, "GLD": 0.03, "VNQ": -0.24, "DBC": -0.15},
    "Growth rally": {"SPY": 0.12, "EFA": 0.14, "IEF": -0.04, "GLD": -0.05, "VNQ": 0.10, "DBC": 0.08},
}


def run_stress_tests(weights: pd.Series, capital_usd: float) -> pd.DataFrame:
    """Apply one-time asset shocks to a constant-weight portfolio."""

    rows = []
    for name, shocks in SCENARIOS.items():
        portfolio_return = sum(float(weights.get(symbol, 0.0)) * shock for symbol, shock in shocks.items())
        rows.append(
            {
                "scenario": name,
                "portfolio_return_pct": 100 * portfolio_return,
                "portfolio_pnl_usd": capital_usd * portfolio_return,
                "stressed_value_usd": capital_usd * (1 + portfolio_return),
            }
        )
    return pd.DataFrame(rows)

