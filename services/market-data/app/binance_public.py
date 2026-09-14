"""Read-only Binance public market-data adapter.

This adapter uses public market endpoints only. It has no API-key input and no
order/execution capability. It exists so EchoMatrix can consume actual market
observations instead of synthetic candles.
"""
from __future__ import annotations

import json
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .providers import MarketCandle, MarketDataProviderError


class BinancePublicProvider:
    name = "binance-public"
    base_url = "https://api.binance.com/api/v3/klines"

    def fetch_candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[MarketCandle]:
        params = urlencode({"symbol": symbol.upper().replace("/", ""), "interval": timeframe, "limit": min(limit, 1000)})
        request = Request(f"{self.base_url}?{params}", headers={"User-Agent": "EchoMatrix/1.0"})
        try:
            with urlopen(request, timeout=15) as response:
                payload = json.load(response)
        except Exception as exc:  # pragma: no cover - network failures are environment dependent
            raise MarketDataProviderError(f"Binance market data unavailable: {exc}") from exc

        candles: list[MarketCandle] = []
        for row in payload:
            if len(row) < 6:
                raise MarketDataProviderError("Binance returned a malformed candle")
            candles.append(
                MarketCandle(
                    timestamp=int(row[0]),
                    symbol=symbol.upper(),
                    timeframe=timeframe,
                    open=Decimal(str(row[1])),
                    high=Decimal(str(row[2])),
                    low=Decimal(str(row[3])),
                    close=Decimal(str(row[4])),
                    volume=Decimal(str(row[5])),
                    source=self.name,
                )
            )
        return candles
