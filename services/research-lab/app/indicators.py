"""Deterministic market features used by research policies."""
from __future__ import annotations
from decimal import Decimal
from statistics import fmean, pstdev
from typing import Sequence

D = Decimal

def returns(closes: Sequence[D]) -> list[D]:
    return [D("0")] + [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]

def sma(values: Sequence[D], period: int) -> list[D | None]:
    if period < 1: raise ValueError("period must be positive")
    out: list[D | None] = []
    for i in range(len(values)):
        out.append(sum(values[i-period+1:i+1]) / D(period) if i + 1 >= period else None)
    return out

def ema(values: Sequence[D], period: int) -> list[D | None]:
    if period < 1: raise ValueError("period must be positive")
    out: list[D | None] = [None] * len(values)
    if len(values) < period: return out
    seed = sum(values[:period]) / D(period)
    out[period-1] = seed
    alpha = D(2) / D(period + 1)
    prev = seed
    for i in range(period, len(values)):
        prev = alpha * values[i] + (D(1) - alpha) * prev
        out[i] = prev
    return out

def volatility(series: Sequence[D]) -> D:
    if len(series) < 2: return D("0")
    values = [float(x) for x in series]
    return D(str(pstdev(values)))

def max_drawdown(equity: Sequence[D]) -> D:
    if not equity: return D("0")
    peak = equity[0]
    worst = D("0")
    for value in equity:
        peak = max(peak, value)
        if peak > 0: worst = max(worst, (peak - value) / peak)
    return worst

def feature_snapshot(closes: Sequence[D], volumes: Sequence[D]) -> dict:
    r = returns(closes)
    recent = r[-5:] if len(r) >= 5 else r
    return {
        "last_return": str(r[-1]),
        "momentum_5": str((closes[-1] - closes[-min(5, len(closes))]) / closes[-min(5, len(closes))]),
        "sma_5": str(sma(closes, min(5, len(closes)))[-1]),
        "ema_5": str(ema(closes, min(5, len(closes)))[-1]),
        "return_volatility": str(volatility(recent)),
        "volume_ratio": str(volumes[-1] / (D(str(fmean(float(v) for v in volumes[-min(5, len(volumes)):])))) if volumes and any(volumes[-min(5, len(volumes)):]) else D("0")),
    }
