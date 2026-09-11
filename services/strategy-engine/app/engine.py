"""Deterministic baseline strategy engine. AI strategies can plug into this contract later."""
from decimal import Decimal

from app.models import MarketSnapshot, Signal, StrategyConfig, TradeProposal


class StrategyEngine:
    """Convert market snapshots into normalized trade proposals."""

    def __init__(self, config: StrategyConfig) -> None:
        self.config = config

    def evaluate(self, snapshot: MarketSnapshot) -> TradeProposal:
        change = (snapshot.price - snapshot.previous_price) / snapshot.previous_price
        rationale: list[str] = []

        if snapshot.volume < self.config.minimum_volume:
            return TradeProposal(
                strategy=self.config.name,
                symbol=snapshot.symbol,
                signal=Signal.HOLD,
                confidence=Decimal("0"),
                reference_price=snapshot.price,
                rationale=["volume is below the strategy minimum"],
                timestamp=snapshot.timestamp,
            )

        if change >= self.config.momentum_threshold:
            signal = Signal.BUY
            confidence = min(Decimal("1"), change / (self.config.momentum_threshold * 2))
            rationale.append("positive momentum exceeded the configured threshold")
        elif change <= -self.config.momentum_threshold:
            signal = Signal.SELL
            confidence = min(Decimal("1"), abs(change) / (self.config.momentum_threshold * 2))
            rationale.append("negative momentum exceeded the configured threshold")
        else:
            signal = Signal.HOLD
            confidence = Decimal("0")
            rationale.append("price movement is inside the neutral zone")

        return TradeProposal(
            strategy=self.config.name,
            symbol=snapshot.symbol,
            signal=signal,
            confidence=confidence,
            reference_price=snapshot.price,
            rationale=rationale,
            timestamp=snapshot.timestamp,
        )
