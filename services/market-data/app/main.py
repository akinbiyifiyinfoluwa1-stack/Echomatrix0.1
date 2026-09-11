"""Market Data service: the first sensory layer of the Ecometrics brain."""
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI

from app.models import AssetClass, Candle, Instrument

app = FastAPI(
    title="Ecometrics Market Data",
    description="Canonical market-data layer for the Ecometrics Financial & Wealth OS.",
    version="0.1.0",
)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "ecometrics-market-data",
        "message": "The brain needs senses before it needs a body.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "market-data"}


@app.get("/demo/instrument", response_model=Instrument, tags=["demo"])
def demo_instrument() -> Instrument:
    return Instrument(
        symbol="BTC/USD",
        name="Bitcoin / US Dollar",
        asset_class=AssetClass.CRYPTO,
        base_currency="BTC",
        quote_currency="USD",
        exchange="demo",
    )


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
