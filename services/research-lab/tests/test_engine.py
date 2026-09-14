from decimal import Decimal
from app.contracts import Candle
from app.engine import run_research, compare, stress

def candles():
    closes = [Decimal(x) for x in ["100", "101", "103", "102", "105", "108", "107", "110"]]
    return [Candle(timestamp=i, open=p, high=p*Decimal("1.01"), low=p*Decimal("0.99"), close=p, volume=Decimal("100")+i) for i,p in enumerate(closes)]

def test_research_is_simulation_only():
    result = run_research("BTC/USD", candles(), Decimal("10000"), Decimal("0.001"), Decimal("0.10"), Decimal("0.005"))
    assert result["mode"] == "simulation-only"
    assert "features" in result and "metrics" in result

def test_experiments_rank_and_return_winner():
    result = compare("BTC/USD", candles(), Decimal("10000"), Decimal("0.001"), [Decimal("0.003"), Decimal("0.005")], [Decimal("0.10"), Decimal("0.20")])
    assert result["experiment_count"] == 4
    assert result["winner"]["rank"] == 1

def test_stress_has_three_scenarios():
    result = stress("BTC/USD", candles(), Decimal("10000"), Decimal("0.001"), Decimal("0.10"), Decimal("0.005"), Decimal("0.10"))
    assert set(["baseline", "up_shock", "down_shock"]).issubset(result)
