"""Scenario generation for the EchoMatrix simulation research laboratory.

All transformations are deterministic and operate only on supplied historical
candles. This module never creates or submits an external order.
"""
from __future__ import annotations
from decimal import Decimal
from app.contracts import Candle

D = Decimal


def validate_candles(candles: list[Candle]) -> None:
    if len(candles) < 3:
        raise ValueError("at least three candles are required")
    timestamps = [c.timestamp for c in candles]
    if timestamps != sorted(timestamps):
        raise ValueError("candles must be sorted by timestamp")
    if len(set(timestamps)) != len(timestamps):
        raise ValueError("duplicate candle timestamps are not allowed")


def _shift(c: Candle, factor: D, volume_factor: D = D("1")) -> Candle:
    return Candle(timestamp=c.timestamp, open=c.open * factor, high=c.high * factor, low=c.low * factor, close=c.close * factor, volume=c.volume * volume_factor)


def scenario_matrix(candles: list[Candle], shock_pct: D = D("0.10")) -> dict[str, list[Candle]]:
    """Create baseline, upside, downside, volatility and liquidity scenarios."""
    validate_candles(candles)
    if not D("0") < shock_pct < D("1"):
        raise ValueError("shock_pct must be between 0 and 1")
    last = len(candles) - 1
    up = list(candles)
    down = list(candles)
    high_vol = list(candles)
    low_liquidity = list(candles)
    up[last] = _shift(candles[last], D("1") + shock_pct)
    down[last] = _shift(candles[last], D("1") - shock_pct)
    high_vol[last] = _shift(candles[last], D("1"), D("2"))
    low_liquidity[last] = _shift(candles[last], D("1"), D("0.25"))
    return {
        "baseline": list(candles),
        "upside_shock": up,
        "downside_shock": down,
        "high_volume": high_vol,
        "low_liquidity": low_liquidity,
    }
