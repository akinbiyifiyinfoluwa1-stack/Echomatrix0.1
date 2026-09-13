"""HTTP entrypoint for the EchoMatrix core brain."""
import os

import httpx
from fastapi import FastAPI, HTTPException

from app.engine import EchoMatrixCore
from app.models import CycleRequest

app = FastAPI(
    title="EchoMatrix Core",
    description="Simulation-first intelligence runtime. No live execution.",
    version="0.2.0",
)
core = EchoMatrixCore()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "echomatrix-core", "mode": "simulation"}


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "echomatrix-core",
        "message": "Build the brain first. Give the brain a body later.",
        "pipeline": "connected",
    }


@app.post("/cycle")
def cycle(request: CycleRequest) -> dict:
    """Run the deterministic core baseline without external service calls."""
    return core.run_cycle(request).model_dump(mode="json")


@app.post("/demo/cycle")
def demo_cycle() -> dict:
    request = CycleRequest(
        symbol="BTC/USD",
        price="102000",
        previous_price="100000",
        volume="1",
    )
    return core.run_cycle(request).model_dump(mode="json")


@app.post("/end-to-end")
async def end_to_end(request: CycleRequest) -> dict:
    """Delegate one simulation cycle to the canonical multi-service brain.

    The integration pipeline owns research, strategy, AI, risk, allocation,
    simulation, portfolio, persistence, and memory. This endpoint makes the
    core runtime the public brain entrypoint while keeping execution simulated.
    """
    pipeline_url = os.getenv(
        "INTEGRATION_PIPELINE_URL",
        "http://integration-pipeline:8000",
    ).rstrip("/")

    price_change = abs((request.price - request.previous_price) / request.previous_price)
    proposed_position = request.simulated_cash * request.max_exposure
    stop_distance = request.price * max(price_change, 0.01)

    payload = {
        "symbol": request.symbol,
        "price": str(request.price),
        "previous_price": str(request.previous_price),
        "volume": str(request.volume),
        "portfolio_equity": str(request.simulated_cash),
        "current_exposure": "0",
        "proposed_position_value": str(proposed_position),
        "stop_distance": str(stop_distance),
        "daily_drawdown": "0",
        "research_confidence": "0.8",
        "ai_confidence": str(request.confidence_threshold),
        "use_ai": True,
        "simulate": True,
        "persist": True,
        "account_id": "echomatrix-core-demo",
        "initial_cash": str(request.simulated_cash),
        "fee_rate": "0.001",
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{pipeline_url}/pipeline/run", json=payload)
            response.raise_for_status()
            result = response.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"end-to-end pipeline failed: {exc}") from exc

    return {
        "service": "echomatrix-core",
        "mode": "simulation",
        "real_money_execution": False,
        "cycle": result,
    }
