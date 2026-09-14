"""EchoMatrix end-to-end intelligence pipeline API."""
import os
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.models import PipelineRequest, PipelineResult, ReplayRequest
from app.pipeline import EchoMatrixPipeline
from app.replay import replay_market_series

app = FastAPI(
    title="EchoMatrix Integration Pipeline",
    description="End-to-end coordinator from market intelligence to persistent simulated decisions.",
    version="0.4.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
pipeline = EchoMatrixPipeline()
last_result: PipelineResult | None = None
last_replay: dict | None = None


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
        "multi_cycle_replay": "enabled",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "integration-pipeline", "mode": "simulation"}


@app.get("/readiness", tags=["meta"])
async def readiness() -> dict:
    results: dict[str, dict] = {}
    healthy = True
    async with httpx.AsyncClient(timeout=8) as client:
        for service, base_url in pipeline.services.items():
            try:
                response = await client.get(f"{base_url.rstrip('/')}/health")
                response.raise_for_status()
                results[service] = {"status": "ok"}
            except Exception as exc:
                healthy = False
                results[service] = {"status": "error", "error": str(exc)}
    return {"status": "ready" if healthy else "degraded", "checked_at": datetime.now(timezone.utc).isoformat(), "services": results}


@app.post("/pipeline/run", response_model=PipelineResult, tags=["pipeline"])
async def run_pipeline(request: PipelineRequest) -> PipelineResult:
    global last_result
    try:
        last_result = await pipeline.run(request)
        return last_result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"pipeline stage failed: {exc}") from exc


@app.post("/pipeline/replay", tags=["simulation"])
async def replay_pipeline(request: ReplayRequest) -> dict:
    """Replay many simulated market states in one request; never executes externally."""
    global last_replay
    try:
        last_replay = replay_market_series(
            request.prices,
            initial_cash=request.initial_cash,
            fee_rate=request.fee_rate,
            allocation_fraction=request.allocation_fraction,
        )
        last_replay["symbol"] = request.symbol
        return last_replay
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/pipeline/replay/demo", tags=["simulation"])
async def replay_demo() -> dict:
    request = ReplayRequest(prices=[Decimal("100000"), Decimal("101000"), Decimal("102500"), Decimal("101000"), Decimal("104000"), Decimal("103000")])
    return await replay_pipeline(request)


@app.get("/pipeline/replay/status", tags=["diagnostics"])
def replay_status() -> dict:
    return {"status": "completed" if last_replay else "idle", "last_replay": last_replay}


@app.get("/pipeline/demo", response_model=PipelineResult, tags=["demo"])
async def demo_pipeline(use_ai: bool = Query(default=True)) -> PipelineResult:
    global last_result
    request = PipelineRequest(symbol="BTC/USD", price=101000, previous_price=100000, volume=12.5, portfolio_equity=10000, current_exposure=3000, proposed_position_value=2000, stop_distance=2000, daily_drawdown=0.01, research_confidence=0.80, ai_confidence=0.85, use_ai=use_ai, simulate=True, persist=True)
    try:
        last_result = await pipeline.run(request)
        return last_result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"pipeline stage failed: {exc}") from exc


@app.get("/pipeline/self-test", tags=["diagnostics"])
async def pipeline_self_test(use_ai: bool = Query(default=False)) -> dict:
    global last_result
    request = PipelineRequest(symbol="BTC/USD", price=101000, previous_price=100000, volume=12.5, portfolio_equity=10000, current_exposure=3000, proposed_position_value=2000, stop_distance=2000, daily_drawdown=0.01, research_confidence=0.80, ai_confidence=0.85, use_ai=use_ai, simulate=True, persist=True, account_id="backend-self-test")
    started_at = datetime.now(timezone.utc)
    try:
        result = await pipeline.run(request)
        last_result = result
        return {"status": "passed", "mode": "ai" if use_ai else "infrastructure", "started_at": started_at.isoformat(), "completed_at": datetime.now(timezone.utc).isoformat(), "correlation_id": result.correlation_id, "stages_completed": result.stages_completed, "stage_count": len(result.stages_completed), "action": result.action, "allocated_value": str(result.allocated_value), "persisted_record_id": result.persisted_record_id, "simulation_fill_created": result.simulation_fill is not None, "real_money_execution": False}
    except Exception as exc:
        return {"status": "failed", "mode": "ai" if use_ai else "infrastructure", "started_at": started_at.isoformat(), "completed_at": datetime.now(timezone.utc).isoformat(), "error": str(exc), "real_money_execution": False}


@app.get("/pipeline/status", tags=["diagnostics"])
def pipeline_status() -> dict:
    return {"status": "idle", "last_result": None} if last_result is None else {"status": "completed", "last_result": last_result.model_dump(mode="json")}


@app.get("/dashboard/overview", tags=["dashboard"])
async def dashboard_overview(account_id: str = "pipeline-demo") -> dict:
    try:
        account = await portfolio_get(f"/accounts/{account_id}", {"initial_cash": "10000"})
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"portfolio service unavailable: {exc}") from exc
    return {"mode": "simulation", "account": account, "latest_cycle": last_result.model_dump(mode="json") if last_result else None, "latest_replay": last_replay, "ai_confidence": str(last_result.confidence) if last_result else None, "stages": last_result.stages_completed if last_result else []}


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
    return await demo_pipeline(use_ai=False)
