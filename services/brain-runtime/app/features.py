"""Deterministic market-state features derived only from supplied observations."""
from decimal import Decimal
from statistics import mean, pstdev


def pct(a: Decimal, b: Decimal) -> Decimal:
    return (a - b) / b if b else Decimal("0")


def feature_snapshot(candles: list) -> dict:
    closes = [Decimal(str(c.close)) for c in candles]
    volumes = [Decimal(str(c.volume)) for c in candles]
    returns = [pct(closes[i], closes[i-1]) for i in range(1, len(closes))]
    recent = returns[-20:] or [Decimal("0")]
    avg_ret = Decimal(str(mean(float(x) for x in recent)))
    vol = Decimal(str(pstdev(float(x) for x in recent))) if len(recent) > 1 else Decimal("0")
    short = mean(float(x) for x in closes[-10:])
    long = mean(float(x) for x in closes[-30:])
    volume_avg = mean(float(x) for x in volumes[-20:]) if volumes else 0.0
    volume_ratio = float(volumes[-1]) / volume_avg if volume_avg else 1.0
    trend = "up" if short > long * 1.001 else "down" if short < long * 0.999 else "flat"
    regime = "high-volatility" if float(vol) > 0.02 else "low-volatility" if float(vol) < 0.005 else "normal-volatility"
    return {
        "last_price": str(closes[-1]),
        "return_20": str(pct(closes[-1], closes[-21])) if len(closes) >= 21 else "0",
        "mean_return": str(avg_ret),
        "realized_volatility": str(vol),
        "trend": trend,
        "regime": regime,
        "volume_ratio": round(volume_ratio, 4),
        "observation_count": len(candles),
    }
