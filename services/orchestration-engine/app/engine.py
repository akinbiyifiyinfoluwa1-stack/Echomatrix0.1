"""Cross-service decision coordinator for the Ecometrics brain.

This layer coordinates normalized inputs from market data, research, strategy,
AI, risk, and capital allocation. It does not connect to brokers or execute
real-money trades.
"""
from decimal import Decimal

from app.models import DecisionAction, PipelineDecision, PipelineRequest


class OrchestrationEngine:
    """Turn intelligence and risk context into one normalized decision."""

    def __init__(
        self,
        max_position_value: Decimal = Decimal("2500"),
        max_portfolio_exposure: Decimal = Decimal("7000"),
        max_risk_per_trade: Decimal = Decimal("0.01"),
        max_drawdown: Decimal = Decimal("0.05"),
    ) -> None:
        self.max_position_value = max_position_value
        self.max_portfolio_exposure = max_portfolio_exposure
        self.max_risk_per_trade = max_risk_per_trade
        self.max_drawdown = max_drawdown

    def decide(self, request: PipelineRequest) -> PipelineDecision:
        stages = ["market-data", "research", "strategy", "ai-core", "risk"]
        reasons: list[str] = []

        momentum = (request.price - request.previous_price) / request.previous_price
        intelligence_confidence = (
            request.research_confidence + request.ai_confidence
        ) / Decimal("2")

        if request.volume <= 0:
            return self._blocked(request, "market volume is unavailable", stages)

        if request.daily_drawdown >= self.max_drawdown:
            return self._blocked(request, "daily drawdown limit reached", stages)

        # The strategy direction is intentionally conservative: the orchestrator
        # consumes normalized intelligence rather than inventing a new strategy.
        if momentum > 0:
            action = DecisionAction.BUY
            reasons.append("market snapshot shows positive momentum")
        elif momentum < 0:
            action = DecisionAction.SELL
            reasons.append("market snapshot shows negative momentum")
        else:
            return self._blocked(request, "market signal is neutral", stages)

        allowed = min(request.proposed_position_value, self.max_position_value)
        remaining_exposure = max(
            Decimal("0"), self.max_portfolio_exposure - request.current_exposure
        )
        allowed = min(allowed, remaining_exposure)

        stop_fraction = request.stop_distance / request.price
        max_trade_risk = request.portfolio_equity * self.max_risk_per_trade
        if stop_fraction > 0:
            allowed = min(allowed, max_trade_risk / stop_fraction)

        if allowed <= 0:
            return self._blocked(request, "risk limits leave no allocatable capital", stages)

        # Confidence scales capital rather than overriding risk controls.
        confidence_multiplier = max(
            Decimal("0.25"), min(Decimal("1"), intelligence_confidence)
        )
        allocated = allowed * confidence_multiplier
        risk_amount = allocated * stop_fraction

        if intelligence_confidence < Decimal("0.35"):
            action = DecisionAction.HOLD
            reasons.append("combined research and AI confidence is too low")
            allocated = Decimal("0")
            risk_amount = Decimal("0")
        else:
            reasons.append("research and AI confidence support the direction")
            reasons.append("capital was scaled after risk constraints")

        stages.append("capital-allocation")
        stages.append("decision")

        return PipelineDecision(
            symbol=request.symbol,
            action=action,
            confidence=intelligence_confidence,
            proposed_position_value=request.proposed_position_value,
            allowed_position_value=allocated,
            risk_amount=risk_amount,
            portfolio_exposure_after=request.current_exposure + allocated,
            reasons=reasons,
            stages=stages,
        )

    def _blocked(
        self, request: PipelineRequest, reason: str, stages: list[str]
    ) -> PipelineDecision:
        return PipelineDecision(
            symbol=request.symbol,
            action=DecisionAction.BLOCK,
            confidence=Decimal("0"),
            proposed_position_value=request.proposed_position_value,
            allowed_position_value=Decimal("0"),
            risk_amount=Decimal("0"),
            portfolio_exposure_after=request.current_exposure,
            reasons=[reason],
            stages=[*stages, "decision"],
        )
