import unittest

import numpy as np
import pandas as pd

from src.data_quality import overall_quality_status, quality_score, run_data_quality_checks


class DataQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.portfolio = pd.DataFrame(
            {
                "symbol": ["SPY", "IEF"],
                "asset_name": ["Equity", "Bonds"],
                "asset_class": ["Equity", "Fixed income"],
                "target_weight": [0.6, 0.4],
            }
        )
        dates = pd.bdate_range("2025-01-01", periods=300)
        self.prices = pd.DataFrame(
            {
                "SPY": 100 * np.cumprod(np.full(len(dates), 1.001)),
                "IEF": 100 * np.cumprod(np.full(len(dates), 1.0002)),
            },
            index=dates,
        )

    def test_clean_data_has_no_failures(self) -> None:
        result = run_data_quality_checks(self.portfolio, self.prices, "SPY")
        self.assertFalse(result["status"].eq("FAIL").any())

    def test_weight_reconciliation_break_fails(self) -> None:
        broken = self.portfolio.copy()
        broken.loc[0, "target_weight"] = 0.5
        result = run_data_quality_checks(broken, self.prices, "SPY")
        row = result[result["check"].eq("Weights sum to 100%")].iloc[0]
        self.assertEqual(row["status"], "FAIL")

    def test_missing_market_observation_warns(self) -> None:
        broken = self.prices.copy()
        broken.loc[broken.index[20], "IEF"] = None
        result = run_data_quality_checks(self.portfolio, broken, "SPY")
        row = result[result["check"].eq("Cross-asset date coverage")].iloc[0]
        self.assertEqual(row["status"], "WARN")

    def test_score_and_status_reflect_warning(self) -> None:
        broken = self.prices.copy()
        broken.loc[broken.index[20], "IEF"] = None
        result = run_data_quality_checks(self.portfolio, broken, "SPY")
        self.assertEqual(overall_quality_status(result), "WARN")
        self.assertLess(quality_score(result), 100.0)


if __name__ == "__main__":
    unittest.main()

