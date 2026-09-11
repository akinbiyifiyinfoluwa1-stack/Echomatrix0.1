"""Deterministic capital allocation engine. It never executes trades."""
from decimal import Decimal

from app.models import AllocationAction, AllocationDecision, AllocationRequest


class CapitalAllocationEngine:
    """Convert a risk-approved opportunity into a bounded capital allocation."""

    def allocate(self, request: AllocationRequest) -> AllocationDecision:
        reasons: list[str] = []

        if request.allowed_position_value <= 0:
            return AllocationDecision(
                action=AllocationAction.HOLD,
                allocated_capital=Decimal("0"),
                allocation_ratio=Decimal("0"),
                projected_exposure=request.current_exposure,
                rationale=["risk engine did not approve any position value"],
            )

        remaining_exposure = max(
            Decimal("0"), request.max_portfolio_exposure - request.current_exposure
        )
        risk_cap = min(request.allowed_position_value, remaining_exposure)
        confidence_ratio = request.allocation_floor + (
            request.allocation_ceiling - request.allocation_floor
        ) * request.confidence

        capital_cap = request.available_capital * confidence_ratio
        allocated = min(risk_cap, request.proposed_position_value, capital_cap)

        if allocated <= 0:
            return AllocationDecision(
                action=AllocationAction.HOLD,
                allocated_capital=Decimal("0"),
                allocation_ratio=Decimal("0"),
                projected_exposure=request.current_exposure,
                rationale=["no capital remains after allocation constraints"],
            )

        if allocated < request.proposed_position_value:
            reasons.append("allocation was reduced by capital, confidence, or exposure limits")
        else:
            reasons.append("requested opportunity fits allocation constraints")

        ratio = allocated / request.available_capital
        return AllocationDecision(
            action=AllocationAction.ALLOCATE,
            allocated_capital=allocated,
            allocation_ratio=ratio,
            projected_exposure=request.current_exposure + allocated,
            rationale=reasons,
        )
