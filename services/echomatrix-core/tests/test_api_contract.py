from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_simulation_mode() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "echomatrix-core"
    assert response.json()["mode"] == "simulation"


def test_demo_cycle_remains_local_and_traceable() -> None:
    response = TestClient(app).post("/demo/cycle")
    body = response.json()
    assert response.status_code == 200
    assert body["cycle_id"]
    assert body["stages"][-1] == "memory.lesson"
    assert body["proposed_notional"] >= 0
