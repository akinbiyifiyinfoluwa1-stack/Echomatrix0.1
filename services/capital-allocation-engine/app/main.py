"""Capital allocation API for the Ecometrics capital brain."""
from decimal import Decimal

from fastapi import FastAPI

from app.engine import CapitalAllocationEngine
from app.models import AllocationRequest

app = FastAPI(
    title="Ecometrics Capital Allocation Engine",
    description="Converts risk-approved opportunities into bounded capital allocations.",
    version="0.1.0",
)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "ecometrics-capital-allocation-engine",
        "message": "Decide how much capital belongs in an approved opportunity.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "capital-allocation-engine"}


@app.get("/demo/allocation", tags=["demo"])
def demo_allocation() -> dict:
    request = AllocationRequest(
        available_capital=Decimal("10000"),
        proposed_position_value=Decimal("2000"),
        allowed_position_value=Decimal("1500"),
        confidence=Decimal("0.8"),
        current_exposure=Decimal("3000"),
        max_portfolio_exposure=Decimal("5000"),
        allocation_floor=Decimal("0.25"),
        allocation_ceiling=Decimal("0.75"),
    )
    decision = CapitalAllocationEngine().allocate(request)
    return decision.model_dump(mode="json")


@app.post("/allocate", tags=["allocation"])
def allocate(request: AllocationRequest) -> dict:
    decision = CapitalAllocationEngine().allocate(request)
    return decision.model_dump(mode="json")
