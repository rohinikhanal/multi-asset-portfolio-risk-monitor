import unittest

import pandas as pd

from src.portfolio_analytics import (
    align_prices,
    calculate_portfolio_returns,
    calculate_returns,
    max_drawdown,
    performance_summary,
    risk_contribution,
    weight_series,
)


class PortfolioAnalyticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.portfolio = pd.DataFrame(
            {
                "symbol": ["A", "B"],
                "asset_name": ["Asset A", "Asset B"],
                "asset_class": ["Equity", "Bond"],
                "target_weight": [0.6, 0.4],
            }
        )
        self.prices = pd.DataFrame(
            {"A": [100.0, 110.0, 99.0, 108.9], "B": [100.0, 100.0, 102.0, 102.0]},
            index=pd.date_range("2026-01-01", periods=4, freq="D"),
        )

    def test_weights_are_normalized(self) -> None:
        weights = weight_series(self.portfolio)
        self.assertAlmostEqual(float(weights.sum()), 1.0)
        self.assertAlmostEqual(float(weights["A"]), 0.6)

    def test_portfolio_return_is_weighted_sum(self) -> None:
        returns = calculate_returns(self.prices)
        result = calculate_portfolio_returns(returns, weight_series(self.portfolio))
        expected_first = 0.6 * 0.10 + 0.4 * 0.0
        self.assertAlmostEqual(float(result.iloc[0]), expected_first)

    def test_align_prices_fills_short_holiday_gap(self) -> None:
        prices = self.prices.copy()
        prices.loc[prices.index[1], "B"] = None
        aligned = align_prices(prices, ["A", "B"])
        self.assertFalse(aligned.isna().any().any())

    def test_max_drawdown_is_negative(self) -> None:
        returns = pd.Series([0.10, -0.20, 0.05])
        self.assertLess(max_drawdown(returns), 0)

    def test_performance_summary_contains_benchmark_metrics(self) -> None:
        portfolio = pd.Series([0.01, -0.005, 0.012, 0.003])
        benchmark = pd.Series([0.008, -0.004, 0.010, 0.002])
        result = performance_summary(portfolio, benchmark)
        self.assertIn("tracking_error", result)
        self.assertIn("beta", result)

    def test_risk_contributions_sum_to_one_hundred(self) -> None:
        returns = calculate_returns(self.prices)
        result = risk_contribution(returns, weight_series(self.portfolio))
        self.assertAlmostEqual(float(result["risk_contribution_pct"].sum()), 100.0)


if __name__ == "__main__":
    unittest.main()

