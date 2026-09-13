"""Research Intelligence API."""
from fastapi import FastAPI

from app.engine import ResearchEngine
from app.models import (
    MarketResearchContext,
    MarketResearchRequest,
    ResearchFinding,
    ResearchRequest,
)

app = FastAPI(
    title="EchoMatrix Research Intelligence",
    description="Structured research layer feeding Strategy, AI Core, and intelligence memory.",
    version="0.2.0",
)

engine = ResearchEngine()


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "echomatrix-research-intelligence",
        "message": "Turn observations and external information into structured intelligence.",
        "mode": "simulation-first",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "research-intelligence"}


@app.post("/prompt", tags=["research"])
def create_research_prompt(request: ResearchRequest) -> dict[str, str]:
    return {"prompt": engine.research_prompt(request)}


@app.post("/findings", response_model=ResearchFinding, tags=["research"])
def build_finding(
    request: ResearchRequest,
    summary: str,
    key_points: list[str] | None = None,
) -> ResearchFinding:
    return engine.build_finding(
        request=request,
        summary=summary,
        key_points=key_points or [],
        sources=[],
    )


@app.post("/market-context", response_model=MarketResearchContext, tags=["market"])
def market_context(request: MarketResearchRequest) -> MarketResearchContext:
    """Normalize a market observation without claiming it is live external research."""
    return engine.market_context(request)
