"""Provider-neutral research engine.

This layer separates observed evidence from interpretation. The market-context
path is deterministic and explicitly marks synthetic/demo observations instead
of pretending they are live external research.
"""
from datetime import datetime, timezone
from decimal import Decimal

from app.models import (
    MarketResearchContext,
    MarketResearchRequest,
    ResearchFinding,
    ResearchRequest,
    ResearchSource,
)


class ResearchEngine:
    def build_finding(
        self,
        request: ResearchRequest,
        summary: str,
        key_points: list[str],
        sources: list[ResearchSource],
        confidence: float = 0.5,
    ) -> ResearchFinding:
        return ResearchFinding(
            query=request.query,
            research_type=request.research_type,
            summary=summary,
            key_points=key_points,
            sources=sources[: request.max_sources],
            confidence=confidence,
            generated_at=datetime.now(timezone.utc),
        )

    def research_prompt(self, request: ResearchRequest) -> str:
        context = f" for {request.symbol}" if request.symbol else ""
        return (
            "Research the following topic%s: %s. "
            "Separate verified facts from interpretation, identify uncertainty, "
            "and return concise evidence-backed findings with source references."
            % (context, request.query)
        )

    def market_context(self, request: MarketResearchRequest) -> MarketResearchContext:
        change = (request.price - request.previous_price) / request.previous_price
        if change > 0:
            direction = "up"
            direction_text = "price increased versus the previous observation"
        elif change < 0:
            direction = "down"
            direction_text = "price decreased versus the previous observation"
        else:
            direction = "flat"
            direction_text = "price is unchanged versus the previous observation"

        if request.volume > 0:
            liquidity = "volume is present for this observation"
            quality = "bounded_observation"
            confidence = Decimal("0.70")
        else:
            liquidity = "volume is unavailable or zero"
            quality = "price_only_observation"
            confidence = Decimal("0.45")

        summary = (
            f"{request.symbol}: {direction_text}. "
            f"Observed price={request.price}, previous price={request.previous_price}, "
            f"volume={request.volume}. Source={request.source}."
        )
        finding = self.build_finding(
            ResearchRequest(
                query=f"Market context for {request.symbol}",
                research_type="market",
                symbol=request.symbol,
                max_sources=5,
            ),
            summary=summary,
            key_points=[
                f"direction={direction}",
                f"price_change={change}",
                liquidity,
                "No external news or web claims are included in this deterministic context.",
            ],
            sources=[],
            confidence=float(confidence),
        )
        return MarketResearchContext(
            symbol=request.symbol,
            source=request.source,
            price=request.price,
            previous_price=request.previous_price,
            volume=request.volume,
            price_change=change,
            direction=direction,
            liquidity_observation=liquidity,
            evidence_quality=quality,
            confidence=confidence,
            research=finding,
            generated_at=datetime.now(timezone.utc),
        )
