"""Simulation-only validation primitives for EchoMatrix brain experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Iterable, Sequence

from .models import Candle


@dataclass(frozen=True)
class ValidationFinding:
    code: str
    severity: str
    message: str
    count: int = 1


@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    score: float
    findings: tuple[ValidationFinding, ...]
    sample_count: int
    train_count: int
    test_count: int

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "score": self.score,
            "findings": [asdict(item) for item in self.findings],
            "sample_count": self.sample_count,
            "train_count": self.train_count,
            "test_count": self.test_count,
        }


def _finite(value: float) -> bool:
    return isfinite(float(value))


def validate_candles(candles: Sequence[Candle]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if not candles:
        return [ValidationFinding("EMPTY_DATA", "ERROR", "No candles supplied")]
    timestamps = [item.timestamp for item in candles]
    duplicate_count = len(timestamps) - len(set(timestamps))
    if duplicate_count:
        findings.append(ValidationFinding("DUPLICATE_TIMESTAMPS", "ERROR", "Duplicate candle timestamps detected", duplicate_count))
    out_of_order = sum(1 for left, right in zip(timestamps, timestamps[1:]) if right <= left)
    if out_of_order:
        findings.append(ValidationFinding("NON_MONOTONIC_TIME", "ERROR", "Candle timestamps are not strictly increasing", out_of_order))
    bad = 0
    for candle in candles:
        values = (candle.open, candle.high, candle.low, candle.close, candle.volume)
        if not all(_finite(value) for value in values):
            bad += 1
            continue
        if min(candle.open, candle.close, candle.high, candle.low) <= 0:
            bad += 1
        elif candle.high < max(candle.open, candle.close) or candle.low > min(candle.open, candle.close):
            bad += 1
        elif candle.low > candle.high or candle.volume < 0:
            bad += 1
    if bad:
        findings.append(ValidationFinding("INVALID_CANDLES", "ERROR", "One or more candles contain invalid OHLCV values", bad))
    return findings


def split_temporally(candles: Sequence[Candle], train_fraction: float = 0.70) -> tuple[list[Candle], list[Candle]]:
    """Split chronologically; never shuffle time-series observations."""
    if not 0.5 <= train_fraction < 1.0:
        raise ValueError("train_fraction must be in [0.5, 1.0)")
    cut = max(1, min(len(candles) - 1, int(len(candles) * train_fraction)))
    return list(candles[:cut]), list(candles[cut:])


def detect_temporal_overlap(train: Iterable[Candle], test: Iterable[Candle]) -> ValidationFinding | None:
    train_times = {item.timestamp for item in train}
    overlap = sum(1 for item in test if item.timestamp in train_times)
    if overlap:
        return ValidationFinding("TRAIN_TEST_OVERLAP", "ERROR", "Train and test windows share observations", overlap)
    return None


def validate_research_dataset(candles: Sequence[Candle], train_fraction: float = 0.70) -> ValidationReport:
    findings = validate_candles(candles)
    train, test = split_temporally(candles, train_fraction) if len(candles) >= 2 else (list(candles), [])
    overlap = detect_temporal_overlap(train, test)
    if overlap:
        findings.append(overlap)
    if len(candles) < 30:
        findings.append(ValidationFinding("SMALL_SAMPLE", "WARNING", "Dataset is too small for meaningful research conclusions"))
    if len(test) < 10:
        findings.append(ValidationFinding("SMALL_TEST_SET", "WARNING", "Out-of-sample window is small"))
    errors = sum(item.severity == "ERROR" for item in findings)
    warnings = sum(item.severity == "WARNING" for item in findings)
    score = max(0.0, 1.0 - min(1.0, errors * 0.35 + warnings * 0.08))
    return ValidationReport(
        passed=errors == 0,
        score=round(score, 4),
        findings=tuple(findings),
        sample_count=len(candles),
        train_count=len(train),
        test_count=len(test),
    )
