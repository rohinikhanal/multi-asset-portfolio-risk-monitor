import unittest

import pandas as pd

from src.risk_metrics import expected_shortfall, historical_var, risk_summary, rolling_var_backtest
from src.stress_testing import run_stress_tests


class RiskAndStressTests(unittest.TestCase):
    def test_expected_shortfall_is_not_below_var(self) -> None:
        pnl = pd.Series([-100.0, -50.0, 0.0, 25.0, 75.0])
        self.assertGreaterEqual(expected_shortfall(pnl, 0.80), historical_var(pnl, 0.80))

    def test_rolling_backtest_uses_only_previous_window(self) -> None:
        pnl = pd.Series(
            [-10.0, -20.0, -30.0, -40.0, -100.0],
            index=pd.date_range("2026-01-01", periods=5, freq="D"),
        )
        result = rolling_var_backtest(pnl, confidence=0.80, lookback=3)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(float(result.iloc[0]["var_usd"]), historical_var(pnl.iloc[:3], 0.80))

    def test_risk_summary_counts_out_of_sample_rows(self) -> None:
        pnl = pd.Series(range(-120, 0), index=pd.date_range("2026-01-01", periods=120, freq="D"))
        result = risk_summary(pnl, confidence=0.95, lookback=90)
        self.assertEqual(result["backtest_observations"], 30.0)

    def test_stress_base_market_has_zero_impact(self) -> None:
        weights = pd.Series({"SPY": 0.5, "IEF": 0.5})
        result = run_stress_tests(weights, 1_000_000)
        base = result[result["scenario"].eq("Base market")].iloc[0]
        self.assertEqual(float(base["portfolio_pnl_usd"]), 0.0)

    def test_stress_table_contains_loss_scenario(self) -> None:
        weights = pd.Series({"SPY": 0.6, "IEF": 0.4})
        result = run_stress_tests(weights, 1_000_000)
        self.assertLess(float(result["portfolio_pnl_usd"].min()), 0.0)


if __name__ == "__main__":
    unittest.main()

