"""Streamlit interface for the Multi-Asset Portfolio Risk & Benchmark Monitor."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

from src.config import (
    BENCHMARK_NAME,
    BENCHMARK_SYMBOL,
    DEFAULT_CAPITAL_USD,
    DEFAULT_PORTFOLIO_PATH,
    VAR_LOOKBACK_DAYS,
)
from src.data_loader import prepare_portfolio, read_portfolio
from src.data_quality import overall_quality_status, quality_score, run_data_quality_checks
from src.demo_data import write_demo_portfolio
from src.market_data import MarketDataError, fetch_market_prices
from src.portfolio_analytics import (
    align_prices,
    calculate_portfolio_returns,
    calculate_returns,
    performance_summary,
    return_contribution,
    risk_contribution,
    wealth_index,
    weight_series,
)
from src.reporting import build_markdown_report
from src.risk_metrics import risk_summary, rolling_var_backtest
from src.stress_testing import run_stress_tests


st.set_page_config(
    page_title="Multi-Asset Risk Monitor",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #dbe4f0;
        border-radius: 10px;
        padding: 14px;
        box-shadow: 0 2px 8px rgba(24, 48, 80, 0.05);
    }
    .source-note {
        border-left: 4px solid #2563EB;
        background: #eef4ff;
        padding: 0.7rem 0.9rem;
        border-radius: 4px;
        margin-bottom: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600, show_spinner=False)
def load_market_prices(
    symbols: tuple[str, ...],
    start_date: str,
    end_date: str,
) -> tuple[pd.DataFrame, dict[str, str]]:
    return fetch_market_prices(list(symbols), start_date, end_date)


def money(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    return f"-US${abs(value):,.0f}" if value < 0 else f"US${value:,.0f}"


def percent(value: float) -> str:
    return "N/A" if pd.isna(value) else f"{100 * value:.2f}%"


def status_icon(status: str) -> str:
    return {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(status, "ℹ️")


st.title("📊 Multi-Asset Portfolio Risk & Benchmark Monitor")
st.caption(
    "Synthetic institutional portfolio · published cross-asset prices · benchmark attribution · "
    "rolling out-of-sample risk validation"
)

with st.sidebar:
    st.header("Analysis settings")
    portfolio_source = st.radio(
        "Portfolio source",
        ["Bundled synthetic portfolio", "Upload portfolio CSV"],
    )
    history_years = st.select_slider("Market history", options=[2, 3, 4, 5], value=3)
    capital_usd = st.number_input(
        "Synthetic capital (USD)",
        min_value=100_000,
        max_value=100_000_000,
        value=int(DEFAULT_CAPITAL_USD),
        step=100_000,
    )
    confidence = st.select_slider(
        "VaR confidence", options=[0.90, 0.95, 0.975, 0.99], value=0.95
    )
    risk_free_rate = st.slider("Annual risk-free rate", 0.0, 0.10, 0.02, 0.005)
    inject_issues = st.toggle(
        "Inject controlled data errors",
        value=False,
        help="Creates an allocation break and a missing market observation to demonstrate controls.",
    )
    if portfolio_source == "Upload portfolio CSV":
        portfolio_upload = st.file_uploader("Portfolio CSV", type="csv")
    else:
        portfolio_upload = None
    st.divider()
    st.caption("Educational analytics only — not investment advice or a production risk system.")


try:
    write_demo_portfolio()
    if portfolio_source == "Upload portfolio CSV":
        if portfolio_upload is None:
            st.info("Upload a portfolio CSV to begin. The required schema is documented in README.md.")
            st.stop()
        raw_portfolio = read_portfolio(portfolio_upload)
    else:
        raw_portfolio = read_portfolio(DEFAULT_PORTFOLIO_PATH)
    portfolio = prepare_portfolio(raw_portfolio)

    end_date = date.today() - pd.Timedelta(days=1)
    start_date = end_date - pd.DateOffset(years=history_years)
    symbols = list(dict.fromkeys([BENCHMARK_SYMBOL, *portfolio["symbol"].tolist()]))
    with st.spinner("Retrieving published cross-asset prices..."):
        prices, source_metadata = load_market_prices(
            tuple(symbols), start_date.date().isoformat(), end_date.isoformat()
        )

    if inject_issues:
        portfolio = portfolio.copy()
        portfolio.loc[portfolio.index[0], "target_weight"] -= 0.05
        prices = prices.copy()
        issue_symbol = portfolio["symbol"].iloc[min(1, len(portfolio) - 1)]
        issue_dates = prices.index[prices[BENCHMARK_SYMBOL].notna()]
        if len(issue_dates):
            prices.loc[issue_dates[len(issue_dates) // 2], issue_symbol] = np.nan

    quality_results = run_data_quality_checks(portfolio, prices, BENCHMARK_SYMBOL)
    score = quality_score(quality_results)
    overall_status = overall_quality_status(quality_results)
    failure_count = int(quality_results["status"].eq("FAIL").sum())
    warning_count = int(quality_results["status"].eq("WARN").sum())

    aligned_prices = align_prices(prices, symbols)
    all_returns = calculate_returns(aligned_prices)
    weights = weight_series(portfolio)
    asset_returns = all_returns[weights.index]
    portfolio_returns = calculate_portfolio_returns(asset_returns, weights)
    benchmark_returns = all_returns[BENCHMARK_SYMBOL].rename("benchmark_return")
    performance = performance_summary(portfolio_returns, benchmark_returns, risk_free_rate)
    daily_pnl = (float(capital_usd) * portfolio_returns).rename("daily_pnl_usd")
    risk = risk_summary(daily_pnl, confidence, VAR_LOOKBACK_DAYS)
    backtest = rolling_var_backtest(daily_pnl, confidence, VAR_LOOKBACK_DAYS)
    stresses = run_stress_tests(weights, float(capital_usd))
    risk_contributions = risk_contribution(asset_returns, weights).merge(
        portfolio[["symbol", "asset_name", "asset_class"]], on="symbol", how="left"
    )
    return_contributions = return_contribution(asset_returns, weights).merge(
        portfolio[["symbol", "asset_name", "asset_class"]], on="symbol", how="left"
    )
    indexed_performance = pd.concat(
        [
            wealth_index(portfolio_returns, 100).rename("Synthetic portfolio"),
            wealth_index(benchmark_returns, 100).rename(BENCHMARK_NAME),
        ],
        axis=1,
    ).dropna()
    portfolio_wealth = wealth_index(portfolio_returns, 1.0)
    drawdown = (portfolio_wealth / portfolio_wealth.cummax() - 1).rename("Portfolio drawdown")
except (ValueError, KeyError, MarketDataError, pd.errors.ParserError) as error:
    st.error(f"The analysis could not run: {error}")
    st.info("If the public market feed is temporarily unavailable, wait briefly and rerun the app.")
    st.stop()


st.markdown(
    f"""
    <div class="source-note">
    <strong>Data separation:</strong> company allocation is synthetic; market prices are published adjusted closes
    from <a href="{source_metadata['source_url']}" target="_blank">{source_metadata['source_name']}</a>.
    Period: {source_metadata['first_date']} to {source_metadata['last_date']}. Retrieved {source_metadata['retrieved_at']}.
    </div>
    """,
    unsafe_allow_html=True,
)

overview_tab, performance_tab, risk_tab, allocation_tab, quality_tab, methodology_tab = st.tabs(
    [
        "Executive overview",
        "Performance & benchmark",
        "Risk & stress",
        "Allocation & attribution",
        "Data quality",
        "Methodology",
    ]
)

with overview_tab:
    metrics = st.columns(4)
    metrics[0].metric("Annualized portfolio return", percent(performance["annual_return"]))
    metrics[1].metric("Annualized benchmark return", percent(performance["benchmark_return"]))
    metrics[2].metric("Annualized volatility", percent(performance["annual_volatility"]))
    metrics[3].metric("Maximum drawdown", percent(performance["max_drawdown"]))

    left, right = st.columns([1.7, 1])
    with left:
        st.subheader("Portfolio versus benchmark (indexed to 100)")
        st.line_chart(indexed_performance, height=340)
    with right:
        st.subheader("Management attention")
        st.metric(
            "Data quality score",
            f"{status_icon(overall_status)} {score:.0f}/100",
            help="PASS=1, WARN=0.5 and FAIL=0, averaged across all controls.",
        )
        control_summary = (
            f"{failure_count} critical failure{'s' if failure_count != 1 else ''} · "
            f"{warning_count} warning{'s' if warning_count != 1 else ''}"
        )
        if failure_count:
            st.error(control_summary)
        elif warning_count:
            st.warning(control_summary)
        else:
            st.success(control_summary)

        if pd.notna(risk["breach_rate_pct"]) and risk["breach_rate_pct"] > risk["expected_breach_rate_pct"]:
            st.warning(
                f"VaR breach rate {risk['breach_rate_pct']:.2f}% exceeds the nominal "
                f"{risk['expected_breach_rate_pct']:.2f}% expectation."
            )
        worst = stresses.sort_values("portfolio_pnl_usd").iloc[0]
        st.error(
            f"Most adverse stress: **{worst['scenario']}**  \n"
            f"Instantaneous portfolio impact: **{money(worst['portfolio_pnl_usd'])}**"
        )

    report = build_markdown_report(
        float(capital_usd),
        portfolio,
        performance,
        risk,
        quality_results,
        score,
        stresses,
        source_metadata,
        confidence,
    )
    st.download_button(
        "Download portfolio risk report",
        data=report,
        file_name="multi_asset_portfolio_risk_report.md",
        mime="text/markdown",
    )

with performance_tab:
    st.subheader("Risk-adjusted performance and benchmark diagnostics")
    metrics = st.columns(4)
    metrics[0].metric("Sharpe ratio", f"{performance['sharpe_ratio']:.2f}")
    metrics[1].metric("Portfolio beta", f"{performance['beta']:.2f}")
    metrics[2].metric("Tracking error", percent(performance["tracking_error"]))
    metrics[3].metric("Information ratio", f"{performance['information_ratio']:.2f}")

    left, right = st.columns(2)
    with left:
        st.markdown("#### Indexed performance")
        st.line_chart(indexed_performance, height=320)
    with right:
        st.markdown("#### Portfolio drawdown")
        st.line_chart(drawdown, color="#D64550", height=320)

    st.markdown("#### Daily return correlation")
    correlation = asset_returns.rename(columns=dict(zip(portfolio["symbol"], portfolio["asset_name"]))).corr()
    st.dataframe(correlation.style.format("{:.2f}"), width="stretch")

with risk_tab:
    st.subheader("One-day portfolio risk and rolling out-of-sample validation")
    st.caption(
        f"Each test-day VaR is estimated only from the preceding {VAR_LOOKBACK_DAYS} portfolio P&L observations. "
        "The test-day outcome is never used in its own forecast."
    )
    metrics = st.columns(4)
    metrics[0].metric(f"Historical VaR ({confidence:.1%}, 1-day)", money(risk["historical_var_usd"]))
    metrics[1].metric("Expected Shortfall (1-day)", money(risk["expected_shortfall_usd"]))
    metrics[2].metric("Out-of-sample breaches", f"{int(risk['breach_count'])}")
    metrics[3].metric(
        "Observed / expected rate",
        f"{risk['breach_rate_pct']:.2f}% / {risk['expected_breach_rate_pct']:.2f}%"
        if pd.notna(risk["breach_rate_pct"])
        else "N/A",
    )

    left, right = st.columns(2)
    with left:
        st.markdown("#### Realized P&L versus forecast VaR limit")
        if backtest.empty:
            st.info(f"At least {VAR_LOOKBACK_DAYS + 1} daily observations are required.")
        else:
            st.line_chart(backtest[["pnl_usd", "var_limit_usd"]], height=320)
    with right:
        st.markdown("#### Daily portfolio P&L distribution")
        counts, edges = np.histogram(daily_pnl, bins=30)
        histogram = pd.DataFrame(
            {"observations": counts},
            index=pd.Index(np.round((edges[:-1] + edges[1:]) / 2, 0), name="P&L bin (USD)"),
        )
        st.bar_chart(histogram, color="#7C3AED", height=320)

    st.markdown("#### Deterministic instantaneous stress scenarios")
    st.caption(
        "Stress scenarios apply simultaneous one-time shocks across all asset proxies. "
        "This horizon differs from one-day VaR and the values should not be treated as equivalent measures."
    )
    st.dataframe(
        stresses,
        width="stretch",
        hide_index=True,
        column_config={
            "portfolio_return_pct": st.column_config.NumberColumn(format="%.2f%%"),
            "portfolio_pnl_usd": st.column_config.NumberColumn(format="US$ %.2f"),
            "stressed_value_usd": st.column_config.NumberColumn(format="US$ %.2f"),
        },
    )

with allocation_tab:
    st.subheader("Strategic allocation and attribution")
    allocation = portfolio.set_index("asset_name")[["target_weight"]] * 100
    allocation.columns = ["Target weight (%)"]
    st.bar_chart(allocation, color="#2563EB", height=300)

    left, right = st.columns(2)
    with left:
        st.markdown("#### Contribution to portfolio variance")
        risk_chart = risk_contributions.set_index("asset_name")[["risk_contribution_pct"]]
        st.bar_chart(risk_chart, color="#D64550", height=320)
    with right:
        st.markdown("#### Weighted period-return contribution")
        return_chart = return_contributions.set_index("asset_name")[["weighted_return_contribution_pct"]]
        st.bar_chart(return_chart, color="#18A999", height=320)

    attribution = risk_contributions.merge(
        return_contributions[["symbol", "asset_period_return_pct", "weighted_return_contribution_pct"]],
        on="symbol",
        how="left",
    )
    st.dataframe(
        attribution[
            [
                "symbol",
                "asset_name",
                "asset_class",
                "weight_pct",
                "asset_period_return_pct",
                "weighted_return_contribution_pct",
                "risk_contribution_pct",
            ]
        ],
        width="stretch",
        hide_index=True,
        column_config={
            column: st.column_config.NumberColumn(format="%.2f%%")
            for column in [
                "weight_pct",
                "asset_period_return_pct",
                "weighted_return_contribution_pct",
                "risk_contribution_pct",
            ]
        },
    )

with quality_tab:
    st.subheader("Data controls and exception monitoring")
    metrics = st.columns(4)
    metrics[0].metric("Overall status", f"{status_icon(overall_status)} {overall_status}")
    metrics[1].metric("Quality score", f"{score:.1f}/100")
    metrics[2].metric("Critical failures", failure_count)
    metrics[3].metric("Warnings", warning_count)

    status_filter = st.multiselect(
        "Filter control status", ["PASS", "WARN", "FAIL"], default=["PASS", "WARN", "FAIL"]
    )
    filtered = quality_results[quality_results["status"].isin(status_filter)].copy()
    filtered["status"] = filtered["status"].map(lambda value: f"{status_icon(value)} {value}")
    st.dataframe(filtered, width="stretch", hide_index=True)
    st.info(
        "Enable **Inject controlled data errors** in the sidebar to demonstrate how the app detects "
        "an allocation reconciliation break and missing cross-asset price coverage."
    )

with methodology_tab:
    st.subheader("Methodology, provenance and limitations")
    st.markdown(
        f"""
        **Portfolio construction**

        - The holdings and target weights represent a synthetic investment mandate, not a real employer portfolio.
        - Daily portfolio return is the weighted sum of asset-proxy adjusted-price returns.
        - The demonstration assumes daily rebalancing to constant weights and synthetic capital of {money(float(capital_usd))}.

        **Benchmark and performance**

        - {BENCHMARK_NAME} (`{BENCHMARK_SYMBOL}`) is the benchmark.
        - Sharpe ratio uses the selected annual risk-free assumption of {risk_free_rate:.2%}.
        - Tracking error and information ratio use daily active returns annualized with 252 trading days.
        - Risk contribution uses the sample covariance matrix and component contribution to portfolio variance.

        **Risk horizons**

        - Historical VaR and Expected Shortfall are one-day measures estimated from the previous {VAR_LOOKBACK_DAYS} daily P&Ls.
        - Backtesting is rolling and out of sample.
        - Stress tests are instantaneous, deterministic cross-asset shocks and are not directly comparable with one-day VaR.

        **Data provenance**

        - Market source: [{source_metadata['source_name']}]({source_metadata['source_url']}).
        - Prices are published adjusted-close observations from {source_metadata['first_date']} to {source_metadata['last_date']}.
        - The public chart endpoint is convenient for education but has no production service guarantee or contractual data SLA.

        **Important limitations**

        - No transaction costs, taxes, liquidity constraints, currency conversion, market impact or corporate actions beyond adjusted prices.
        - Constant weights create look-ahead-like implementation simplification unless an explicit rebalance process is added.
        - Historical risk assumes past returns are informative and does not guarantee future loss coverage.
        - Results are educational and must not be used for investment decisions or regulatory reporting.
        """
    )

