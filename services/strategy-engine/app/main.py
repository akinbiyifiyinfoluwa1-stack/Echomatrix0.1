"""Strategy API for generating normalized market proposals."""
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI

from app.engine import StrategyEngine
from app.models import MarketSnapshot, StrategyConfig

app = FastAPI(
    title="Ecometrics Strategy Engine",
    description="Baseline strategy and trade-proposal layer for the Ecometrics capital brain.",
    version="0.1.0",
)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "ecometrics-strategy-engine",
        "message": "Turn market observations into structured proposals.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "strategy-engine"}


@app.get("/demo/proposal", tags=["demo"])
def demo_proposal() -> dict:
    config = StrategyConfig(
        name="baseline-momentum",
        momentum_threshold=Decimal("0.005"),
        minimum_volume=Decimal("1"),
    )
    snapshot = MarketSnapshot(
        symbol="BTC/USD",
        price=Decimal("101000"),
        previous_price=Decimal("100000"),
        volume=Decimal("12.5"),
        timestamp=datetime.now(timezone.utc),
    )
    proposal = StrategyEngine(config).evaluate(snapshot)
    return proposal.model_dump(mode="json")
