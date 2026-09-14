"""Provider contracts for real market-data ingestion.

The market-data layer is deliberately read-only. Providers return observations;
they never place orders or connect to execution accounts.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class MarketCandle:
    timestamp: int
    symbol: str
    timeframe: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    source: str


class MarketDataProvider(Protocol):
    name: str

    def fetch_candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[MarketCandle]:
        """Return real market observations, newest last."""
        ...


class MarketDataProviderError(RuntimeError):
    """Raised when a provider cannot supply trustworthy market data."""
