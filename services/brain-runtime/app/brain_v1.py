"""EchoMatrix Brain V1 consolidation layer. Simulation/research only."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

@dataclass(frozen=True)
class Evidence:
    stage: str
    summary: str
    inputs: list[str]
    confidence: float

def _clip(value: float) -> float:
    return max(0.0, min(1.0, float(value)))

def build_brain_v1_cycle(*, symbol: str, timeframe: str, data_quality: dict[str, Any], market_state: dict[str, Any], research: dict[str, Any], strategy: dict[str, Any], ai_council: dict[str, Any], risk: dict[str, Any], allocation: dict[str, Any], simulation: dict[str, Any], learning: dict[str, Any], durable_memory_hash: str) -> dict[str, Any]:
    """Return one canonical, auditable cognitive-cycle record."""
    evidence = [
        Evidence("market-data", f"Observed {symbol} on {timeframe}", ["market.candles"], _clip(1.0 if data_quality.get("valid") else 0.0)),
        Evidence("market-state", str(market_state.get("regime", "unknown")), ["features", "market-state"], _clip(1.0 - float(market_state.get("volatility", 1.0)))),
        Evidence("research", str(research.get("status", research.get("signal", "available"))), ["research"], _clip(float(research.get("confidence", .5)))),
        Evidence("strategy", str(strategy.get("name", strategy.get("status", "ensemble"))), ["strategy"], _clip(float(strategy.get("confidence", .5)))),
        Evidence("ai-council", str(ai_council.get("consensus", "none")), ["provider-responses"], _clip(float(ai_council.get("confidence", .5)))),
        Evidence("risk", str(risk.get("status", risk.get("decision", "gated"))), ["risk"], _clip(float(risk.get("confidence", .5)))),
        Evidence("allocation", str(allocation.get("status", "simulated")), ["capital-allocation"], _clip(float(allocation.get("confidence", .5)))),
        Evidence("simulation", str(simulation.get("status", "complete")), ["future-bar-replay"], _clip(1.0 if simulation.get("status") == "complete" else .5)),
        Evidence("learning", "Evidence weight updated", ["outcome", "learner"], .8),
        Evidence("memory", durable_memory_hash[:12], ["durable-memory"], 1.0),
    ]
    payload = {
        "schema": "echomatrix.brain.v1", "cycle_id": sha256(f"{symbol}|{timeframe}|{durable_memory_hash}".encode()).hexdigest()[:20],
        "created_at": datetime.now(timezone.utc).isoformat(), "mode": "simulation-only", "execution": False,
        "symbol": symbol, "timeframe": timeframe, "evidence": [asdict(x) for x in evidence],
        "inputs": {"data_quality": data_quality, "market_state": market_state, "research": research, "strategy": strategy, "ai_council": ai_council},
        "controls": {"risk": risk, "allocation": allocation}, "outcome": simulation, "learning": learning,
        "durable_memory_hash": durable_memory_hash,
        "decision_attribution": {
            "conclusion": ai_council.get("consensus", strategy.get("status", "hold")),
            "primary_drivers": [e.stage for e in evidence if e.confidence >= .5],
            "risk_constraint": risk.get("status", "unknown"), "capital_constraint": allocation.get("status", "unknown"),
            "simulation_result": simulation.get("total_pnl", simulation.get("simulated_pnl", 0)),
        },
    }
    return payload

def research_scorecard(replay: dict[str, Any], *, oos: dict[str, Any] | None = None, stress: dict[str, Any] | None = None, monte_carlo: dict[str, Any] | None = None, provider_reliability: float = 0.0) -> dict[str, Any]:
    """Turn validation evidence into a conservative Brain V1 research gate."""
    oos, stress, monte_carlo = oos or {}, stress or {}, monte_carlo or {}
    checks = {
        "simulation_complete": replay.get("status") == "complete", "simulation_only": replay.get("simulation_only") is True,
        "oos_available": bool(oos), "stress_available": bool(stress), "monte_carlo_available": bool(monte_carlo),
        "drawdown_bounded": float(replay.get("max_drawdown_pct", 999)) < 50.0,
        "provider_reliability": _clip(provider_reliability) >= .6,
    }
    score = sum(checks.values()) / len(checks)
    gate = "READY FOR MORE RESEARCH" if score >= .85 and checks["oos_available"] and checks["stress_available"] else "WEAK EVIDENCE" if score >= .55 else "FAILED VALIDATION"
    return {"schema": "echomatrix.research-scorecard.v1", "gate": gate, "score": round(score, 4), "checks": checks,
            "metrics": {"return_pct": replay.get("return_pct", 0), "max_drawdown_pct": replay.get("max_drawdown_pct", 0), "win_rate": replay.get("win_rate", 0), "oos": oos, "stress": stress, "monte_carlo": monte_carlo, "provider_reliability": provider_reliability},
            "simulation_only": True, "real_money_execution": False}
