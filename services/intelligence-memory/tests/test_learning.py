from decimal import Decimal

from app.main import _learning_adjustment
from app.models import LearningRequest


def test_learning_reduces_risk_after_negative_high_risk_result() -> None:
    request = LearningRequest(
        symbol="BTC/USD",
        action="buy",
        strategy="deterministic-ensemble-v1",
        simulated_return=Decimal("-0.03"),
        risk_score=Decimal("0.80"),
        confidence=Decimal("0.60"),
    )
    assert _learning_adjustment(request) == "reduce-risk-and-require-more-confirmation"


def test_learning_retains_low_risk_positive_result() -> None:
    request = LearningRequest(
        symbol="BTC/USD",
        action="buy",
        strategy="deterministic-ensemble-v1",
        simulated_return=Decimal("0.02"),
        risk_score=Decimal("0.20"),
        confidence=Decimal("0.80"),
    )
    assert _learning_adjustment(request) == "retain-context"
