"""Selectable single-ticker and composite benchmark definitions."""

from __future__ import annotations

from dataclasses import dataclass


CUSTOM_BENCHMARK_OPTION = "User-defined ticker"


@dataclass(frozen=True)
class BenchmarkDefinition:
    """A display name and constant-weight collection of market-data symbols."""

    name: str
    components: dict[str, float]

    @property
    def primary_symbol(self) -> str:
        return next(iter(self.components))


BENCHMARK_OPTIONS = {
    "SPY - S&P 500": BenchmarkDefinition("S&P 500 ETF proxy", {"SPY": 1.0}),
    "ACWI - Global equities": BenchmarkDefinition(
        "MSCI ACWI global-equity ETF proxy", {"ACWI": 1.0}
    ),
    "VT - Total world equities": BenchmarkDefinition(
        "Total world stock-market ETF proxy", {"VT": 1.0}
    ),
    "60/40 - U.S. equity/bond": BenchmarkDefinition(
        "60% SPY / 40% IEF constant-weight benchmark", {"SPY": 0.60, "IEF": 0.40}
    ),
}


def resolve_benchmark(selection: str, custom_ticker: str = "") -> BenchmarkDefinition:
    """Resolve a sidebar selection into a validated benchmark definition."""

    if selection == CUSTOM_BENCHMARK_OPTION:
        symbol = custom_ticker.strip().upper()
        if not symbol:
            raise ValueError("Enter a market-data ticker for the user-defined benchmark.")
        return BenchmarkDefinition(f"User-defined benchmark ({symbol})", {symbol: 1.0})
    if selection not in BENCHMARK_OPTIONS:
        raise ValueError(f"Unknown benchmark selection: {selection}")
    return BENCHMARK_OPTIONS[selection]

