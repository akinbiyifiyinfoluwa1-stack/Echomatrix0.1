"""Deterministic pre-trade risk evaluation. No broker connectivity."""
from decimal import Decimal

from app.models import RiskDecision, RiskLimits, RiskRequest, RiskStatus


class RiskEngine:
    """Evaluate proposed capital exposure against portfolio risk limits."""

    def __init__(self, limits: RiskLimits) -> None:
        self.limits = limits

    def evaluate(self, request: RiskRequest) -> RiskDecision:
        reasons: list[str] = []
        proposed = request.proposed_position_value
        max_trade_risk = request.portfolio_equity * self.limits.max_risk_per_trade
        stop_fraction = request.stop_distance / request.entry_price
        implied_risk = proposed * stop_fraction

        allowed = proposed

        if proposed > self.limits.max_position_value:
            allowed = min(allowed, self.limits.max_position_value)
            reasons.append("proposed position exceeds max position value")

        remaining_exposure = max(
            Decimal("0"), self.limits.max_portfolio_exposure - request.current_exposure
        )
        if proposed > remaining_exposure:
            allowed = min(allowed, remaining_exposure)
            reasons.append("proposed position exceeds remaining portfolio exposure")

        if implied_risk > max_trade_risk and stop_fraction > 0:
            risk_limited_value = max_trade_risk / stop_fraction
            allowed = min(allowed, risk_limited_value)
            reasons.append("proposed position exceeds max risk per trade")

        if request.daily_drawdown >= self.limits.max_drawdown:
            return RiskDecision(
                status=RiskStatus.BLOCKED,
                allowed_position_value=Decimal("0"),
                risk_amount=Decimal("0"),
                portfolio_exposure_after=request.current_exposure,
                reasons=["daily drawdown limit reached", *reasons],
            )

        if allowed <= 0:
            return RiskDecision(
                status=RiskStatus.BLOCKED,
                allowed_position_value=Decimal("0"),
                risk_amount=Decimal("0"),
                portfolio_exposure_after=request.current_exposure,
                reasons=reasons or ["no capital remains within risk limits"],
            )

        final_risk = allowed * stop_fraction
        status = RiskStatus.APPROVED if allowed == proposed else RiskStatus.REDUCED
        if status == RiskStatus.APPROVED:
            reasons.append("position is within configured risk limits")

        return RiskDecision(
            status=status,
            allowed_position_value=allowed,
            risk_amount=final_risk,
            portfolio_exposure_after=request.current_exposure + allowed,
            reasons=reasons,
        )
