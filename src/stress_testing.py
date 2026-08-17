"""Deterministic scenarios applied by asset class rather than ticker."""

from __future__ import annotations

import pandas as pd

from .asset_classes import SUPPORTED_ASSET_CLASSES, normalize_asset_class


SCENARIOS = {
    "Base market": {
        "Equity": 0.00,
        "Fixed income": 0.00,
        "Commodity": 0.00,
        "Gold": 0.00,
        "Real estate": 0.00,
        "Crypto": 0.00,
        "Cash": 0.00,
    },
    "Global risk-off": {
        "Equity": -0.20,
        "Fixed income": 0.05,
        "Commodity": -0.10,
        "Gold": 0.08,
        "Real estate": -0.18,
        "Crypto": -0.30,
        "Cash": 0.00,
    },
    "Inflation shock": {
        "Equity": -0.08,
        "Fixed income": -0.12,
        "Commodity": 0.18,
        "Gold": 0.10,
        "Real estate": -0.15,
        "Crypto": -0.15,
        "Cash": 0.00,
    },
    "Liquidity crisis": {
        "Equity": -0.25,
        "Fixed income": -0.08,
        "Commodity": -0.15,
        "Gold": 0.03,
        "Real estate": -0.24,
        "Crypto": -0.35,
        "Cash": 0.00,
    },
    "Growth rally": {
        "Equity": 0.12,
        "Fixed income": -0.04,
        "Commodity": 0.08,
        "Gold": -0.05,
        "Real estate": 0.10,
        "Crypto": 0.20,
        "Cash": 0.00,
    },
}


def _stress_positions(portfolio: pd.DataFrame) -> pd.DataFrame:
    """Return normalized positions and reject any scenario coverage gap."""

    required = ["symbol", "asset_name", "asset_class", "target_weight"]
    missing = set(required) - set(portfolio.columns)
    if missing:
        raise ValueError(f"Stress testing is missing columns: {', '.join(sorted(missing))}")

    positions = portfolio[required].copy()
    positions["asset_class"] = positions["asset_class"].map(normalize_asset_class)
    positions["target_weight"] = pd.to_numeric(positions["target_weight"], errors="coerce")
    if positions["target_weight"].isna().any() or positions["target_weight"].sum() <= 0:
        raise ValueError("Stress testing requires positive numeric portfolio weights.")
    positions["weight"] = positions["target_weight"] / positions["target_weight"].sum()

    unsupported = sorted(
        set(positions.loc[~positions["asset_class"].isin(SUPPORTED_ASSET_CLASSES), "asset_class"])
    )
    if unsupported:
        allowed = ", ".join(SUPPORTED_ASSET_CLASSES)
        raise ValueError(
            f"Unsupported asset class for stress testing: {', '.join(unsupported)}. "
            f"Use one of: {allowed}."
        )
    return positions


def run_stress_tests(portfolio: pd.DataFrame, capital_usd: float) -> pd.DataFrame:
    """Apply every scenario to 100% of the portfolio through asset-class mapping."""

    positions = _stress_positions(portfolio)
    rows = []
    for name, class_shocks in SCENARIOS.items():
        shocks = positions["asset_class"].map(class_shocks)
        portfolio_return = float((positions["weight"] * shocks).sum())
        rows.append(
            {
                "scenario": name,
                "portfolio_return_pct": 100 * portfolio_return,
                "portfolio_pnl_usd": capital_usd * portfolio_return,
                "stressed_value_usd": capital_usd * (1 + portfolio_return),
                "positions_covered": len(positions),
                "coverage_pct": 100.0,
            }
        )
    return pd.DataFrame(rows)


def stress_position_detail(
    portfolio: pd.DataFrame,
    capital_usd: float,
    scenario_name: str,
) -> pd.DataFrame:
    """Return the position-level shock and P&L contribution for one scenario."""

    if scenario_name not in SCENARIOS:
        raise ValueError(f"Unknown stress scenario: {scenario_name}")
    positions = _stress_positions(portfolio)
    positions["shock_pct"] = 100 * positions["asset_class"].map(SCENARIOS[scenario_name])
    positions["pnl_contribution_usd"] = (
        capital_usd * positions["weight"] * positions["shock_pct"] / 100
    )
    positions["weight_pct"] = 100 * positions["weight"]
    return positions[
        [
            "symbol",
            "asset_name",
            "asset_class",
            "weight_pct",
            "shock_pct",
            "pnl_contribution_usd",
        ]
    ]


def stress_assumption_table() -> pd.DataFrame:
    """Return scenarios as a human-readable asset-class shock matrix."""

    result = pd.DataFrame(SCENARIOS).T[list(SUPPORTED_ASSET_CLASSES)] * 100
    result.index.name = "scenario"
    return result.reset_index()
