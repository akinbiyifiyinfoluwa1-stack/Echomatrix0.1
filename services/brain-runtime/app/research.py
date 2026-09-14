"""Research layer: regime, evidence and hypotheses from point-in-time features."""


def research_snapshot(features: dict) -> dict:
    regime = features["regime"]
    trend = features["trend"]
    vol = float(features["realized_volatility"])
    evidence = [f"trend={trend}", f"regime={regime}", f"realized_volatility={vol:.6f}", f"volume_ratio={features['volume_ratio']}"]
    confidence = max(0.0, min(1.0, 0.5 + abs(float(features["mean_return"])) * 10.0))
    hypothesis = "continuation" if trend != "flat" else "mean-reversion-watch"
    return {"regime": regime, "hypothesis": hypothesis, "evidence": evidence, "confidence": round(confidence, 4), "point_in_time": True}
