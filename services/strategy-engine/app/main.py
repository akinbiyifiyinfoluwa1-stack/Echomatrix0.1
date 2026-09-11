"""Strategy API for generating normalized market proposals."""
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI

from app.engine import StrategyEngine
from app.models import MarketSnapshot, StrategyConfig

app = FastAPI(
    title="EchoMatrix Strategy Engine",
    description="Baseline strategy and trade-proposal layer for the EchoMatrix capital brain.",
    version="0.1.0",
)


def _evaluate(snapshot: MarketSnapshot):
    config = StrategyConfig(
        name="baseline-momentum",
        momentum_threshold=Decimal("0.005"),
        minimum_volume=Decimal("1"),
    )
    return StrategyEngine(config).evaluate(snapshot)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "echomatrix-strategy-engine",
        "message": "Turn market observations into structured proposals.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "strategy-engine"}


@app.post("/evaluate", tags=["strategy"])
def evaluate(snapshot: MarketSnapshot) -> dict:
    return _evaluate(snapshot).model_dump(mode="json")


@app.get("/demo/proposal", tags=["demo"])
def demo_proposal() -> dict:
    snapshot = MarketSnapshot(
        symbol="BTC/USD",
        price=Decimal("101000"),
        previous_price=Decimal("100000"),
        volume=Decimal("12.5"),
        timestamp=datetime.now(timezone.utc),
    )
    return _evaluate(snapshot).model_dump(mode="json")
