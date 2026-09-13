from decimal import Decimal

from app.engine import EchoMatrixCore
from app.models import CycleRequest


def test_strong_positive_move_produces_bounded_simulated_buy() -> None:
    result = EchoMatrixCore().run_cycle(
        CycleRequest(price=Decimal("102000"), previous_price=Decimal("100000"))
    )
    assert result.action == "BUY"
    assert result.risk_approved is True
    assert result.proposed_notional == Decimal("2500")
    assert result.simulated_exposure == Decimal("0.25")
    assert result.stages[-1] == "memory.lesson"


def test_small_move_holds_capital() -> None:
    result = EchoMatrixCore().run_cycle(
        CycleRequest(price=Decimal("100200"), previous_price=Decimal("100000"))
    )
    assert result.action == "HOLD"
    assert result.proposed_notional == Decimal("0")


def test_every_cycle_has_traceable_id() -> None:
    result = EchoMatrixCore().run_cycle(
        CycleRequest(price=Decimal("99000"), previous_price=Decimal("100000"))
    )
    assert result.cycle_id
    assert result.symbol == "BTC/USD"
