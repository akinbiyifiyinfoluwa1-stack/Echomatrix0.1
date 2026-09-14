"""Market Data service: real market observations for the EchoMatrix brain."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query

from app.binance_public import BinancePublicProvider
from app.models import AssetClass, Candle, Instrument, MarketTick
from app.normalizer import normalize_candles
from app.providers import MarketDataProviderError

app = FastAPI(
    title="EchoMatrix Market Data",
    description="Read-only real market-data layer for the EchoMatrix Financial & Wealth OS.",
    version="1.0.0",
)
provider = BinancePublicProvider()


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "service": "echomatrix-market-data",
        "mode": "real-market-data-read-only",
        "provider": provider.name,
        "execution": False,
        "message": "The brain receives real market observations before any execution layer exists.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "service": "market-data", "mode": "real-market-data-read-only", "provider": provider.name, "execution": False}


@app.get("/market/candles", tags=["real-market-data"])
def market_candles(
    symbol: str = Query(default="BTC/USD"),
    timeframe: str = Query(default="1m"),
    limit: int = Query(default=100, ge=2, le=1000),
) -> dict:
    """Fetch actual public market candles and pass them through quality gates."""
    try:
        candles = normalize_candles(provider.fetch_candles(symbol, timeframe, limit))
    except MarketDataProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "mode": "real-market-data-read-only",
        "source": provider.name,
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "count": len(candles),
        "latest": {
            "timestamp": candles[-1].timestamp,
            "open": str(candles[-1].open),
            "high": str(candles[-1].high),
            "low": str(candles[-1].low),
            "close": str(candles[-1].close),
            "volume": str(candles[-1].volume),
        },
        "candles": [
            {
                "timestamp": candle.timestamp,
                "open": str(candle.open),
                "high": str(candle.high),
                "low": str(candle.low),
                "close": str(candle.close),
                "volume": str(candle.volume),
                "source": candle.source,
            }
            for candle in candles
        ],
    }


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
    """Test fixture only; not an intelligence input."""
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
    candle = demo_candle()
    return MarketTick(
        instrument=candle.instrument,
        timestamp=candle.timestamp,
        bid=candle.close - Decimal("5"),
        ask=candle.close + Decimal("5"),
        last=candle.close,
        volume=candle.volume,
    )
