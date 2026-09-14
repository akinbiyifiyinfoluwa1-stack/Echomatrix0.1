"""Research policies. They generate hypothetical actions only."""
from __future__ import annotations
from decimal import Decimal
from typing import Sequence
from app.indicators import ema, sma

D = Decimal

def momentum_policy(closes: Sequence[D], threshold: D) -> str:
    if len(closes) < 2: return "hold"
    change = (closes[-1] - closes[-2]) / closes[-2]
    return "buy" if change > threshold else "sell" if change < -threshold else "hold"

def trend_policy(closes: Sequence[D]) -> str:
    if len(closes) < 5: return "hold"
    short = ema(closes, min(5, len(closes)))[-1]
    long_period = min(10, len(closes))
    long = ema(closes, long_period)[-1]
    if short is None or long is None: return "hold"
    return "buy" if short > long else "sell" if short < long else "hold"

def mean_reversion_policy(closes: Sequence[D], period: int = 5, band: D = D("0.01")) -> str:
    if len(closes) < period: return "hold"
    mean = sma(closes, period)[-1]
    if mean is None or mean == 0: return "hold"
    deviation = (closes[-1] - mean) / mean
    return "buy" if deviation < -band else "sell" if deviation > band else "hold"

def ensemble(closes: Sequence[D], threshold: D) -> dict:
    votes = {"momentum": momentum_policy(closes, threshold), "trend": trend_policy(closes), "mean_reversion": mean_reversion_policy(closes)}
    scores = {"buy": sum(v == "buy" for v in votes.values()), "sell": sum(v == "sell" for v in votes.values())}
    action = "buy" if scores["buy"] > scores["sell"] else "sell" if scores["sell"] > scores["buy"] else "hold"
    confidence = D(max(scores.values())) / D(len(votes))
    return {"action": action, "confidence": str(confidence), "votes": votes}
