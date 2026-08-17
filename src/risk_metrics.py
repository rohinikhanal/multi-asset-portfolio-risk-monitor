"""Historical VaR, Expected Shortfall and rolling out-of-sample backtesting."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _clean_pnl(pnl: pd.Series) -> pd.Series:
    return pd.to_numeric(pnl, errors="coerce").dropna().astype(float).sort_index()


def historical_var(pnl: pd.Series, confidence: float = 0.95) -> float:
    """Return positive one-day historical Value at Risk."""

    if not 0 < confidence < 1:
        raise ValueError("Confidence must be between 0 and 1.")
    clean = _clean_pnl(pnl)
    if clean.empty:
        return float("nan")
    return float(max(0.0, np.quantile(-clean, confidence)))


def expected_shortfall(pnl: pd.Series, confidence: float = 0.95) -> float:
    """Return the average loss at or beyond historical VaR."""

    clean = _clean_pnl(pnl)
    if clean.empty:
        return float("nan")
    var_value = historical_var(clean, confidence)
    tail = (-clean)[(-clean) >= var_value]
    return float(max(var_value, tail.mean())) if not tail.empty else var_value


def rolling_var_backtest(
    pnl: pd.Series,
    confidence: float = 0.95,
    lookback: int = 90,
) -> pd.DataFrame:
    """Forecast each test-day VaR using only the preceding lookback window."""

    if not isinstance(lookback, int) or isinstance(lookback, bool) or lookback < 2:
        raise ValueError("Lookback must be an integer of at least 2 observations.")
    clean = _clean_pnl(pnl)
    columns = ["pnl_usd", "var_usd", "var_limit_usd", "breach"]
    if len(clean) <= lookback:
        return pd.DataFrame(columns=columns, index=clean.index[:0])

    records = []
    dates = []
    for position in range(lookback, len(clean)):
        history = clean.iloc[position - lookback : position]
        var_value = historical_var(history, confidence)
        actual = float(clean.iloc[position])
        records.append(
            {
                "pnl_usd": actual,
                "var_usd": var_value,
                "var_limit_usd": -var_value,
                "breach": actual < -var_value,
            }
        )
        dates.append(clean.index[position])
    return pd.DataFrame(records, index=pd.Index(dates, name=clean.index.name))[columns]


def risk_summary(
    pnl: pd.Series,
    confidence: float = 0.95,
    lookback: int = 90,
) -> dict[str, float]:
    """Return next-day risk estimates and out-of-sample breach statistics."""

    clean = _clean_pnl(pnl)
    backtest = rolling_var_backtest(clean, confidence, lookback)
    estimation = clean.iloc[-lookback:]
    breach_rate = float(100 * backtest["breach"].mean()) if not backtest.empty else float("nan")
    return {
        "historical_var_usd": historical_var(estimation, confidence),
        "expected_shortfall_usd": expected_shortfall(estimation, confidence),
        "estimation_observations": float(len(estimation)),
        "backtest_observations": float(len(backtest)),
        "breach_count": float(backtest["breach"].sum()) if not backtest.empty else 0.0,
        "breach_rate_pct": breach_rate,
        "expected_breach_rate_pct": float(100 * (1 - confidence)),
        "lookback_days": float(lookback),
    }

