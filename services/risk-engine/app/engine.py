"""Deterministic pre-trade risk evaluation. No broker connectivity."""
from decimal import Decimal

from app.models import RiskDecision, RiskLimits, RiskRequest, RiskStatus


class RiskEngine:
    """Evaluate proposed capital exposure against portfolio risk limits."""

    def __init__(self, limits: RiskLimits) -> None:
        self.limits = limits

    def _metrics(self, request: RiskRequest, allowed: Decimal, implied_risk: Decimal) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        max_trade_risk = request.portfolio_equity * self.limits.max_risk_per_trade
        exposure_after = request.current_exposure + allowed
        risk_utilization = implied_risk / max_trade_risk if max_trade_risk > 0 else Decimal("1")
        exposure_utilization = exposure_after / self.limits.max_portfolio_exposure
        drawdown_utilization = request.daily_drawdown / self.limits.max_drawdown
        risk_score = max(
            Decimal("0"),
            min(
                Decimal("1"),
                max(risk_utilization, exposure_utilization, drawdown_utilization),
            ),
        )
        return risk_utilization, exposure_utilization, drawdown_utilization, risk_score

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
            metrics = self._metrics(request, Decimal("0"), Decimal("0"))
            return RiskDecision(
                status=RiskStatus.BLOCKED,
                allowed_position_value=Decimal("0"),
                risk_amount=Decimal("0"),
                portfolio_exposure_after=request.current_exposure,
                reasons=["daily drawdown limit reached", *reasons],
                risk_utilization=metrics[0],
                exposure_utilization_after=metrics[1],
                drawdown_utilization=metrics[2],
                risk_score=metrics[3],
            )

        if allowed <= 0:
            metrics = self._metrics(request, Decimal("0"), Decimal("0"))
            return RiskDecision(
                status=RiskStatus.BLOCKED,
                allowed_position_value=Decimal("0"),
                risk_amount=Decimal("0"),
                portfolio_exposure_after=request.current_exposure,
                reasons=reasons or ["no capital remains within risk limits"],
                risk_utilization=metrics[0],
                exposure_utilization_after=metrics[1],
                drawdown_utilization=metrics[2],
                risk_score=metrics[3],
            )

        final_risk = allowed * stop_fraction
        status = RiskStatus.APPROVED if allowed == proposed else RiskStatus.REDUCED
        if status == RiskStatus.APPROVED:
            reasons.append("position is within configured risk limits")

        metrics = self._metrics(request, allowed, final_risk)
        return RiskDecision(
            status=status,
            allowed_position_value=allowed,
            risk_amount=final_risk,
            portfolio_exposure_after=request.current_exposure + allowed,
            reasons=reasons,
            risk_utilization=metrics[0],
            exposure_utilization_after=metrics[1],
            drawdown_utilization=metrics[2],
            risk_score=metrics[3],
        )
