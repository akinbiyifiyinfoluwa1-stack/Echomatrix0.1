from decimal import Decimal

from app.engine import ResearchEngine
from app.models import MarketResearchRequest


def test_market_context_preserves_observation_and_marks_demo_source() -> None:
    result = ResearchEngine().market_context(
        MarketResearchRequest(
            symbol="BTC/USD",
            price=Decimal("101000"),
            previous_price=Decimal("100000"),
            volume=Decimal("12.5"),
            source="market-data-demo",
        )
    )
    assert result.direction == "up"
    assert result.source == "market-data-demo"
    assert result.research.sources == []
    assert result.research.confidence == 0.7


def test_market_context_handles_zero_volume_without_fake_liquidity() -> None:
    result = ResearchEngine().market_context(
        MarketResearchRequest(
            symbol="TEST/USD",
            price=Decimal("100"),
            previous_price=Decimal("100"),
            volume=Decimal("0"),
        )
    )
    assert result.direction == "flat"
    assert result.evidence_quality == "price_only_observation"
    assert result.confidence == Decimal("0.45")
