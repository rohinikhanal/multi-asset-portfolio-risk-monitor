"""Retrieve and validate published daily market prices."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import pandas as pd
import requests

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


class MarketDataError(ValueError):
    """Raised when published market data cannot be retrieved or parsed."""


def parse_chart_payload(payload: dict, symbol: str) -> pd.Series:
    """Parse one Yahoo chart response into a UTC-normalized adjusted-close series."""

    chart = payload.get("chart", {})
    if chart.get("error"):
        raise MarketDataError(f"Market-data provider rejected {symbol}: {chart['error']}")
    results = chart.get("result") or []
    if not results:
        raise MarketDataError(f"No market-price history was returned for {symbol}.")

    result = results[0]
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators") or {}
    adjusted_blocks = indicators.get("adjclose") or []
    quote_blocks = indicators.get("quote") or []
    if adjusted_blocks:
        values = adjusted_blocks[0].get("adjclose") or []
    elif quote_blocks:
        values = quote_blocks[0].get("close") or []
    else:
        values = []
    if len(timestamps) != len(values) or not timestamps:
        raise MarketDataError(f"Incomplete timestamp/price arrays were returned for {symbol}.")

    index = pd.to_datetime(timestamps, unit="s", utc=True).normalize().tz_localize(None)
    series = pd.Series(pd.to_numeric(values, errors="coerce"), index=index, name=symbol)
    series = series[~series.index.duplicated(keep="last")].sort_index().dropna()
    if series.empty:
        raise MarketDataError(f"All returned prices were missing for {symbol}.")
    return series.astype(float)


def fetch_symbol_history(
    symbol: str,
    start_date: str | date,
    end_date: str | date,
    timeout: int = 30,
) -> pd.Series:
    """Fetch daily adjusted-close history for one public market symbol."""

    start = pd.Timestamp(start_date, tz="UTC")
    end = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    if start >= end:
        raise ValueError("Market-data start date must be before the end date.")

    response = requests.get(
        YAHOO_CHART_URL.format(symbol=symbol),
        params={
            "period1": int(start.timestamp()),
            "period2": int(end.timestamp()),
            "interval": "1d",
            "events": "history",
        },
        headers={"User-Agent": "Mozilla/5.0 multi-asset-risk-monitor/1.0"},
        timeout=timeout,
    )
    try:
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as error:
        raise MarketDataError(f"Could not retrieve published prices for {symbol}: {error}") from error
    return parse_chart_payload(payload, symbol)


def fetch_market_prices(
    symbols: list[str],
    start_date: str | date,
    end_date: str | date | None = None,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Fetch several symbols concurrently and return an aligned price matrix."""

    unique_symbols = list(dict.fromkeys(symbol.upper() for symbol in symbols))
    end_date = end_date or (date.today() - timedelta(days=1))
    series_by_symbol: dict[str, pd.Series] = {}
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=min(6, len(unique_symbols))) as executor:
        futures = {
            executor.submit(fetch_symbol_history, symbol, start_date, end_date): symbol
            for symbol in unique_symbols
        }
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                series_by_symbol[symbol] = future.result()
            except (MarketDataError, requests.RequestException) as error:
                errors.append(str(error))

    if errors:
        raise MarketDataError(" | ".join(errors))

    prices = pd.concat([series_by_symbol[symbol] for symbol in unique_symbols], axis=1)
    prices.index.name = "date"
    prices = prices.sort_index()
    metadata = {
        "source_name": "Yahoo Finance chart data",
        "source_url": "https://finance.yahoo.com/",
        "data_type": "Published adjusted-close market prices",
        "retrieved_at": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M UTC"),
        "first_date": prices.index.min().strftime("%Y-%m-%d"),
        "last_date": prices.index.max().strftime("%Y-%m-%d"),
        "disclaimer": "Educational use; the public chart endpoint has no production SLA.",
    }
    return prices, metadata

