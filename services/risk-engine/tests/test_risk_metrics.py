from decimal import Decimal

from app.engine import RiskEngine
from app.models import RiskLimits, RiskRequest, RiskStatus


def _engine() -> RiskEngine:
    return RiskEngine(
        RiskLimits(
            max_position_value=Decimal("2500"),
            max_portfolio_exposure=Decimal("7000"),
            max_risk_per_trade=Decimal("0.01"),
            max_drawdown=Decimal("0.05"),
        )
    )


def test_risk_decision_exposes_utilization_metrics() -> None:
    result = _engine().evaluate(
        RiskRequest(
            portfolio_equity=Decimal("10000"),
            current_exposure=Decimal("3000"),
            proposed_position_value=Decimal("2000"),
            stop_distance=Decimal("2000"),
            entry_price=Decimal("100000"),
            daily_drawdown=Decimal("0.01"),
        )
    )
    assert result.status == RiskStatus.APPROVED
    assert result.risk_utilization == Decimal("0.4")
    assert result.exposure_utilization_after == Decimal("5") / Decimal("7")
    assert result.drawdown_utilization == Decimal("0.2")
    assert result.risk_score == Decimal("5") / Decimal("7")


def test_drawdown_limit_blocks_and_reports_high_risk_score() -> None:
    result = _engine().evaluate(
        RiskRequest(
            portfolio_equity=Decimal("10000"),
            current_exposure=Decimal("3000"),
            proposed_position_value=Decimal("1000"),
            stop_distance=Decimal("1000"),
            entry_price=Decimal("100000"),
            daily_drawdown=Decimal("0.05"),
        )
    )
    assert result.status == RiskStatus.BLOCKED
    assert result.allowed_position_value == Decimal("0")
    assert result.risk_score == Decimal("1")
