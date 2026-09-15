"""Canonical Brain V1 record builder for the integration pipeline.

Simulation/research only. This adapter turns the already-completed pipeline stages
into one auditable cognitive-cycle record without adding execution capability.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any


def build_brain_v1_pipeline_record(
    *,
    correlation_id: str,
    symbol: str,
    observation: dict[str, Any],
    strategy: dict[str, Any],
    research: dict[str, Any],
    ai_analysis: dict[str, Any] | None,
    risk: dict[str, Any],
    allocation: dict[str, Any],
    decision: dict[str, Any],
    simulation_fill: dict[str, Any] | None,
    portfolio_state: dict[str, Any] | None,
    learning_result: dict[str, Any] | None,
    memory_context: list[dict[str, Any]],
    persisted_record_id: str | None,
) -> dict[str, Any]:
    """Build one deterministic, traceable Brain V1 record from a pipeline run."""
    ai = ai_analysis or {}
    simulation = simulation_fill or {"status": "not-run", "simulation_only": True}
    cycle_id = sha256(correlation_id.encode()).hexdigest()[:20]
    confidence = float(decision.get("confidence", 0) or 0)
    risk_status = str(risk.get("status", risk.get("decision", "unknown")))
    allocation_status = str(allocation.get("status", "simulated"))
    conclusion = str(decision.get("action", "hold"))

    evidence = [
        {"stage": "market-data", "summary": f"Observed {symbol}", "inputs": ["observation"], "confidence": 1.0},
        {"stage": "research", "summary": str(research.get("summary", research.get("status", "available"))), "inputs": ["research-context"], "confidence": float(research.get("confidence", 0.0) or 0.0)},
        {"stage": "strategy", "summary": str(strategy.get("strategy", strategy.get("status", "ensemble"))), "inputs": ["strategy-ensemble"], "confidence": float(strategy.get("confidence", confidence) or confidence)},
        {"stage": "ai-council", "summary": str(ai.get("content", ai.get("consensus", "disabled"))), "inputs": ["ai-core"], "confidence": float(ai.get("confidence", confidence) or confidence)},
        {"stage": "risk", "summary": risk_status, "inputs": ["risk"], "confidence": float(risk.get("confidence", 0.0) or 0.0)},
        {"stage": "allocation", "summary": allocation_status, "inputs": ["capital-allocation"], "confidence": confidence},
        {"stage": "simulation", "summary": str(simulation.get("status", "not-run")), "inputs": ["simulation-fill"], "confidence": confidence if simulation_fill else 0.0},
        {"stage": "learning", "summary": "Learning update recorded", "inputs": ["outcome", "learning-loop"], "confidence": 0.8 if learning_result else 0.0},
        {"stage": "memory", "summary": f"{len(memory_context)} prior lessons recalled", "inputs": ["intelligence-memory"], "confidence": 1.0},
    ]

    return {
        "schema": "echomatrix.brain.v1",
        "cycle_id": cycle_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "simulation-only",
        "execution": False,
        "correlation_id": correlation_id,
        "symbol": symbol,
        "observation": observation,
        "evidence": evidence,
        "decision_attribution": {
            "conclusion": conclusion,
            "primary_drivers": [item["stage"] for item in evidence if item["confidence"] >= 0.5],
            "risk_constraint": risk_status,
            "capital_constraint": allocation_status,
            "simulation_result": simulation.get("simulated_pnl", simulation.get("pnl", 0)),
            "memory_recalled": len(memory_context),
        },
        "inputs": {
            "strategy": strategy,
            "research": research,
            "ai_analysis": ai,
            "risk": risk,
            "allocation": allocation,
        },
        "outcome": simulation,
        "portfolio_state": portfolio_state,
        "learning": learning_result,
        "persisted_record_id": persisted_record_id,
        "simulation_only": True,
        "real_money_execution": False,
    }
