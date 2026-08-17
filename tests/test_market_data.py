import unittest

import pandas as pd

from src.market_data import MarketDataError, parse_chart_payload


class MarketDataTests(unittest.TestCase):
    def test_chart_payload_is_parsed_to_daily_series(self) -> None:
        payload = {
            "chart": {
                "result": [
                    {
                        "timestamp": [1672669800, 1672756200],
                        "indicators": {"adjclose": [{"adjclose": [100.0, 102.5]}]},
                    }
                ],
                "error": None,
            }
        }

        series = parse_chart_payload(payload, "TEST")

        self.assertEqual(series.name, "TEST")
        self.assertEqual(len(series), 2)
        self.assertAlmostEqual(float(series.iloc[-1]), 102.5)
        self.assertIsInstance(series.index, pd.DatetimeIndex)

    def test_provider_error_is_rejected(self) -> None:
        payload = {"chart": {"result": None, "error": {"description": "Unknown symbol"}}}
        with self.assertRaises(MarketDataError):
            parse_chart_payload(payload, "BAD")

    def test_missing_prices_are_dropped(self) -> None:
        payload = {
            "chart": {
                "result": [
                    {
                        "timestamp": [1672669800, 1672756200],
                        "indicators": {"adjclose": [{"adjclose": [100.0, None]}]},
                    }
                ],
                "error": None,
            }
        }
        series = parse_chart_payload(payload, "TEST")
        self.assertEqual(len(series), 1)


if __name__ == "__main__":
    unittest.main()

