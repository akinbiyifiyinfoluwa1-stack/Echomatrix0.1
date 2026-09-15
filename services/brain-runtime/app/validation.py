"""Research validation and walk-forward evaluation for the simulation-only brain."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from math import isfinite
from statistics import mean
from typing import Any, Sequence
from .models import Candle

@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    count: int = 1

@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    score: float
    sample_count: int
    train_count: int
    test_count: int
    findings: tuple[Finding, ...]
    def as_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "score": self.score, "sample_count": self.sample_count,
                "train_count": self.train_count, "test_count": self.test_count,
                "findings": [asdict(x) for x in self.findings]}

def validate_candles(candles: Sequence[Candle]) -> ValidationReport:
    findings: list[Finding] = []
    if not candles:
        findings.append(Finding("EMPTY_DATA", "ERROR", "No candles supplied"))
        return ValidationReport(False, 0.0, 0, 0, 0, tuple(findings))
    timestamps = [c.timestamp for c in candles]
    duplicate = len(timestamps) - len(set(timestamps))
    unordered = sum(right <= left for left, right in zip(timestamps, timestamps[1:]))
    invalid = 0
    for c in candles:
        vals = (c.open, c.high, c.low, c.close, c.volume)
        if not all(isfinite(float(v)) for v in vals): invalid += 1; continue
        if min(float(c.open), float(c.high), float(c.low), float(c.close)) <= 0 or float(c.volume) < 0: invalid += 1
        elif float(c.high) < max(float(c.open), float(c.close)) or float(c.low) > min(float(c.open), float(c.close)): invalid += 1
    if duplicate: findings.append(Finding("DUPLICATE_TIMESTAMPS", "ERROR", "Duplicate observations detected", duplicate))
    if unordered: findings.append(Finding("NON_MONOTONIC_TIME", "ERROR", "Observations are not strictly chronological", unordered))
    if invalid: findings.append(Finding("INVALID_OHLCV", "ERROR", "Invalid OHLCV observations detected", invalid))
    if len(candles) < 30: findings.append(Finding("SMALL_SAMPLE", "WARNING", "Dataset is small for research conclusions"))
    errors = sum(f.severity == "ERROR" for f in findings)
    warnings = sum(f.severity == "WARNING" for f in findings)
    score = max(0.0, 1.0 - min(1.0, errors * .35 + warnings * .08))
    return ValidationReport(errors == 0, round(score, 4), len(candles), 0, 0, tuple(findings))

def temporal_split(candles: Sequence[Candle], train_fraction: float = .70) -> tuple[list[Candle], list[Candle]]:
    if not .50 <= train_fraction < 1.0: raise ValueError("train_fraction must be in [0.5, 1.0)")
    if len(candles) < 2: return list(candles), []
    cut = max(1, min(len(candles) - 1, int(len(candles) * train_fraction)))
    return list(candles[:cut]), list(candles[cut:])

def walk_forward_windows(candles: Sequence[Candle], train_size: int, test_size: int, step: int | None = None) -> list[dict[str, Any]]:
    if train_size < 1 or test_size < 1: raise ValueError("train_size and test_size must be positive")
    step = step or test_size
    windows = []
    start = 0
    while start + train_size + test_size <= len(candles):
        train = candles[start:start + train_size]; test = candles[start + train_size:start + train_size + test_size]
        windows.append({"index": len(windows), "train_start": train[0].timestamp, "train_end": train[-1].timestamp,
                        "test_start": test[0].timestamp, "test_end": test[-1].timestamp,
                        "train_count": len(train), "test_count": len(test)})
        start += step
    return windows

def leakage_report(train: Sequence[Candle], test: Sequence[Candle]) -> dict[str, Any]:
    train_ts = {c.timestamp for c in train}; overlap = sum(c.timestamp in train_ts for c in test)
    return {"passed": overlap == 0, "overlap_count": overlap, "simulation_only": True}

def summarize_oos(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    returns = [float(r.get("return_pct", 0.0)) for r in results]
    drawdowns = [float(r.get("max_drawdown_pct", 0.0)) for r in results]
    wins = [float(r.get("win_rate", 0.0)) for r in results]
    return {"windows": len(results), "mean_return_pct": mean(returns) if returns else 0.0,
            "median_return_pct": sorted(returns)[len(returns)//2] if returns else 0.0,
            "worst_return_pct": min(returns) if returns else 0.0,
            "worst_drawdown_pct": max(drawdowns) if drawdowns else 0.0,
            "mean_win_rate": mean(wins) if wins else 0.0,
            "simulation_only": True}
