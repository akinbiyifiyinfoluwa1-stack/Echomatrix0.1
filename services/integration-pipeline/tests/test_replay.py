from decimal import Decimal

import pytest

from app.models import ReplayRequest
from app.replay import replay_market_series


def test_replay_request_rejects_short_series():
    with pytest.raises(ValueError):
        replay_market_series([Decimal("100")])


def test_replay_request_runs_multiple_market_states():
    result = replay_market_series(
        [Decimal("100"), Decimal("101"), Decimal("103"), Decimal("101"), Decimal("105")],
        allocation_fraction=Decimal("0.10"),
    )
    assert result["mode"] == "simulation-only"
    assert result["summary"]["cycles"] == 5
    assert len(result["cycles"]) == 5
    assert "return_pct" in result["summary"]


def test_replay_contract_defaults():
    request = ReplayRequest(prices=[Decimal("100"), Decimal("101")])
    assert request.symbol == "BTC/USD"
    assert request.initial_cash == Decimal("10000")
