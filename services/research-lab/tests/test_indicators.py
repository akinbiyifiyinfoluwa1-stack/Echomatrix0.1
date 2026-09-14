from decimal import Decimal
from app.indicators import returns, sma, ema, max_drawdown

def test_returns_and_moving_averages():
    values = [Decimal("10"), Decimal("12"), Decimal("14"), Decimal("16"), Decimal("18")]
    assert returns(values)[1] == Decimal("0.2")
    assert sma(values, 3)[-1] == Decimal("16")
    assert ema(values, 3)[-1] is not None

def test_drawdown():
    values = [Decimal("100"), Decimal("110"), Decimal("99"), Decimal("120")]
    assert max_drawdown(values) == Decimal("0.1")
