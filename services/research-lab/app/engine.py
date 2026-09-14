"""Research laboratory orchestration: features, policies, replay, metrics and stress tests."""
from __future__ import annotations
from decimal import Decimal
from app.contracts import Candle
from app.indicators import feature_snapshot
from app.metrics import performance, rank_key
from app.policies import ensemble
from app.simulator import replay

D = Decimal

def validate_candles(candles: list[Candle]) -> None:
    if len(candles) < 3: raise ValueError("at least three candles are required")
    timestamps = [c.timestamp for c in candles]
    if timestamps != sorted(timestamps): raise ValueError("candles must be sorted by timestamp")
    if len(set(timestamps)) != len(timestamps): raise ValueError("duplicate candle timestamps are not allowed")
    for c in candles:
        if c.high < max(c.open, c.close) or c.low > min(c.open, c.close) or c.low > c.high:
            raise ValueError(f"invalid OHLC candle at timestamp {c.timestamp}")

def run_research(symbol: str, candles: list[Candle], initial_cash: D, fee_rate: D, allocation_fraction: D, threshold: D) -> dict:
    validate_candles(candles)
    closes = [c.close for c in candles]; volumes = [c.volume for c in candles]
    features = feature_snapshot(closes, volumes)
    policy = ensemble(closes, threshold)
    summary = replay(closes, initial_cash, fee_rate, allocation_fraction, threshold)
    metrics = performance([D(x) for x in summary["equity_curve"]])
    return {"mode": "simulation-only", "symbol": symbol, "features": features, "policy": policy, "summary": summary, "metrics": metrics}

def compare(symbol: str, candles: list[Candle], initial_cash: D, fee_rate: D, thresholds: list[D], allocations: list[D]) -> dict:
    validate_candles(candles)
    closes = [c.close for c in candles]
    results = []
    for threshold in thresholds:
        for allocation in allocations:
            summary = replay(closes, initial_cash, fee_rate, allocation, threshold)
            metrics = performance([D(x) for x in summary["equity_curve"]])
            results.append({"name": f"threshold={threshold};allocation={allocation}", "threshold": str(threshold), "allocation": str(allocation), "summary": summary, "metrics": metrics})
    ranked = sorted(results, key=lambda x: rank_key(x["summary"]), reverse=True)
    for rank, item in enumerate(ranked, 1): item["rank"] = rank
    return {"mode": "simulation-only", "symbol": symbol, "experiment_count": len(ranked), "ranked": ranked, "winner": ranked[0] if ranked else None}

def stress(symbol: str, candles: list[Candle], initial_cash: D, fee_rate: D, allocation_fraction: D, threshold: D, shock_pct: D) -> dict:
    validate_candles(candles)
    base = [c.close for c in candles]
    up = base[:-1] + [base[-1] * (D("1") + shock_pct)]
    down = base[:-1] + [base[-1] * (D("1") - shock_pct)]
    return {"mode": "simulation-only", "symbol": symbol, "shock_pct": str(shock_pct), "baseline": replay(base, initial_cash, fee_rate, allocation_fraction, threshold), "up_shock": replay(up, initial_cash, fee_rate, allocation_fraction, threshold), "down_shock": replay(down, initial_cash, fee_rate, allocation_fraction, threshold)}
