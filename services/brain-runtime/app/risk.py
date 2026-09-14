"""Independent simulation risk gate."""

def risk_snapshot(features: dict, strategy: dict, equity: float = 10000.0) -> dict:
    vol = float(features["realized_volatility"])
    drawdown_budget = 0.02 if vol < 0.02 else 0.01
    confidence = max(0.0, min(1.0, abs(float(strategy["score"])) * 1.5))
    approved = strategy["action"] != "HOLD" and confidence >= 0.45 and vol < 0.10
    return {"approved": approved, "confidence": round(confidence, 4), "risk_budget_fraction": drawdown_budget, "estimated_volatility": vol, "reason": "approved" if approved else "risk gate rejected", "external_execution": False, "equity_reference": equity}
