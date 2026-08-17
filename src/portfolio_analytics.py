"""Portfolio return, benchmark, drawdown and attribution calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def weight_series(portfolio: pd.DataFrame) -> pd.Series:
    """Return portfolio weights indexed by symbol."""

    weights = portfolio.set_index("symbol")["target_weight"].astype(float)
    return weights / weights.sum()


def align_prices(prices: pd.DataFrame, required_symbols: list[str]) -> pd.DataFrame:
    """Align assets to common business dates with limited holiday filling."""

    missing = sorted(set(required_symbols) - set(prices.columns))
    if missing:
        raise ValueError(f"Missing price series: {', '.join(missing)}")
    benchmark_dates = prices.index[prices[required_symbols[0]].notna()]
    aligned = prices.loc[benchmark_dates, required_symbols].ffill(limit=3).dropna()
    if len(aligned) < 2:
        raise ValueError("Not enough aligned prices to calculate portfolio returns.")
    return aligned


def calculate_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Calculate simple daily returns without implicit missing-value filling."""

    return prices.pct_change(fill_method=None).dropna(how="any")


def calculate_portfolio_returns(
    asset_returns: pd.DataFrame,
    weights: pd.Series,
) -> pd.Series:
    """Calculate daily returns for a constant-weight portfolio."""

    result = asset_returns[weights.index].mul(weights, axis=1).sum(axis=1)
    result.name = "portfolio_return"
    return result


def wealth_index(returns: pd.Series, initial_value: float = 100.0) -> pd.Series:
    """Convert a return series into a cumulative wealth index."""

    result = initial_value * (1.0 + returns.fillna(0.0)).cumprod()
    result.name = returns.name
    return result


def max_drawdown(returns: pd.Series) -> float:
    """Return the most negative peak-to-trough drawdown."""

    wealth = wealth_index(returns, 1.0)
    drawdown = wealth / wealth.cummax() - 1.0
    return float(drawdown.min()) if not drawdown.empty else float("nan")


def performance_summary(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.0,
) -> dict[str, float]:
    """Return annualized portfolio and benchmark performance statistics."""

    combined = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
    combined.columns = ["portfolio", "benchmark"]
    if combined.empty:
        return {key: float("nan") for key in (
            "annual_return", "annual_volatility", "sharpe_ratio", "max_drawdown",
            "benchmark_return", "tracking_error", "information_ratio", "beta",
        )}

    portfolio = combined["portfolio"]
    benchmark = combined["benchmark"]
    years_factor = TRADING_DAYS / len(portfolio)
    annual_return = float((1 + portfolio).prod() ** years_factor - 1)
    benchmark_return = float((1 + benchmark).prod() ** years_factor - 1)
    annual_volatility = float(portfolio.std(ddof=1) * np.sqrt(TRADING_DAYS))
    daily_risk_free = (1 + risk_free_rate) ** (1 / TRADING_DAYS) - 1
    sharpe = (
        float((portfolio.mean() - daily_risk_free) / portfolio.std(ddof=1) * np.sqrt(TRADING_DAYS))
        if portfolio.std(ddof=1) > 0
        else float("nan")
    )
    active = portfolio - benchmark
    tracking_error = float(active.std(ddof=1) * np.sqrt(TRADING_DAYS))
    information_ratio = (
        float(active.mean() / active.std(ddof=1) * np.sqrt(TRADING_DAYS))
        if active.std(ddof=1) > 0
        else float("nan")
    )
    benchmark_variance = benchmark.var(ddof=1)
    beta = (
        float(portfolio.cov(benchmark) / benchmark_variance)
        if benchmark_variance > 0
        else float("nan")
    )
    return {
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_drawdown(portfolio),
        "benchmark_return": benchmark_return,
        "tracking_error": tracking_error,
        "information_ratio": information_ratio,
        "beta": beta,
    }


def risk_contribution(asset_returns: pd.DataFrame, weights: pd.Series) -> pd.DataFrame:
    """Estimate component contribution to portfolio variance."""

    covariance = asset_returns[weights.index].cov() * TRADING_DAYS
    marginal = covariance.to_numpy() @ weights.to_numpy()
    portfolio_variance = float(weights.to_numpy() @ marginal)
    contributions = (
        weights.to_numpy() * marginal / portfolio_variance
        if portfolio_variance > 0
        else np.zeros(len(weights))
    )
    return pd.DataFrame(
        {
            "symbol": weights.index,
            "weight_pct": 100 * weights.to_numpy(),
            "risk_contribution_pct": 100 * contributions,
        }
    )


def return_contribution(asset_returns: pd.DataFrame, weights: pd.Series) -> pd.DataFrame:
    """Return weighted buy-and-hold period-return contributions by asset."""

    period_returns = (1 + asset_returns[weights.index]).prod() - 1
    contribution = period_returns * weights
    return pd.DataFrame(
        {
            "symbol": weights.index,
            "asset_period_return_pct": 100 * period_returns.to_numpy(),
            "weighted_return_contribution_pct": 100 * contribution.to_numpy(),
        }
    )

