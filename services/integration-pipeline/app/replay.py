"""Batch replay coordinator for deterministic simulation research."""
from decimal import Decimal
from typing import Sequence

from app.portfolio_cycle import PortfolioSimulator


def replay_market_series(
    prices: Sequence[Decimal],
    initial_cash: Decimal = Decimal("10000"),
    fee_rate: Decimal = Decimal("0.001"),
    allocation_fraction: Decimal = Decimal("0.10"),
) -> dict:
    if len(prices) < 2:
        raise ValueError("at least two prices are required")
    if allocation_fraction < 0 or allocation_fraction > 1:
        raise ValueError("allocation_fraction must be between 0 and 1")

    sim = PortfolioSimulator(initial_cash, fee_rate)
    cycle_results: list[dict] = []
    previous = prices[0]
    sim.record_cycle(previous, "hold", Decimal("0"))
    cycle_results.append(sim.snapshot(previous))

    for price in prices[1:]:
        change = (price - previous) / previous
        action = "buy" if change > Decimal("0.005") else "sell" if change < Decimal("-0.005") else "hold"
        allocation = sim.cash * allocation_fraction if action != "hold" else Decimal("0")
        result = sim.record_cycle(price, action, allocation)
        result["price_change"] = change
        cycle_results.append(result)
        previous = price

    summary = sim.summary(previous)
    return {
        "mode": "simulation-only",
        "cycles": cycle_results,
        "summary": summary,
    }
