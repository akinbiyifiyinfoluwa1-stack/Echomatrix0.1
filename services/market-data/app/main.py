"""Market Data service: broad real market observations for the EchoMatrix brain."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query

from app.biquote_public import BiquotePublicProvider
from app.binance_public import BinancePublicProvider
from app.coinbase_public import CoinbasePublicProvider
from app.collector import MarketCollector
from app.models import AssetClass, Candle, Instrument, MarketTick
from app.normalizer import normalize_candles
from app.providers import MarketDataProviderError

providers = {
    "biquote-public": BiquotePublicProvider(),
    "binance-public": BinancePublicProvider(),
    "coinbase-public": CoinbasePublicProvider(),
}


def _collector_error(exc: Exception) -> None:
    print(f"[market-collector] {exc}")


collector = MarketCollector(providers)


@asynccontextmanager
async def lifespan(app: FastAPI):
    symbols = [
        s.strip().upper()
        for s in os.getenv(
            "MARKET_COLLECT_SYMBOLS",
            "EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD,NZDUSD,USDCHF,XAUUSD,USOIL,UKOIL,US30,US500,USTEC,DE40,UK100,AAPL,MSFT,NVDA,TSLA,SPY,QQQ,BTC/USD,ETH/USD",
        ).split(",")
        if s.strip()
    ]
    timeframe = os.getenv("MARKET_COLLECT_TIMEFRAME", "1h")
    interval = int(os.getenv("MARKET_COLLECT_INTERVAL_SECONDS", "60"))
    collector.start(symbols, timeframe, interval_seconds=interval, limit=100, on_error=_collector_error)
    yield
    collector.stop()


app = FastAPI(
    title="EchoMatrix Market Data",
    description="Read-only real market-data layer for the EchoMatrix Financial & Wealth OS.",
    version="1.2.0",
    lifespan=lifespan,
)


def _provider(name: str):
    if name not in providers:
        raise HTTPException(status_code=400, detail=f"unknown market-data provider: {name}")
    return providers[name]


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "service": "echomatrix-market-data",
        "mode": "real-market-data-read-only",
        "providers": list(providers),
        "coverage": ["forex", "stocks", "indices", "commodities", "metals", "energy", "crypto"],
        "automatic_collection": True,
        "execution": False,
        "message": "The brain receives real market observations before any execution layer exists.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {
        "status": "ok",
        "service": "market-data",
        "mode": "real-market-data-read-only",
        "providers": list(providers),
        "automatic_collection": True,
        "last_collection": collector.last_run,
        "execution": False,
    }


@app.get("/market/providers", tags=["real-market-data"])
def market_providers() -> dict:
    return {
        "mode": "real-market-data-read-only",
        "providers": [
            {
                "name": name,
                "execution": False,
                "coverage": ["forex", "stocks", "indices", "commodities", "metals", "energy"]
                if name == "biquote-public"
                else ["crypto"],
            }
            for name in providers
        ],
    }


@app.get("/market/symbols", tags=["real-market-data"])
def market_symbols(
    asset_type: str | None = Query(default=None),
    live_only: bool = False,
    limit: int = Query(default=500, ge=1, le=2000),
) -> dict:
    """Discover the broad multi-asset instrument catalogue."""
    provider = _provider("biquote-public")
    try:
        symbols = provider.symbols(asset_type=asset_type, live_only=live_only, limit=limit)
    except MarketDataProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"mode": "real-market-data-read-only", "source": provider.name, "count": len(symbols), "symbols": symbols}


@app.get("/market/candles", tags=["real-market-data"])
def market_candles(
    symbol: str = Query(default="EURUSD"),
    timeframe: str = Query(default="1h"),
    limit: int = Query(default=100, ge=2, le=1000),
    source: str = Query(default="biquote-public"),
) -> dict:
    """Fetch actual public market candles and pass them through quality gates."""
    try:
        provider = _provider(source)
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


@app.post("/market/collect", tags=["real-market-data"])
def collect_now(
    symbols: str = Query(default="EURUSD,GBPUSD,USDJPY,XAUUSD,USOIL,US500,BTC/USD,ETH/USD"),
    timeframe: str = Query(default="1h"),
) -> dict:
    selected = [item.strip().upper() for item in symbols.split(",") if item.strip()]
    return collector.collect_once(selected, timeframe=timeframe, limit=100)


@app.get("/market/collection-status", tags=["real-market-data"])
def collection_status() -> dict:
    return {
        "mode": "real-market-data-read-only",
        "automatic_collection": True,
        "last_collection": collector.last_run,
        "cache_dir": str(collector.cache_dir),
        "execution": False,
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
