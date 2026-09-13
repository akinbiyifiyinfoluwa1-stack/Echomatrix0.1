from pathlib import Path


PIPELINE = Path(__file__).resolve().parents[1] / "app" / "pipeline.py"


def test_pipeline_uses_research_context_and_strategy_ensemble() -> None:
    source = PIPELINE.read_text(encoding="utf-8")
    assert '"/ensemble"' in source
    assert '"/market-context"' in source
    assert 'stages.append("strategy-ensemble")' in source
    assert 'stages.append("research-context")' in source


def test_pipeline_remains_simulation_only() -> None:
    source = PIPELINE.read_text(encoding="utf-8")
    assert '"simulation"' in source
    assert 'broker' not in source.lower() or "no broker" in source.lower()
