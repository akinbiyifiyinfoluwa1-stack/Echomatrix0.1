"""The first self-contained EchoMatrix intelligence loop.

This runtime deliberately stops at simulation. It can make and trace decisions,
but it never connects to a broker, exchange, wallet, or payment system.
"""
from decimal import Decimal, ROUND_DOWN
from uuid import uuid4

from app.models import CycleRequest, CycleResult


class EchoMatrixCore:
    def run_cycle(self, request: CycleRequest) -> CycleResult:
        stages = ["market.observed"]
        price_change = (request.price - request.previous_price) / request.previous_price
        stages.append("research.synthesized")

        # Deterministic baseline intelligence: direction comes from price change;
        # confidence increases with the magnitude of the observed move but is capped.
        magnitude = min(abs(price_change) * Decimal("10"), Decimal("1"))
        confidence = (Decimal("0.50") + magnitude * Decimal("0.40")).quantize(
            Decimal("0.0001"), rounding=ROUND_DOWN
        )
        action = "HOLD"
        if price_change > Decimal("0.005"):
            action = "BUY"
        elif price_change < Decimal("-0.005"):
            action = "SELL"
        stages.append("strategy.generated")
        stages.append("ai.baseline")

        risk_approved = confidence >= request.confidence_threshold
        stages.append("risk.evaluated")

        max_notional = request.simulated_cash * request.max_exposure
        proposed_notional = max_notional if risk_approved and action != "HOLD" else Decimal("0")
        simulated_exposure = proposed_notional / request.simulated_cash
        stages.append("allocation.bounded")
        stages.append("simulation.decision")

        if action == "HOLD":
            lesson = "No sufficiently strong directional evidence; preserve simulated capital."
        elif not risk_approved:
            lesson = "Signal direction was detected, but confidence did not clear the risk threshold."
        else:
            lesson = "A bounded simulated decision was produced and recorded without external execution."
        stages.append("memory.lesson")

        return CycleResult(
            cycle_id=str(uuid4()),
            symbol=request.symbol,
            action=action,
            confidence=confidence,
            price_change=price_change,
            proposed_notional=proposed_notional,
            risk_approved=risk_approved,
            simulated_cash=request.simulated_cash,
            simulated_exposure=simulated_exposure,
            stages=stages,
            lesson=lesson,
        )
