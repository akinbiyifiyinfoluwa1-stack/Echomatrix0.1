"""Strategy ensemble used only for simulated research."""

def strategy_snapshot(features: dict, research: dict) -> dict:
    trend = features["trend"]
    volume_ok = 0.8 <= float(features["volume_ratio"]) <= 1.8
    score = 0.0
    if trend == "up": score += 0.45
    elif trend == "down": score -= 0.45
    if volume_ok: score += 0.15 if score > 0 else -0.15 if score < 0 else 0
    action = "BUY" if score > 0.35 else "SELL" if score < -0.35 else "HOLD"
    return {"action": action, "score": round(score, 4), "strategies": ["trend", "volume-confirmation", "regime-filter"], "research_hypothesis": research["hypothesis"], "simulation_only": True}
