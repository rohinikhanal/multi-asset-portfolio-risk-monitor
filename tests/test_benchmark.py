import unittest

from src.benchmark import CUSTOM_BENCHMARK_OPTION, resolve_benchmark


class BenchmarkTests(unittest.TestCase):
    def test_predefined_composite_benchmark(self) -> None:
        benchmark = resolve_benchmark("60/40 - U.S. equity/bond")
        self.assertEqual(benchmark.components, {"SPY": 0.60, "IEF": 0.40})
        self.assertEqual(benchmark.primary_symbol, "SPY")

    def test_user_defined_ticker_is_normalized(self) -> None:
        benchmark = resolve_benchmark(CUSTOM_BENCHMARK_OPTION, "  ^gdaxi ")
        self.assertEqual(benchmark.components, {"^GDAXI": 1.0})

    def test_empty_custom_ticker_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Enter a market-data ticker"):
            resolve_benchmark(CUSTOM_BENCHMARK_OPTION, "")


if __name__ == "__main__":
    unittest.main()
