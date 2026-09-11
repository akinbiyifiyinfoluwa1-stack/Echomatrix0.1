"""Provider-neutral research engine.

This first version does not invent research results. It accepts supplied source
material and normalizes it into a form the AI Core and memory layer can consume.
A web/news provider can be plugged in later behind this contract.
"""
from datetime import datetime, timezone

from app.models import ResearchFinding, ResearchRequest, ResearchSource


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
