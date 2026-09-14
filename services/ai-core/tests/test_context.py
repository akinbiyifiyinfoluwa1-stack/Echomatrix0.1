from app.context import build_decision_prompt
from app.main import health, root


def test_context_prompt_contains_all_brain_layers() -> None:
    prompt = build_decision_prompt({
        "observation": {"symbol": "BTC/USD"},
        "strategy": {"strategy": "ensemble"},
        "research": {"confidence": "0.8"},
        "risk": {"risk_score": "0.2"},
        "memory": [{"title": "prior lesson"}],
    })
    assert "BTC/USD" in prompt
    assert "ensemble" in prompt
    assert "prior lesson" in prompt


def test_ai_core_advertises_context_engine() -> None:
    assert root()["context_engine"] == "enabled"
    assert health()["mode"] == "simulation"
