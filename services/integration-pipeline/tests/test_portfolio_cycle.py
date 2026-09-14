from decimal import Decimal

from app.portfolio_cycle import PortfolioSimulator, replay_prices


def test_multi_cycle_preserves_state():
    sim = PortfolioSimulator(Decimal("10000"), Decimal("0.001"))
    first = sim.record_cycle(Decimal("100"), "hold", Decimal("0"))
    second = sim.record_cycle(Decimal("110"), "buy", Decimal("1000"))
    third = sim.snapshot(Decimal("120"))

    assert first["portfolio"]["equity"] == Decimal("10000.00")
    assert second["trade"]["opened"] is True
    assert third["equity"] > Decimal("10000")
    assert third["total_fees"] == Decimal("1.00")


def test_replay_returns_full_curve_and_summary():
    result = replay_prices(
        [Decimal("100"), Decimal("101"), Decimal("102"), Decimal("100")],
        Decimal("10000"),
    )
    assert result["mode"] == "simulation-only"
    assert len(result["cycles"]) == 4
    assert result["summary"]["cycles"] == 4
    assert "drawdown" in result["summary"]
