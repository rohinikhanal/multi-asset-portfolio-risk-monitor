"""Portfolio and market-data validation controls."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .data_loader import PORTFOLIO_COLUMNS


@dataclass(frozen=True)
class CheckResult:
    category: str
    check: str
    status: str
    failed_records: int
    details: str


def _result(category: str, check: str, count: int, details: str, warning: bool = False) -> CheckResult:
    status = "PASS" if count == 0 else ("WARN" if warning else "FAIL")
    return CheckResult(category, check, status, int(count), details)


def portfolio_checks(portfolio: pd.DataFrame) -> list[CheckResult]:
    """Validate schema, identifiers and portfolio weights."""

    missing = sorted(PORTFOLIO_COLUMNS - set(portfolio.columns))
    results = [
        _result(
            "Portfolio",
            "Required columns",
            len(missing),
            "All required columns are present." if not missing else f"Missing: {', '.join(missing)}",
        )
    ]
    if missing:
        return results

    duplicates = int(portfolio["symbol"].duplicated(keep=False).sum())
    results.append(_result("Portfolio", "Unique symbols", duplicates, f"Found {duplicates} duplicate symbol rows."))

    invalid_weights = int(
        (portfolio["target_weight"].isna() | (portfolio["target_weight"] < 0)).sum()
    )
    results.append(
        _result("Portfolio", "Non-negative numeric weights", invalid_weights, f"Found {invalid_weights} invalid weights.")
    )

    weight_total = float(portfolio["target_weight"].sum())
    total_break = int(not np.isclose(weight_total, 1.0, atol=0.001))
    results.append(
        _result(
            "Portfolio",
            "Weights sum to 100%",
            total_break,
            f"Portfolio weights sum to {100 * weight_total:.2f}%.",
        )
    )
    return results


def market_checks(
    prices: pd.DataFrame,
    required_symbols: list[str],
    benchmark_symbol: str,
) -> list[CheckResult]:
    """Validate published market-series coverage, freshness and plausibility."""

    missing_symbols = sorted(set(required_symbols) - set(prices.columns))
    results = [
        _result(
            "Market data",
            "Required price series",
            len(missing_symbols),
            "All required market series are present."
            if not missing_symbols
            else f"Missing series: {', '.join(missing_symbols)}",
        )
    ]
    if missing_symbols:
        return results

    duplicate_dates = int(prices.index.duplicated(keep=False).sum())
    results.append(_result("Market data", "Unique dates", duplicate_dates, f"Found {duplicate_dates} duplicate dates."))

    nonpositive = int((prices[required_symbols] <= 0).sum().sum())
    results.append(
        _result("Market data", "Positive adjusted prices", nonpositive, f"Found {nonpositive} non-positive values.")
    )

    reference_dates = prices.index[prices[benchmark_symbol].notna()]
    reference = prices.loc[reference_dates, required_symbols]
    missing_values = int(reference.isna().sum().sum())
    results.append(
        _result(
            "Market data",
            "Cross-asset date coverage",
            missing_values,
            f"Found {missing_values} missing asset values on benchmark trading dates.",
            warning=True,
        )
    )

    aligned = reference.ffill(limit=3)
    extreme_moves = int((aligned.pct_change(fill_method=None).abs() > 0.35).sum().sum())
    results.append(
        _result(
            "Market data",
            "Extreme daily-return monitoring",
            extreme_moves,
            f"Found {extreme_moves} absolute daily moves above 35%.",
            warning=True,
        )
    )

    short_history = int(len(reference.dropna(how="all")) < 252)
    results.append(
        _result(
            "Market data",
            "Minimum one-year history",
            short_history,
            f"Found {len(reference.dropna(how='all'))} benchmark trading dates.",
        )
    )
    return results


def run_data_quality_checks(
    portfolio: pd.DataFrame,
    prices: pd.DataFrame,
    benchmark_symbol: str,
) -> pd.DataFrame:
    """Run all portfolio and market-data controls."""

    results = portfolio_checks(portfolio)
    if PORTFOLIO_COLUMNS.issubset(portfolio.columns):
        symbols = list(dict.fromkeys([benchmark_symbol, *portfolio["symbol"].tolist()]))
        results.extend(market_checks(prices, symbols, benchmark_symbol))
    return pd.DataFrame([asdict(result) for result in results])


def quality_score(results: pd.DataFrame) -> float:
    """Return PASS=1, WARN=0.5 and FAIL=0 as a transparent score."""

    if results.empty:
        return 0.0
    weights = results["status"].map({"PASS": 1.0, "WARN": 0.5, "FAIL": 0.0})
    return float(np.round(100 * weights.fillna(0).mean(), 1))


def overall_quality_status(results: pd.DataFrame) -> str:
    statuses = set(results.get("status", pd.Series(dtype=str)))
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"

