"""Unified research laboratory: experiments, scenarios and robustness."""
from __future__ import annotations
from decimal import Decimal
from app.contracts import Candle
from app.engine import run_research
from app.scenarios import scenario_matrix
from app.scorecard import score, robustness

D = Decimal


def run_lab(symbol: str, candles: list[Candle], initial_cash: D, fee_rate: D, thresholds: list[D], allocations: list[D], shock_pct: D) -> dict:
    scenarios = scenario_matrix(candles, shock_pct)
    experiments = []
    for threshold in thresholds:
        for allocation in allocations:
            base = run_research(symbol, candles, initial_cash, fee_rate, allocation, threshold)
            base_score = score(base["summary"], base["metrics"])
            scenario_scores = []
            scenario_summaries = {}
            for name, series in scenarios.items():
                report = run_research(symbol, series, initial_cash, fee_rate, allocation, threshold)
                scenario_score = score(report["summary"], report["metrics"])
                scenario_scores.append(scenario_score)
                scenario_summaries[name] = {"summary": report["summary"], "metrics": report["metrics"], "score": scenario_score["score"]}
            experiments.append({
                "name": f"threshold={threshold};allocation={allocation}",
                "threshold": str(threshold),
                "allocation": str(allocation),
                "score": base_score["score"],
                "scorecard": base_score,
                "scenario_scores": scenario_scores,
                "scenarios": scenario_summaries,
            })
    ranked = robustness(experiments)
    return {
        "mode": "simulation-only",
        "symbol": symbol,
        "research_lab_version": "2.0",
        "scenario_count": len(scenarios),
        "scenario_names": list(scenarios),
        "thresholds_tested": [str(x) for x in thresholds],
        "allocations_tested": [str(x) for x in allocations],
        "shock_pct": str(shock_pct),
        **ranked,
    }
