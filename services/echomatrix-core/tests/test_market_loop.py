from app.main import health, root


def test_core_advertises_market_data_connection() -> None:
    body = root()
    assert body["market_data"] == "connected"
    assert body["pipeline"] == "connected"


def test_core_health_remains_simulation_only() -> None:
    body = health()
    assert body["mode"] == "simulation"
    assert body["service"] == "echomatrix-core"
