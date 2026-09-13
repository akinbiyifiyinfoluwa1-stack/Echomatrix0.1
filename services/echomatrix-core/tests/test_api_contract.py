from app.main import demo_cycle, health


def test_health_reports_simulation_mode() -> None:
    body = health()
    assert body["service"] == "echomatrix-core"
    assert body["mode"] == "simulation"


def test_demo_cycle_remains_local_and_traceable() -> None:
    body = demo_cycle()
    assert body["cycle_id"]
    assert body["stages"][-1] == "memory.lesson"
    assert body["proposed_notional"] >= 0
