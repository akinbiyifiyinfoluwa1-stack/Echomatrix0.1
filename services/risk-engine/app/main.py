"""Risk API for the EchoMatrix capital protection layer."""
from decimal import Decimal

from fastapi import FastAPI

from app.engine import RiskEngine
from app.models import RiskLimits, RiskRequest

app = FastAPI(
    title="EchoMatrix Risk Engine",
    description="Pre-trade capital, exposure, drawdown, and position-risk evaluation.",
    version="0.1.0",
)


def _evaluate(request: RiskRequest):
    limits = RiskLimits(
        max_position_value=Decimal("2500"),
        max_portfolio_exposure=Decimal("7000"),
        max_risk_per_trade=Decimal("0.01"),
        max_drawdown=Decimal("0.05"),
    )
    return RiskEngine(limits).evaluate(request)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "echomatrix-risk-engine",
        "message": "Protect capital before allocating it.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "risk-engine"}


@app.post("/evaluate", tags=["risk"])
def evaluate(request: RiskRequest) -> dict:
    return _evaluate(request).model_dump(mode="json")


@app.get("/demo/evaluate", tags=["demo"])
def demo_evaluate() -> dict:
    request = RiskRequest(
        portfolio_equity=Decimal("10000"),
        current_exposure=Decimal("3000"),
        proposed_position_value=Decimal("2000"),
        stop_distance=Decimal("2000"),
        entry_price=Decimal("100000"),
        daily_drawdown=Decimal("0.01"),
    )
    return _evaluate(request).model_dump(mode="json")
