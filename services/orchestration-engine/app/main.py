"""Ecometrics orchestration API: one decision surface for the financial brain."""
from decimal import Decimal

from fastapi import FastAPI

from app.engine import OrchestrationEngine
from app.models import PipelineRequest, PipelineDecision

app = FastAPI(
    title="Ecometrics Orchestration Engine",
    description="Coordinates market, research, strategy, AI, risk, and allocation into one decision.",
    version="0.1.0",
)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "ecometrics-orchestration-engine",
        "message": "Coordinate the brain before giving it a body.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "orchestration-engine"}


@app.post("/decision", response_model=PipelineDecision, tags=["decision"])
def decision(request: PipelineRequest) -> PipelineDecision:
    return OrchestrationEngine().decide(request)


@app.get("/demo/decision", response_model=PipelineDecision, tags=["demo"])
def demo_decision() -> PipelineDecision:
    request = PipelineRequest(
        symbol="BTC/USD",
        price=Decimal("101000"),
        previous_price=Decimal("100000"),
        volume=Decimal("12.5"),
        portfolio_equity=Decimal("10000"),
        current_exposure=Decimal("3000"),
        proposed_position_value=Decimal("2000"),
        stop_distance=Decimal("2000"),
        daily_drawdown=Decimal("0.01"),
        research_confidence=Decimal("0.80"),
        ai_confidence=Decimal("0.85"),
    )
    return OrchestrationEngine().decide(request)
