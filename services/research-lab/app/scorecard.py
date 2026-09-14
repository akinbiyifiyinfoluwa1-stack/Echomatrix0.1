"""Unified research scorecard for simulation experiments."""
from __future__ import annotations
from decimal import Decimal

D = Decimal


def _d(value) -> D:
    return D(str(value))


def score(summary: dict, metrics: dict) -> dict:
    """Turn simulation metrics into a comparable, bounded research score."""
    ret = _d(summary.get("return_pct", 0))
    drawdown = abs(_d(metrics.get("max_drawdown_pct", 0)))
    win_rate = _d(summary.get("win_rate", 0))
    profit_factor = _d(summary.get("profit_factor", 0))
    risk_penalty = min(drawdown / D("100"), D("1"))
    return_bonus = max(min(ret / D("100"), D("1")), D("-1"))
    pf_bonus = min(profit_factor / D("3"), D("1")) if profit_factor >= 0 else D("0")
    total = D("0.40") * return_bonus + D("0.25") * win_rate + D("0.20") * pf_bonus + D("0.15") * (D("1") - risk_penalty)
    return {
        "score": str(total.quantize(D("0.0001"))),
        "return_component": str(return_bonus.quantize(D("0.0001"))),
        "win_rate_component": str(win_rate.quantize(D("0.0001"))),
        "profit_factor_component": str(pf_bonus.quantize(D("0.0001"))),
        "risk_component": str((D("1") - risk_penalty).quantize(D("0.0001"))),
    }


def robustness(results: list[dict]) -> dict:
    """Rank experiments by baseline score while penalizing scenario instability."""
    ranked = []
    for item in results:
        scenario_scores = [_d(x.get("score", 0)) for x in item.get("scenario_scores", [])]
        baseline = _d(item.get("score", 0))
        if scenario_scores:
            worst = min(scenario_scores)
            spread = max(scenario_scores) - worst
            robust = baseline * D("0.70") + worst * D("0.20") - min(spread, D("1")) * D("0.10")
        else:
            worst = baseline
            spread = D("0")
            robust = baseline
        ranked.append({**item, "worst_scenario_score": str(worst), "scenario_spread": str(spread), "robustness_score": str(robust)})
    ranked.sort(key=lambda x: _d(x["robustness_score"]), reverse=True)
    for idx, item in enumerate(ranked, 1):
        item["robustness_rank"] = idx
    return {"experiment_count": len(ranked), "ranked": ranked, "winner": ranked[0] if ranked else None}
