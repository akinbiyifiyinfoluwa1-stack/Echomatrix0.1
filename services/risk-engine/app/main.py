"""Risk API for the Ecometrics capital protection layer."""
from decimal import Decimal

from fastapi import FastAPI

from app.engine import RiskEngine
from app.models import RiskLimits, RiskRequest

app = FastAPI(
    title="Ecometrics Risk Engine",
    description="Pre-trade capital, exposure, drawdown, and position-risk evaluation.",
    version="0.1.0",
)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "ecometrics-risk-engine",
        "message": "Protect capital before allocating it.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "risk-engine"}


@app.get("/demo/evaluate", tags=["demo"])
def demo_evaluate() -> dict:
    limits = RiskLimits(
        max_position_value=Decimal("2500"),
        max_portfolio_exposure=Decimal("7000"),
        max_risk_per_trade=Decimal("0.01"),
        max_drawdown=Decimal("0.05"),
    )
    request = RiskRequest(
        portfolio_equity=Decimal("10000"),
        current_exposure=Decimal("3000"),
        proposed_position_value=Decimal("2000"),
        stop_distance=Decimal("2000"),
        entry_price=Decimal("100000"),
        daily_drawdown=Decimal("0.01"),
    )
    decision = RiskEngine(limits).evaluate(request)
    return decision.model_dump(mode="json")
