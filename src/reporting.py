"""Generate a portable Markdown portfolio-risk report."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def _money(value: float) -> str:
    return f"-USD {abs(value):,.2f}" if value < 0 else f"USD {value:,.2f}"


def _percent(value: float) -> str:
    return "N/A" if pd.isna(value) else f"{100 * value:.2f}%"


def build_markdown_report(
    capital_usd: float,
    portfolio: pd.DataFrame,
    performance: dict[str, float],
    risk: dict[str, float],
    quality_results: pd.DataFrame,
    quality_score_value: float,
    stress_results: pd.DataFrame,
    source_metadata: dict[str, str],
    confidence: float,
) -> str:
    """Return an interview-ready management report."""

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    failures = quality_results[quality_results["status"].eq("FAIL")]
    warnings = quality_results[quality_results["status"].eq("WARN")]
    worst_stress = stress_results.sort_values("portfolio_pnl_usd").iloc[0]
    allocations = "\n".join(
        f"- {row.symbol} / {row.asset_name}: {100 * row.target_weight:.1f}%"
        for row in portfolio.itertuples()
    )
    failure_lines = (
        "\n".join(f"- {row.check}: {row.details}" for row in failures.itertuples())
        if not failures.empty
        else "- No critical failures."
    )
    warning_lines = (
        "\n".join(f"- {row.check}: {row.details}" for row in warnings.itertuples())
        if not warnings.empty
        else "- No warnings."
    )

    return f"""# Multi-Asset Portfolio Risk & Benchmark Report

Generated: {generated}

## Executive summary

- Synthetic portfolio capital: {_money(capital_usd)}
- Annualized portfolio return: {_percent(performance['annual_return'])}
- Annualized benchmark return: {_percent(performance['benchmark_return'])}
- Annualized volatility: {_percent(performance['annual_volatility'])}
- Maximum drawdown: {_percent(performance['max_drawdown'])}
- Sharpe ratio: {performance['sharpe_ratio']:.2f}
- One-day Historical VaR ({confidence:.0%}): {_money(risk['historical_var_usd'])}
- One-day Expected Shortfall ({confidence:.0%}): {_money(risk['expected_shortfall_usd'])}
- Rolling out-of-sample backtest: {int(risk['breach_count'])} breaches over {int(risk['backtest_observations'])} days
- Data-quality score: {quality_score_value:.1f}/100 ({len(failures)} critical failures, {len(warnings)} warnings)
- Most adverse deterministic stress: {worst_stress['scenario']} ({_money(worst_stress['portfolio_pnl_usd'])})

## Strategic allocation

{allocations}

## Data-quality exceptions

### Critical failures

{failure_lines}

### Warnings

{warning_lines}

## Data provenance

- Company portfolio: synthetic demonstration data
- Market prices: {source_metadata['source_name']}
- Market-data period: {source_metadata['first_date']} to {source_metadata['last_date']}
- Retrieved: {source_metadata['retrieved_at']}
- Limitation: {source_metadata['disclaimer']}

## Methodology and limitations

Portfolio returns assume daily constant weights and exclude fees, taxes, bid-ask spreads,
market impact and rebalancing costs. VaR and Expected Shortfall are one-day estimates from
the latest {int(risk['lookback_days'])} portfolio P&L observations. Backtest estimates use
only information available before each test day. Stress scenarios are instantaneous,
deterministic full-portfolio shocks and are not directly comparable to one-day VaR.
The portfolio is synthetic and the public price feed has no production service guarantee.
This educational output is not investment advice or a regulatory risk report.
"""

