"""EchoMatrix end-to-end intelligence pipeline API."""
from fastapi import FastAPI, HTTPException

from app.models import PipelineRequest, PipelineResult
from app.pipeline import EchoMatrixPipeline, PipelineError

app = FastAPI(
    title="EchoMatrix Integration Pipeline",
    description="End-to-end coordinator from market intelligence to persistent simulated decisions.",
    version="0.1.0",
)

pipeline = EchoMatrixPipeline()


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "echomatrix-integration-pipeline",
        "mode": "simulation-first",
        "message": "Connect the brain end-to-end before giving it a real-money body.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "integration-pipeline"}


@app.post("/pipeline/run", response_model=PipelineResult, tags=["pipeline"])
async def run_pipeline(request: PipelineRequest) -> PipelineResult:
    try:
        return await pipeline.run(request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"pipeline stage failed: {exc}") from exc


@app.get("/pipeline/demo", response_model=PipelineResult, tags=["demo"])
async def demo_pipeline() -> PipelineResult:
    request = PipelineRequest(
        symbol="BTC/USD",
        price=101000,
        previous_price=100000,
        volume=12.5,
        portfolio_equity=10000,
        current_exposure=3000,
        proposed_position_value=2000,
        stop_distance=2000,
        daily_drawdown=0.01,
        research_confidence=0.80,
        ai_confidence=0.85,
        persist=True,
    )
    try:
        return await pipeline.run(request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"pipeline stage failed: {exc}") from exc
