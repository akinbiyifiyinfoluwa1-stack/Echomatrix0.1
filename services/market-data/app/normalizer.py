"""Canonical normalization and quality gates for provider observations."""
from __future__ import annotations

from decimal import Decimal

from .providers import MarketCandle, MarketDataProviderError


def normalize_candles(candles: list[MarketCandle]) -> list[MarketCandle]:
    if not candles:
        raise MarketDataProviderError("No market observations supplied")
    ordered = sorted(candles, key=lambda candle: candle.timestamp)
    previous = None
    for candle in ordered:
        if candle.open <= 0 or candle.high <= 0 or candle.low <= 0 or candle.close <= 0:
            raise MarketDataProviderError("Market prices must be positive")
        if candle.volume < 0:
            raise MarketDataProviderError("Market volume cannot be negative")
        if candle.high < max(candle.open, candle.close) or candle.low > min(candle.open, candle.close):
            raise MarketDataProviderError("Invalid OHLC relationship")
        if previous is not None and candle.timestamp <= previous:
            raise MarketDataProviderError("Duplicate or non-increasing market timestamps")
        previous = candle.timestamp
    return ordered


def latest(candles: list[MarketCandle]) -> MarketCandle:
    return normalize_candles(candles)[-1]
