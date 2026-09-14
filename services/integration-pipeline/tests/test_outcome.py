from decimal import Decimal

from app.outcome import evaluate_outcome


def test_long_position_marks_profit():
    result = evaluate_outcome(
        action="buy",
        entry_price=Decimal("100"),
        mark_price=Decimal("110"),
        quantity=Decimal("2"),
        entry_fee=Decimal("0.20"),
        exit_fee_rate=Decimal("0.001"),
        risk_amount=Decimal("5"),
    )
    assert result["gross_pnl"] == Decimal("20.00")
    assert result["net_pnl"] == Decimal("19.58")
    assert result["profitable"] is True
    assert result["risk_multiple"] > Decimal("3")


def test_short_position_marks_profit_when_price_falls():
    result = evaluate_outcome(
        action="sell",
        entry_price=Decimal("100"),
        mark_price=Decimal("90"),
        quantity=Decimal("2"),
        risk_amount=Decimal("10"),
    )
    assert result["gross_pnl"] == Decimal("20.00")
    assert result["net_pnl"] == Decimal("20.00")


def test_loss_is_negative():
    result = evaluate_outcome(
        action="buy",
        entry_price=Decimal("100"),
        mark_price=Decimal("95"),
        quantity=Decimal("1"),
    )
    assert result["net_pnl"] == Decimal("-5.00")
    assert result["profitable"] is False
