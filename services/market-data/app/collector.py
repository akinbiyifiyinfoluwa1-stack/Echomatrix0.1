"""Automatic read-only market observation collector.

The collector periodically downloads public market observations and stores a
small append-only JSONL cache for downstream research. It never executes,
connects to accounts, or places orders.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Callable

from app.normalizer import normalize_candles
from app.providers import MarketDataProvider, MarketDataProviderError


class MarketCollector:
    def __init__(self, providers: dict[str, MarketDataProvider], cache_dir: str | None = None) -> None:
        self.providers = providers
        self.cache_dir = Path(cache_dir or os.getenv("MARKET_CACHE_DIR", "/tmp/echomatrix-market-cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self.last_run: dict | None = None

    def collect_once(self, symbols: list[str], timeframe: str = "1m", limit: int = 100) -> dict:
        results: list[dict] = []
        for symbol in symbols:
            collected = False
            errors: list[str] = []
            for provider_name, provider in self.providers.items():
                try:
                    candles = normalize_candles(provider.fetch_candles(symbol, timeframe, limit))
                    if not candles:
                        continue
                    path = self.cache_dir / f"{symbol.replace('/', '_')}_{timeframe}.jsonl"
                    with self._lock, path.open("a", encoding="utf-8") as handle:
                        for candle in candles[-min(10, len(candles)) :]:
                            handle.write(json.dumps({
                                "timestamp": candle.timestamp,
                                "symbol": candle.symbol,
                                "timeframe": candle.timeframe,
                                "open": str(candle.open),
                                "high": str(candle.high),
                                "low": str(candle.low),
                                "close": str(candle.close),
                                "volume": str(candle.volume),
                                "source": candle.source,
                            }) + "\n")
                    results.append({"symbol": symbol, "provider": provider_name, "count": len(candles), "status": "ok"})
                    collected = True
                    break
                except (MarketDataProviderError, ValueError, OSError) as exc:
                    errors.append(f"{provider_name}: {exc}")
            if not collected:
                results.append({"symbol": symbol, "status": "error", "errors": errors})

        summary = {"mode": "real-market-data-read-only", "status": "ok", "results": results, "timestamp": int(time.time())}
        self.last_run = summary
        return summary

    def start(self, symbols: list[str], timeframe: str = "1m", interval_seconds: int = 60, limit: int = 100, on_error: Callable[[Exception], None] | None = None) -> None:
        if self._thread and self._thread.is_alive():
            return

        def worker() -> None:
            while not self._stop.is_set():
                try:
                    self.collect_once(symbols, timeframe, limit)
                except Exception as exc:  # collector must not crash the API service
                    if on_error:
                        on_error(exc)
                self._stop.wait(max(15, interval_seconds))

        self._stop.clear()
        self._thread = threading.Thread(target=worker, name="echomatrix-market-collector", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
