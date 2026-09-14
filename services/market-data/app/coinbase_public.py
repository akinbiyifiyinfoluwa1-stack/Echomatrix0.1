"""Read-only Coinbase public candle provider.

No account, API key, wallet, or order capability is present here.
"""
from __future__ import annotations

import json
from decimal import Decimal
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.providers import MarketCandle, MarketDataProviderError


class CoinbasePublicProvider:
    name = "coinbase-public"
    base_url = "https://api.exchange.coinbase.com/products/{product}/candles"

    _granularity = {
        "1m": 60,
        "5m": 300,
        "15m": 900,
        "1h": 3600,
        "6h": 21600,
        "1d": 86400,
    }

    def fetch_candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[MarketCandle]:
        product = symbol.upper().replace("/", "-")
        if timeframe not in self._granularity:
            raise MarketDataProviderError(f"Coinbase does not support timeframe {timeframe!r}")
        limit = max(2, min(limit, 300))
        url = self.base_url.format(product=quote(product, safe=""))
        request = Request(url, headers={"User-Agent": "EchoMatrix/1.0"})
        try:
            with urlopen(request, timeout=15) as response:
                rows = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise MarketDataProviderError(f"Coinbase public request failed: {exc}") from exc

        if not isinstance(rows, list):
            raise MarketDataProviderError("Coinbase returned malformed candle data")
        candles: list[MarketCandle] = []
        for row in rows[-limit:]:
            if not isinstance(row, list) or len(row) < 6:
                raise MarketDataProviderError("Coinbase returned malformed candle row")
            timestamp, low, high, open_, close, volume = row[:6]
            candles.append(
                MarketCandle(
                    timestamp=int(timestamp) * 1000,
                    symbol=symbol.upper(),
                    timeframe=timeframe,
                    open=Decimal(str(open_)),
                    high=Decimal(str(high)),
                    low=Decimal(str(low)),
                    close=Decimal(str(close)),
                    volume=Decimal(str(volume)),
                    source=self.name,
                )
            )
        return candles
