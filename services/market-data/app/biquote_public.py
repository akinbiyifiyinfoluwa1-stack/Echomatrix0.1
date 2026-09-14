"""Read-only Biquote market-data adapter for broad multi-asset coverage."""
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.providers import MarketCandle, MarketDataProviderError


class BiquotePublicProvider:
    """Public read-only feed covering forex, stocks, crypto, indices and commodities."""

    name = "biquote-public"
    base_url = "https://biquote.io"

    def _get_json(self, path: str, params: dict[str, str] | None = None):
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "EchoMatrix/1.0"})
        try:
            with urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise MarketDataProviderError(f"Biquote request failed: {exc}") from exc

    def fetch_candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[MarketCandle]:
        interval = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1h", "4h": "4h", "1d": "1d"}.get(timeframe)
        if interval is None:
            raise MarketDataProviderError(f"Unsupported Biquote timeframe: {timeframe}")
        payload = self._get_json(f"/api/{symbol.replace('/', '')}/ohlc", {"interval": interval, "limit": str(min(limit, 1000))})
        bars = payload.get("bars", [])
        if not isinstance(bars, list):
            raise MarketDataProviderError("Biquote returned an invalid OHLC response")
        candles: list[MarketCandle] = []
        for bar in reversed(bars):
            try:
                timestamp = int(__import__("datetime").datetime.fromisoformat(bar["openTime"].replace("Z", "+00:00")).timestamp() * 1000)
                candles.append(
                    MarketCandle(
                        timestamp=timestamp,
                        symbol=symbol.upper(),
                        timeframe=timeframe,
                        open=Decimal(str(bar["open"])),
                        high=Decimal(str(bar["high"])),
                        low=Decimal(str(bar["low"])),
                        close=Decimal(str(bar["close"])),
                        volume=Decimal(str(bar.get("tickVolume", bar.get("volume", 0)))),
                        source=self.name,
                    )
                )
            except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
                raise MarketDataProviderError(f"Malformed Biquote OHLC bar: {exc}") from exc
        return candles

    def latest(self, symbol: str) -> dict:
        payload = self._get_json(f"/api/{symbol.replace('/', '')}")
        return payload

    def symbols(self, *, asset_type: str | None = None, live_only: bool = False, limit: int = 2000) -> list[dict]:
        params = {"liveOnly": "true" if live_only else "false"}
        if asset_type:
            params["type"] = asset_type
        payload = self._get_json("/api/symbols", params)
        if not isinstance(payload, list):
            raise MarketDataProviderError("Biquote returned an invalid symbol catalogue")
        return payload[:limit]
