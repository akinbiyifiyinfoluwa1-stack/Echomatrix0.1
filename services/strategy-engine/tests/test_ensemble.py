from datetime import datetime, timezone
from decimal import Decimal

from app.engine import StrategyEngine
from app.models import MarketSnapshot, StrategyConfig, Signal


def _engine() -> StrategyEngine:
    return StrategyEngine(
        StrategyConfig(
            name="baseline-momentum",
            momentum_threshold=Decimal("0.005"),
            minimum_volume=Decimal("1"),
        )
    )


def test_ensemble_confirms_strong_positive_observation() -> None:
    result = _engine().ensemble(
        MarketSnapshot(
            symbol="BTC/USD",
            price=Decimal("101000"),
            previous_price=Decimal("100000"),
            volume=Decimal("12.5"),
            timestamp=datetime.now(timezone.utc),
        )
    )
    assert result.signal == Signal.BUY
    assert result.regime == "bullish-momentum"
    assert result.confidence > Decimal("0")
    assert len(result.components) == 3
    assert result.proposal.strategy == "deterministic-ensemble-v1"


def test_ensemble_stays_neutral_when_price_change_is_small() -> None:
    result = _engine().ensemble(
        MarketSnapshot(
            symbol="BTC/USD",
            price=Decimal("100200"),
            previous_price=Decimal("100000"),
            volume=Decimal("12.5"),
            timestamp=datetime.now(timezone.utc),
        )
    )
    assert result.signal == Signal.HOLD
    assert result.regime == "neutral"
