# Multi-Asset Portfolio Risk & Benchmark Monitor

An interactive Python and Streamlit application that combines a **synthetic
institutional portfolio** with **published cross-asset market prices**. It measures
risk-adjusted performance, benchmark-relative results, rolling out-of-sample VaR,
cross-asset stress losses, concentration, attribution, and data quality.

This is an educational portfolio project for quantitative-risk, portfolio-analytics,
trading-analyst, asset-management, model-validation, and data-analyst applications.

## Business question

> Did the portfolio outperform its benchmark, which assets created its return and
> risk, does the VaR model work on unseen days, and where would losses come from in a
> cross-asset market shock?

## What makes it useful

- Separates synthetic company data from published market observations.
- Retrieves adjusted daily prices for equity, fixed-income, commodity, and real-estate
  proxies.
- Compares the portfolio with an S&P 500 proxy rather than presenting returns alone.
- Measures annualized return, volatility, Sharpe ratio, beta, tracking error,
  information ratio, and maximum drawdown.
- Attributes period return and portfolio variance contribution by asset.
- Calculates one-day Historical VaR and Expected Shortfall.
- Runs a rolling 90-day out-of-sample VaR backtest without using the test-day P&L in
  its own forecast.
- Separates one-day VaR from instantaneous full-portfolio stress scenarios.
- Validates weights, symbols, price coverage, duplicate dates, non-positive prices,
  extreme returns, and minimum history.
- Produces a downloadable Markdown management report.

## Demonstration portfolio

| Proxy | Asset exposure | Weight |
|---|---|---:|
| SPY | U.S. large-cap equity | 30% |
| EFA | Developed markets excluding the U.S. | 20% |
| IEF | U.S. Treasury bonds | 20% |
| GLD | Gold | 10% |
| VNQ | U.S. listed real estate | 10% |
| DBC | Broad commodities | 10% |

The weights represent an imagined investment mandate and do not describe any real
company, client, fund, or employer.

## Market-data source

The application retrieves published adjusted-close observations through the public
Yahoo Finance chart service and displays the retrieval timestamp and available data
period in the dashboard. This source is convenient for an educational demonstration
but has no contractual production SLA. A production implementation should use a
licensed institutional vendor or an approved internal market-data service.

The application does not redistribute a bundled price-history database. Prices are
retrieved when the dashboard starts and cached for one hour.

## Quick start on Windows

Double-click `START_DASHBOARD.bat`. The first run creates an isolated Python
environment and installs the dependencies. Later runs reuse that environment.

Alternatively, use PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit normally opens at `http://localhost:8501`.

## Portfolio upload schema

The dashboard can replace the bundled portfolio with a CSV containing:

```csv
symbol,asset_name,asset_class,target_weight
SPY,U.S. large-cap equity,Equity,0.30
IEF,U.S. Treasury bonds,Fixed income,0.20
```

Requirements:

- `symbol` must be available through the selected public market source.
- `target_weight` must be numeric and non-negative.
- weights must sum to `1.0`.
- each symbol must appear once.

## Dashboard pages

1. **Executive overview** — performance, benchmark, data-quality and stress alerts.
2. **Performance & benchmark** — Sharpe, beta, tracking error, information ratio,
   wealth index, drawdown, and correlations.
3. **Risk & stress** — one-day VaR/ES, rolling backtest and deterministic scenarios.
4. **Allocation & attribution** — weights, return contribution and variance contribution.
5. **Data quality** — control status, critical failures, warnings and detailed evidence.
6. **Methodology** — formulas, horizons, provenance, assumptions and limitations.

## Core methodology

### Portfolio return

The demonstration assumes daily rebalancing to constant strategic weights:

```text
portfolio return(t) = sum(weight(i) × asset return(i,t))
```

### Benchmark analytics

- Active return = portfolio return − benchmark return.
- Tracking error = annualized standard deviation of active daily returns.
- Information ratio = annualized mean active return / active-return volatility.
- Beta = covariance(portfolio, benchmark) / variance(benchmark).

### Risk contribution

The application uses the sample covariance matrix. Component variance contribution is:

```text
weight(i) × [covariance matrix × weights](i) / portfolio variance
```

Contributions may be negative when an asset provides covariance diversification.

### Rolling out-of-sample VaR

For every test day:

```text
previous 90 daily P&Ls
        ↓
estimate one-day Historical VaR
        ↓
observe the next day's P&L
        ↓
record breach / no breach
        ↓
move the window one day forward
```

The displayed current VaR and Expected Shortfall use the latest 90 daily P&Ls.

### Stress horizon

Stress tests apply simultaneous, instantaneous shocks to every asset proxy. A full
cross-asset stress loss and a one-day VaR answer different questions and are not
presented as equivalent exposure measures.

## Testing

Run:

```powershell
python -m unittest discover -s tests -v
```

Tests cover market-response parsing, portfolio analytics, VaR look-ahead prevention,
stress aggregation, and data-quality controls.

## Project structure

```text
multi-asset-portfolio-risk-monitor/
├── app.py
├── requirements.txt
├── START_DASHBOARD.bat
├── data/
│   └── portfolio.csv
├── src/
│   ├── config.py
│   ├── data_loader.py
│   ├── data_quality.py
│   ├── demo_data.py
│   ├── market_data.py
│   ├── portfolio_analytics.py
│   ├── reporting.py
│   ├── risk_metrics.py
│   └── stress_testing.py
└── tests/
```

## Important limitations

- The holdings and capital are synthetic.
- Public market data may be delayed, revised, unavailable, or subject to provider terms.
- Adjusted-price returns are proxy returns, not verified executable portfolio prices.
- Constant daily weights ignore the mechanics and costs of rebalancing.
- No fees, taxes, spreads, slippage, market impact, liquidity, FX conversion or leverage.
- Historical risk models do not guarantee future loss coverage.
- Results are not investment advice and must not be used for production limits or
  regulatory reporting.

## Extension roadmap

1. Add a licensed-data adapter and secure Streamlit secrets.
2. Add transaction-level holdings, cash flows and explicit rebalance dates.
3. Add Kupiec coverage and Christoffersen independence tests.
4. Add factor regression, marginal VaR and Euler VaR contribution.
5. Add Black-Litterman allocation and constrained optimization.
6. Add transaction-cost-aware rebalancing recommendations.
7. Persist data and model runs in PostgreSQL with an audit trail.
8. Add CI/CD, Docker deployment and scheduled data refreshes.

## Suggested interview explanation

> I built a multi-asset analytics application that combines a clearly labelled
> synthetic portfolio with published market data. It evaluates benchmark-relative
> performance, return and risk attribution, drawdown, rolling out-of-sample VaR, and
> cross-asset stress scenarios. I also added transparent controls for allocation and
> market-data quality so the model's output is auditable rather than just visual.

## License

MIT License. See `LICENSE`. Market observations remain subject to their data provider's
terms and are not covered by the software license.

