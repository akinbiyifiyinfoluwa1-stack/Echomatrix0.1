"""Historical dataset normalization and deterministic quality gates."""
from __future__ import annotations
from decimal import Decimal
from typing import Iterable
from app.contracts import Candle

def normalize(rows: Iterable[dict]) -> list[Candle]:
    candles = [Candle(timestamp=int(r["timestamp"]), open=Decimal(str(r["open"])), high=Decimal(str(r["high"])), low=Decimal(str(r["low"])), close=Decimal(str(r["close"])), volume=Decimal(str(r.get("volume", 0)))) for r in rows]
    candles.sort(key=lambda c: c.timestamp)
    timestamps = [c.timestamp for c in candles]
    if len(timestamps) != len(set(timestamps)): raise ValueError("duplicate timestamps detected")
    for c in candles:
        if c.high < max(c.open, c.close) or c.low > min(c.open, c.close) or c.low > c.high: raise ValueError(f"invalid OHLC at {c.timestamp}")
        if c.volume < 0: raise ValueError(f"negative volume at {c.timestamp}")
    return candles

def quality_report(candles: list[Candle]) -> dict:
    timestamps = [c.timestamp for c in candles]
    gaps = sum(1 for a,b in zip(timestamps, timestamps[1:]) if b <= a)
    return {"rows": len(candles), "unique_timestamps": len(set(timestamps)), "non_increasing_gaps": gaps, "valid": gaps == 0 and bool(candles)}
