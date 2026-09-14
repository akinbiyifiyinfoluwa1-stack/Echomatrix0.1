import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from app.advanced import (
    DurableMemory, ExternalIntelligence, Hardening, SystemEvaluator,
    StrategyCandidate, evaluate_providers, evolve_strategies, full_brain_replay,
    portfolio_intelligence,
)
from app.models import Candle
from decimal import Decimal


def candles(n=80):
    out=[]
    for i in range(n):
        p=100+i*0.15+(i%7)*0.03
        out.append(Candle(timestamp=i,symbol="TEST",timeframe="1h",open=Decimal(str(p)),high=Decimal(str(p+1)),low=Decimal(str(p-1)),close=Decimal(str(p)),volume=Decimal("100"),source="test"))
    return out


def test_full_brain_replay_runs_future_mark():
    result=full_brain_replay(candles())
    assert result["status"] == "complete"
    assert result["simulation_only"] is True
    assert result["external_execution"] is False
    assert result["bars"] == 80


def test_strategy_evolution():
    result=evolve_strategies([StrategyCandidate("a",.5,.3,.2,.2),StrategyCandidate("b",.2,.6,.2,.2)], {"a":.8,"b":.2}, 2)
    assert result["champion"]["name"] == "a"


def test_provider_evaluation_and_portfolio():
    ranked=evaluate_providers({"gemini":[{"valid":True,"label":"BUY","latency_ms":10,"cost_score":.8}],"groq":[{"valid":True,"label":"SELL","latency_ms":20,"cost_score":.9}]})
    assert ranked["leader"] in {"gemini","groq"}
    p=portfolio_intelligence([{"pnl":2,"action":"BUY"},{"pnl":-1,"action":"SELL"}])
    assert p["outcome_count"] == 2


def test_external_intelligence_and_hardening():
    items=ExternalIntelligence().normalize([{"source":"test","text":"headline","sentiment":2,"reliability":-1}])
    assert items[0]["sentiment"] == 1.0 and items[0]["reliability"] == 0.0
    assert Hardening.run({"LIVE_EXECUTION":"false"})["passed"]
    assert not Hardening.run({"LIVE_EXECUTION":"true"})["passed"]


def test_durable_memory_and_evaluator(tmp_path):
    memory=DurableMemory(str(tmp_path/"memory.jsonl"))
    digest=memory.write({"kind":"test","value":1})
    assert len(digest) == 64
    assert memory.read()[0]["event"]["value"] == 1
    evaluation=SystemEvaluator().evaluate({"status":"complete","simulation_only":True,"external_execution":False})
    assert evaluation["passed"]
