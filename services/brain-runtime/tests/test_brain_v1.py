from app.brain_v1 import build_brain_v1_cycle, research_scorecard


def test_brain_v1_cycle_is_auditable_and_simulation_only():
    result = build_brain_v1_cycle(
        symbol="BTCUSDT", timeframe="1h", data_quality={"valid": True},
        market_state={"regime": "normal-volatility", "volatility": .01},
        research={"status": "ready", "confidence": .8},
        strategy={"name": "ensemble", "confidence": .7},
        ai_council={"consensus": "BUY", "confidence": .8},
        risk={"status": "approved", "confidence": .8},
        allocation={"status": "simulated", "confidence": .8},
        simulation={"status": "complete", "total_pnl": 12.5},
        learning={"key": "normal:trend", "new": .03},
        durable_memory_hash="abc123def456",
    )
    assert result["schema"] == "echomatrix.brain.v1"
    assert result["execution"] is False
    assert result["decision_attribution"]["conclusion"] == "BUY"
    assert len(result["evidence"]) >= 8


def test_scorecard_requires_oos_and_stress_for_ready_gate():
    replay = {"status": "complete", "simulation_only": True, "max_drawdown_pct": 12, "return_pct": 4, "win_rate": .6}
    weak = research_scorecard(replay, provider_reliability=.8)
    assert weak["gate"] in {"WEAK EVIDENCE", "FAILED VALIDATION"}
    ready = research_scorecard(replay, oos={"passed": True}, stress={"passed": True}, monte_carlo={"passed": True}, provider_reliability=.8)
    assert ready["gate"] == "READY FOR MORE RESEARCH"
