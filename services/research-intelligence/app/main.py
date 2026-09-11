"""Research Intelligence API."""
from fastapi import FastAPI

from app.engine import ResearchEngine
from app.models import ResearchFinding, ResearchRequest

app = FastAPI(
    title="Ecometrics Research Intelligence",
    description="Structured research layer feeding AI Core and intelligence memory.",
    version="0.1.0",
)

engine = ResearchEngine()


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "ecometrics-research-intelligence",
        "message": "Turn external information into structured intelligence.",
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
