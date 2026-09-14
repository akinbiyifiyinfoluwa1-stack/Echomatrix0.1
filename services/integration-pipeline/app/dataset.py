"""Historical market dataset primitives for simulation research.

This layer is deliberately provider-neutral and simulation-only. It accepts
already supplied historical observations and normalizes them into a stable
sequence for replay/walk-forward research; it never fetches or executes
against a broker or exchange.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Sequence


@dataclass(frozen=True)
class MarketObservation:
    timestamp: str
    symbol: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal = Decimal("0")

    def validate(self) -> None:
        if not self.symbol:
            raise ValueError("symbol is required")
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC prices must be positive")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("invalid OHLC bounds")
        if self.volume < 0:
            raise ValueError("volume cannot be negative")


def normalize_observations(observations: Iterable[MarketObservation]) -> list[MarketObservation]:
    """Validate, sort, and reject duplicate timestamps for deterministic replay."""
    rows = list(observations)
    for row in rows:
        row.validate()
    rows.sort(key=lambda row: row.timestamp)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row.symbol, row.timestamp)
        if key in seen:
            raise ValueError(f"duplicate observation: {row.symbol} @ {row.timestamp}")
        seen.add(key)
    return rows


def close_series(observations: Sequence[MarketObservation]) -> list[Decimal]:
    rows = normalize_observations(observations)
    if len(rows) < 2:
        raise ValueError("at least two observations are required")
    symbols = {row.symbol for row in rows}
    if len(symbols) != 1:
        raise ValueError("a close series must contain one symbol")
    return [row.close for row in rows]
