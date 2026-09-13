"""Deterministic strategy engine with a small explainable ensemble."""
from decimal import Decimal

from app.models import (
    MarketSnapshot,
    Signal,
    StrategyComponent,
    StrategyConfig,
    StrategyEnsembleResult,
    TradeProposal,
)


class StrategyEngine:
    """Convert market snapshots into normalized, non-executing proposals."""

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

    def ensemble(self, snapshot: MarketSnapshot) -> StrategyEnsembleResult:
        change = (snapshot.price - snapshot.previous_price) / snapshot.previous_price
        momentum = self.evaluate(snapshot)

        if snapshot.volume >= self.config.minimum_volume:
            volume_signal = momentum.signal if momentum.signal != Signal.HOLD else Signal.HOLD
            volume_score = Decimal("0.20") if volume_signal != Signal.HOLD else Decimal("0")
            volume_confidence = Decimal("1")
            volume_reason = "volume clears the configured confirmation floor"
        else:
            volume_signal = Signal.HOLD
            volume_score = Decimal("0")
            volume_confidence = Decimal("0")
            volume_reason = "volume does not clear the configured confirmation floor"

        trend_score = max(Decimal("-1"), min(Decimal("1"), change / self.config.momentum_threshold))
        trend_signal = Signal.BUY if trend_score > 0 else Signal.SELL if trend_score < 0 else Signal.HOLD
        trend_confidence = min(Decimal("1"), abs(trend_score))
        trend_reason = "directional price change is positive" if trend_score > 0 else (
            "directional price change is negative" if trend_score < 0 else "no directional price change"
        )

        momentum_score = (
            momentum.confidence if momentum.signal == Signal.BUY else
            -momentum.confidence if momentum.signal == Signal.SELL else Decimal("0")
        )
        composite = (momentum_score * Decimal("0.60")) + (trend_score * Decimal("0.25")) + (volume_score * Decimal("0.15"))
        composite = max(Decimal("-1"), min(Decimal("1"), composite))

        if composite >= Decimal("0.20"):
            signal = Signal.BUY
        elif composite <= Decimal("-0.20"):
            signal = Signal.SELL
        else:
            signal = Signal.HOLD

        confidence = min(Decimal("1"), abs(composite))
        regime = "bullish-momentum" if composite >= Decimal("0.20") else (
            "bearish-momentum" if composite <= Decimal("-0.20") else "neutral"
        )
        components = [
            StrategyComponent(
                name="momentum",
                signal=momentum.signal,
                score=momentum_score,
                confidence=momentum.confidence,
                rationale=momentum.rationale[0],
            ),
            StrategyComponent(
                name="trend",
                signal=trend_signal,
                score=trend_score,
                confidence=trend_confidence,
                rationale=trend_reason,
            ),
            StrategyComponent(
                name="volume-confirmation",
                signal=volume_signal,
                score=volume_score,
                confidence=volume_confidence,
                rationale=volume_reason,
            ),
        ]
        proposal = TradeProposal(
            strategy="deterministic-ensemble-v1",
            symbol=snapshot.symbol,
            signal=signal,
            confidence=confidence,
            reference_price=snapshot.price,
            rationale=[
                f"ensemble regime={regime}",
                f"composite score={composite}",
                "This is an analytical proposal only; no execution occurs in the strategy service.",
            ],
            timestamp=snapshot.timestamp,
        )
        return StrategyEnsembleResult(
            symbol=snapshot.symbol,
            signal=signal,
            confidence=confidence,
            composite_score=composite,
            regime=regime,
            components=components,
            proposal=proposal,
            timestamp=snapshot.timestamp,
        )
