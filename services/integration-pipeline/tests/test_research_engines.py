from decimal import Decimal

import pytest

from app.dataset import MarketObservation, close_series, normalize_observations
from app.experiments import ExperimentSpec, run_experiment_registry
from app.walk_forward import walk_forward_replay


def obs(ts: str, close: str) -> MarketObservation:
    price = Decimal(close)
    return MarketObservation(ts, "BTC/USD", price, price, price, price, Decimal("1"))


def test_dataset_normalizes_and_orders_observations() -> None:
    rows = normalize_observations([obs("2026-01-03", "103"), obs("2026-01-01", "100"), obs("2026-01-02", "101")])
    assert [row.timestamp for row in rows] == ["2026-01-01", "2026-01-02", "2026-01-03"]
    assert close_series(rows) == [Decimal("100"), Decimal("101"), Decimal("103")]


def test_dataset_rejects_duplicate_timestamp() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        normalize_observations([obs("2026-01-01", "100"), obs("2026-01-01", "101")])


def test_walk_forward_produces_multiple_out_of_sample_windows() -> None:
    prices = [Decimal(str(value)) for value in [100, 101, 103, 104, 102, 105, 108, 107, 110, 112]]
    result = walk_forward_replay(prices, train_size=4, test_size=3, step=2)
    assert result["mode"] == "simulation-only"
    assert result["method"] == "walk-forward"
    assert result["aggregate"]["window_count"] == 2
    assert len(result["windows"]) == 2


def test_experiment_registry_ranks_policies() -> None:
    prices = [Decimal(str(value)) for value in [100, 102, 105, 103, 108, 110]]
    result = run_experiment_registry(
        prices,
        [
            ExperimentSpec("sensitive", Decimal("0.10"), Decimal("0.005")),
            ExperimentSpec("conservative", Decimal("0.05"), Decimal("0.02")),
        ],
    )
    assert result["mode"] == "simulation-only"
    assert result["experiment_count"] == 2
    assert result["best"]["name"] in {"sensitive", "conservative"}
