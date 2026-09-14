from decimal import Decimal

import pytest

from app.normalizer import normalize_candles
from app.providers import MarketCandle, MarketDataProviderError


def candle(ts: int, close: str = "100") -> MarketCandle:
    return MarketCandle(ts, "BTC/USD", "1m", Decimal("99"), Decimal("101"), Decimal("98"), Decimal(close), Decimal("10"), "test")


def test_normalizer_orders_candles():
    result = normalize_candles([candle(2), candle(1)])
    assert [item.timestamp for item in result] == [1, 2]


def test_normalizer_rejects_duplicate_timestamps():
    with pytest.raises(MarketDataProviderError):
        normalize_candles([candle(1), candle(1)])


def test_normalizer_rejects_invalid_ohlc():
    bad = MarketCandle(1, "BTC/USD", "1m", Decimal("99"), Decimal("98"), Decimal("97"), Decimal("100"), Decimal("10"), "test")
    with pytest.raises(MarketDataProviderError):
        normalize_candles([bad])
