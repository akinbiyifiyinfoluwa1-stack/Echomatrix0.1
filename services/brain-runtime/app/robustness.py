"""Simulation-only robustness and stress testing for EchoMatrix research."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from random import Random
from statistics import mean
from typing import Any, Sequence


@dataclass(frozen=True)
class StressScenario:
    name: str
    return_multiplier: float = 1.0
    drawdown_multiplier: float = 1.0
    win_rate_shift: float = 0.0


def _metric(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def apply_stress(results: Sequence[dict[str, Any]], scenario: StressScenario) -> dict[str, Any]:
    """Apply deterministic perturbations to research results; never executes anything."""
    stressed = []
    for row in results:
        item = dict(row)
        item["return_pct"] = _metric(row, "return_pct") * scenario.return_multiplier
        item["max_drawdown_pct"] = _metric(row, "max_drawdown_pct") * scenario.drawdown_multiplier
        item["win_rate"] = max(0.0, min(1.0, _metric(row, "win_rate") + scenario.win_rate_shift))
        stressed.append(item)
    returns = [_metric(x, "return_pct") for x in stressed]
    drawdowns = [_metric(x, "max_drawdown_pct") for x in stressed]
    return {
        "scenario": asdict(scenario),
        "windows": len(stressed),
        "mean_return_pct": mean(returns) if returns else 0.0,
        "worst_return_pct": min(returns) if returns else 0.0,
        "worst_drawdown_pct": max(drawdowns) if drawdowns else 0.0,
        "results": stressed,
        "simulation_only": True,
    }


def default_stress_scenarios() -> list[StressScenario]:
    return [
        StressScenario("baseline"),
        StressScenario("adverse-returns", return_multiplier=0.75),
        StressScenario("high-friction", return_multiplier=0.85, drawdown_multiplier=1.20, win_rate_shift=-0.03),
        StressScenario("high-volatility", return_multiplier=0.70, drawdown_multiplier=1.50, win_rate_shift=-0.05),
        StressScenario("severe-regime-shift", return_multiplier=0.50, drawdown_multiplier=2.00, win_rate_shift=-0.10),
    ]


def stress_matrix(results: Sequence[dict[str, Any]], scenarios: Sequence[StressScenario] | None = None) -> dict[str, Any]:
    scenarios = list(scenarios or default_stress_scenarios())
    reports = [apply_stress(results, scenario) for scenario in scenarios]
    return {
        "scenario_count": len(reports),
        "reports": reports,
        "simulation_only": True,
        "external_execution": False,
    }


def monte_carlo_outcomes(
    results: Sequence[dict[str, Any]],
    iterations: int = 500,
    seed: int = 42,
) -> dict[str, Any]:
    """Bootstrap research outcomes to estimate robustness of aggregate returns."""
    rows = list(results)
    if not rows:
        return {"iterations": 0, "status": "no-data", "simulation_only": True}
    iterations = max(1, min(int(iterations), 5000))
    rng = Random(seed)
    returns = [_metric(row, "return_pct") for row in rows]
    totals: list[float] = []
    for _ in range(iterations):
        sample = [returns[rng.randrange(len(returns))] for _ in returns]
        totals.append(sum(sample))
    totals.sort()
    def percentile(p: float) -> float:
        index = min(len(totals) - 1, max(0, int((len(totals) - 1) * p)))
        return totals[index]
    return {
        "status": "complete",
        "iterations": iterations,
        "seed": seed,
        "observations": len(rows),
        "mean_total_return_pct": mean(totals),
        "p05_total_return_pct": percentile(.05),
        "p50_total_return_pct": percentile(.50),
        "p95_total_return_pct": percentile(.95),
        "probability_negative_total": sum(value < 0 for value in totals) / len(totals),
        "simulation_only": True,
        "external_execution": False,
    }


def robustness_score(stress: dict[str, Any], monte_carlo: dict[str, Any]) -> dict[str, Any]:
    """Convert stress and bootstrap diagnostics into a bounded research score."""
    reports = stress.get("reports", [])
    if not reports:
        return {"score": 0.0, "status": "no-data", "simulation_only": True}
    severe = reports[-1]
    stress_survival = 1.0 if severe.get("worst_return_pct", 0.0) >= 0 else 0.5
    drawdown_penalty = min(1.0, max(0.0, severe.get("worst_drawdown_pct", 0.0) / 100.0))
    negative_prob = max(0.0, min(1.0, float(monte_carlo.get("probability_negative_total", 1.0))))
    score = max(0.0, min(1.0, 0.45 * stress_survival + 0.30 * (1 - drawdown_penalty) + 0.25 * (1 - negative_prob)))
    return {
        "score": round(score, 4),
        "stress_survival": stress_survival,
        "drawdown_penalty": round(drawdown_penalty, 4),
        "negative_outcome_probability": round(negative_prob, 4),
        "simulation_only": True,
    }
