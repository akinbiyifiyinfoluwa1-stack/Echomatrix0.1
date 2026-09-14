from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app, provider
from app.providers import MarketCandle


def test_health_declares_real_read_only_mode():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "real-market-data-read-only"
    assert response.json()["execution"] is False


def test_real_candles_are_normalized(monkeypatch):
    def fake_fetch(symbol: str, timeframe: str, limit: int = 200):
        return [
            MarketCandle(2, symbol, timeframe, Decimal("101"), Decimal("103"), Decimal("100"), Decimal("102"), Decimal("12"), "test"),
            MarketCandle(1, symbol, timeframe, Decimal("99"), Decimal("101"), Decimal("98"), Decimal("100"), Decimal("10"), "test"),
        ]

    monkeypatch.setattr(provider, "fetch_candles", fake_fetch)
    response = TestClient(app).get("/market/candles", params={"symbol": "BTC/USD", "timeframe": "1m", "limit": 2})
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "real-market-data-read-only"
    assert [row["timestamp"] for row in body["candles"]] == [1, 2]
