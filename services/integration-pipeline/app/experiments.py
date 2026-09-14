"""Experiment registry for comparing deterministic simulation policies."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Sequence

from app.replay import replay_market_series


@dataclass(frozen=True)
class ExperimentSpec:
    name: str
    allocation_fraction: Decimal
    threshold: Decimal


def _replay_with_threshold(
    prices: Sequence[Decimal],
    allocation_fraction: Decimal,
    threshold: Decimal,
    initial_cash: Decimal,
    fee_rate: Decimal,
) -> dict:
    if len(prices) < 2:
        raise ValueError("at least two prices are required")
    from app.portfolio_cycle import PortfolioSimulator

    sim = PortfolioSimulator(initial_cash, fee_rate)
    previous = prices[0]
    sim.record_cycle(previous, "hold", Decimal("0"))
    for price in prices[1:]:
        change = (price - previous) / previous
        action = "buy" if change > threshold else "sell" if change < -threshold else "hold"
        allocation = sim.cash * allocation_fraction if action != "hold" else Decimal("0")
        sim.record_cycle(price, action, allocation)
        previous = price
    return sim.summary(previous)


def run_experiment_registry(
    prices: Sequence[Decimal],
    specs: Sequence[ExperimentSpec],
    initial_cash: Decimal = Decimal("10000"),
    fee_rate: Decimal = Decimal("0.001"),
) -> dict:
    """Compare multiple simulation policies on identical observations."""
    if not specs:
        raise ValueError("at least one experiment is required")
    results = []
    for spec in specs:
        if not 0 <= spec.allocation_fraction <= 1:
            raise ValueError(f"invalid allocation fraction for {spec.name}")
        if spec.threshold < 0:
            raise ValueError(f"invalid threshold for {spec.name}")
        summary = _replay_with_threshold(prices, spec.allocation_fraction, spec.threshold, initial_cash, fee_rate)
        results.append({"name": spec.name, "parameters": {"allocation_fraction": str(spec.allocation_fraction), "threshold": str(spec.threshold)}, "summary": summary})
    results.sort(key=lambda item: Decimal(str(item["summary"]["return_pct"])), reverse=True)
    return {
        "mode": "simulation-only",
        "experiment_count": len(results),
        "ranking": results,
        "best": results[0],
        "baseline": replay_market_series(prices, initial_cash=initial_cash, fee_rate=fee_rate),
    }
