from decimal import Decimal
from app.contracts import Candle, ExperimentRequest
from app.lab import run_lab
from app.scenarios import scenario_matrix


def candles():
    return [Candle(timestamp=i, open=100+i, high=102+i, low=99+i, close=101+i, volume=1000+i*10) for i in range(8)]


def test_scenario_matrix_contains_all_modes():
    result = scenario_matrix(candles(), Decimal("0.10"))
    assert set(result) == {"baseline", "upside_shock", "downside_shock", "high_volume", "low_liquidity"}
    assert len(result["baseline"]) == 8
    assert result["upside_shock"][-1].close > result["baseline"][-1].close
    assert result["downside_shock"][-1].close < result["baseline"][-1].close


def test_unified_lab_ranks_experiments():
    result = run_lab("BTC/USD", candles(), Decimal("10000"), Decimal("0.001"), [Decimal("0.003"), Decimal("0.005")], [Decimal("0.05"), Decimal("0.10")], Decimal("0.10"))
    assert result["mode"] == "simulation-only"
    assert result["scenario_count"] == 5
    assert result["experiment_count"] == 4
    assert result["winner"] is not None
    assert result["winner"]["robustness_rank"] == 1
