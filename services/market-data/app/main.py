"""Market Data service: the first sensory layer of the EchoMatrix brain."""
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI

from app.models import AssetClass, Candle, Instrument, MarketTick

app = FastAPI(
    title="EchoMatrix Market Data",
    description="Canonical market-data layer for the EchoMatrix Financial & Wealth OS.",
    version="0.2.0",
)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "echomatrix-market-data",
        "message": "The brain needs senses before it needs a body.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "market-data"}


def demo_instrument() -> Instrument:
    return Instrument(
        symbol="BTC/USD",
        name="Bitcoin / US Dollar",
        asset_class=AssetClass.CRYPTO,
        base_currency="BTC",
        quote_currency="USD",
        exchange="demo",
    )


@app.get("/demo/instrument", response_model=Instrument, tags=["demo"])
def instrument() -> Instrument:
    return demo_instrument()


@app.get("/demo/candle", response_model=Candle, tags=["demo"])
def demo_candle() -> Candle:
    return Candle(
        instrument=demo_instrument(),
        timestamp=datetime.now(timezone.utc),
        timeframe="1m",
        open=Decimal("100000"),
        high=Decimal("100250"),
        low=Decimal("99800"),
        close=Decimal("100150"),
        volume=Decimal("12.5"),
    )


@app.get("/demo/snapshot", response_model=MarketTick, tags=["demo"])
def demo_snapshot() -> MarketTick:
    """Return a normalized latest-price observation for downstream services."""
    candle = demo_candle()
    return MarketTick(
        instrument=candle.instrument,
        timestamp=candle.timestamp,
        bid=candle.close - Decimal("5"),
        ask=candle.close + Decimal("5"),
        last=candle.close,
        volume=candle.volume,
    )
