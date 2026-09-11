"""EchoMatrix end-to-end intelligence pipeline API."""
import os

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import PipelineRequest, PipelineResult
from app.pipeline import EchoMatrixPipeline

app = FastAPI(
    title="EchoMatrix Integration Pipeline",
    description="End-to-end coordinator from market intelligence to persistent simulated decisions.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = EchoMatrixPipeline()
last_result: PipelineResult | None = None


async def portfolio_get(path: str, params: dict | None = None) -> dict | list:
    base_url = os.getenv("PORTFOLIO_ENGINE_URL", "http://portfolio-engine:8000").rstrip("/")
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(f"{base_url}{path}", params=params)
        response.raise_for_status()
        return response.json()


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
    global last_result
    try:
        last_result = await pipeline.run(request)
        return last_result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"pipeline stage failed: {exc}") from exc


@app.get("/pipeline/demo", response_model=PipelineResult, tags=["demo"])
async def demo_pipeline() -> PipelineResult:
    global last_result
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
        last_result = await pipeline.run(request)
        return last_result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"pipeline stage failed: {exc}") from exc


@app.get("/dashboard/overview", tags=["dashboard"])
async def dashboard_overview(account_id: str = "pipeline-demo") -> dict:
    """Single read model consumed by the public EchoMatrix dashboard."""
    try:
        account = await portfolio_get(
            f"/accounts/{account_id}",
            {"initial_cash": "10000"},
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"portfolio service unavailable: {exc}") from exc

    return {
        "mode": "simulation",
        "account": account,
        "latest_cycle": last_result.model_dump(mode="json") if last_result else None,
        "ai_confidence": str(last_result.confidence) if last_result else None,
        "stages": last_result.stages_completed if last_result else [],
    }


@app.get("/dashboard/positions", tags=["dashboard"])
async def dashboard_positions(account_id: str = "pipeline-demo") -> list[dict]:
    try:
        return await portfolio_get(f"/accounts/{account_id}/positions")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"portfolio service unavailable: {exc}") from exc


@app.get("/dashboard/history", tags=["dashboard"])
async def dashboard_history(account_id: str = "pipeline-demo") -> list[dict]:
    try:
        return await portfolio_get(f"/accounts/{account_id}/history")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"portfolio service unavailable: {exc}") from exc


@app.post("/dashboard/run-cycle", response_model=PipelineResult, tags=["dashboard"])
async def dashboard_run_cycle() -> PipelineResult:
    return await demo_pipeline()
