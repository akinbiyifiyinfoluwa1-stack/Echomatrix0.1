from app.brain_v1 import build_brain_v1_pipeline_record


def test_brain_v1_record_is_auditable_and_simulation_only():
    record = build_brain_v1_pipeline_record(
        correlation_id="corr-123",
        symbol="BTC/USD",
        observation={"price": "100", "previous_price": "99"},
        strategy={"strategy": "trend", "confidence": 0.8},
        research={"summary": "validated context", "confidence": 0.75},
        ai_analysis={"provider": "disabled", "content": "AI disabled for this run"},
        risk={"status": "approved", "confidence": 0.9},
        allocation={"status": "simulated", "allocated_capital": "100"},
        decision={"action": "buy", "confidence": 0.8, "risk_amount": "2"},
        simulation_fill={"status": "complete", "simulated_pnl": "3"},
        portfolio_state={"equity": "10003"},
        learning_result={"status": "updated"},
        memory_context=[{"memory_id": "m1"}],
        persisted_record_id="record-1",
    )
    assert record["schema"] == "echomatrix.brain.v1"
    assert record["execution"] is False
    assert record["simulation_only"] is True
    assert record["real_money_execution"] is False
    assert record["decision_attribution"]["conclusion"] == "buy"
    assert "risk" in record["decision_attribution"]["primary_drivers"]


def test_brain_v1_cycle_id_is_deterministic_for_same_correlation():
    kwargs = dict(
        correlation_id="same-correlation",
        symbol="ETH/USD",
        observation={},
        strategy={},
        research={},
        ai_analysis=None,
        risk={},
        allocation={},
        decision={"action": "hold"},
        simulation_fill=None,
        portfolio_state=None,
        learning_result=None,
        memory_context=[],
        persisted_record_id=None,
    )
    assert build_brain_v1_pipeline_record(**kwargs)["cycle_id"] == build_brain_v1_pipeline_record(**kwargs)["cycle_id"]
