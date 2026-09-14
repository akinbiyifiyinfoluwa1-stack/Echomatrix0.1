"""Performance metrics for research reports."""
from __future__ import annotations
from decimal import Decimal
from statistics import pstdev
D = Decimal

def performance(equity_curve: list[D], periods_per_year: int = 252) -> dict:
    if len(equity_curve) < 2: return {"sharpe_like": "0", "volatility_pct": "0", "max_drawdown_pct": "0"}
    rets = [(equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1] for i in range(1, len(equity_curve)) if equity_curve[i-1]]
    mean = sum(rets, D("0")) / D(len(rets)) if rets else D("0")
    vol = D(str(pstdev([float(x) for x in rets]))) if len(rets) > 1 else D("0")
    sharpe = (mean / vol) * D(str(periods_per_year ** 0.5)) if vol else D("0")
    peak = equity_curve[0]; dd = D("0")
    for value in equity_curve:
        peak = max(peak, value)
        if peak: dd = max(dd, (peak-value)/peak)
    return {"period_return_pct": str(((equity_curve[-1]-equity_curve[0])/equity_curve[0])*D("100")), "volatility_pct": str(vol*D("100")), "sharpe_like": str(sharpe), "max_drawdown_pct": str(dd*D("100"))}

def rank_key(summary: dict) -> tuple[Decimal, Decimal, Decimal]:
    return (D(str(summary.get("return_pct", "-999999"))), -D(str(summary.get("max_drawdown_pct", "999999"))), D(str(summary.get("win_rate", "0"))))
