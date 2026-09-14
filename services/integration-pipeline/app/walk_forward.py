"""Walk-forward research engine for EchoMatrix simulation.

Walk-forward evaluation separates calibration/training observations from a
subsequent out-of-sample test window. It is intentionally lightweight so the
brain can later plug in richer strategies without changing the evaluation
contract.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from app.replay import replay_market_series


def _slice_window(values: Sequence[Decimal], start: int, end: int) -> list[Decimal]:
    window = list(values[start:end])
    if len(window) < 2:
        raise ValueError("each walk-forward test window needs at least two prices")
    return window


def walk_forward_replay(
    prices: Sequence[Decimal],
    train_size: int,
    test_size: int,
    step: int | None = None,
    initial_cash: Decimal = Decimal("10000"),
    fee_rate: Decimal = Decimal("0.001"),
    allocation_fraction: Decimal = Decimal("0.10"),
) -> dict:
    """Run rolling out-of-sample windows and aggregate their results."""
    if len(prices) < 4:
        raise ValueError("at least four prices are required")
    if train_size < 2 or test_size < 2:
        raise ValueError("train_size and test_size must be at least 2")
    step = test_size if step is None else step
    if step < 1:
        raise ValueError("step must be positive")
    if train_size + test_size > len(prices):
        raise ValueError("train_size + test_size exceeds available observations")

    windows: list[dict] = []
    start = 0
    while start + train_size + test_size <= len(prices):
        train = _slice_window(prices, start, start + train_size)
        test = _slice_window(prices, start + train_size - 1, start + train_size + test_size)
        result = replay_market_series(test, initial_cash=initial_cash, fee_rate=fee_rate, allocation_fraction=allocation_fraction)
        windows.append({
            "window": len(windows) + 1,
            "train_start": start,
            "train_end": start + train_size - 1,
            "test_start": start + train_size - 1,
            "test_end": start + train_size + test_size - 1,
            "train_observations": len(train),
            "test_observations": len(test),
            "test_summary": result["summary"],
        })
        start += step

    if not windows:
        raise ValueError("no walk-forward windows could be formed")

    returns = [Decimal(str(item["test_summary"]["return_pct"])) for item in windows]
    avg_return = sum(returns) / Decimal(len(returns))
    positive = sum(1 for value in returns if value > 0)
    return {
        "mode": "simulation-only",
        "method": "walk-forward",
        "train_size": train_size,
        "test_size": test_size,
        "step": step,
        "windows": windows,
        "aggregate": {
            "window_count": len(windows),
            "average_test_return_pct": str(avg_return.quantize(Decimal("0.01"))),
            "positive_window_rate": str((Decimal(positive) / Decimal(len(windows))).quantize(Decimal("0.0001"))),
            "worst_test_return_pct": str(min(returns)),
            "best_test_return_pct": str(max(returns)),
        },
    }
