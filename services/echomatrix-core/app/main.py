"""HTTP entrypoint for the EchoMatrix core brain."""
import os

import httpx
from fastapi import FastAPI, HTTPException

from app.engine import EchoMatrixCore
from app.models import CycleRequest

app = FastAPI(
    title="EchoMatrix Core",
    description="Simulation-first intelligence runtime. No live execution.",
    version="0.4.0",
)
core = EchoMatrixCore()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "echomatrix-core", "mode": "simulation", "brain_loop": "connected"}


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "echomatrix-core",
        "message": "Build the brain first. Give the brain a body later.",
        "pipeline": "connected",
        "market_data": "connected",
        "brain_loop": "market→research→strategy→ai→risk→allocation→simulation→memory→learning",
        "real_money_execution": "false",
    }


@app.post("/cycle")
def cycle(request: CycleRequest) -> dict:
    return core.run_cycle(request).model_dump(mode="json")


@app.post("/demo/cycle")
def demo_cycle() -> dict:
    request = CycleRequest(symbol="BTC/USD", price="102000", previous_price="100000", volume="1")
    return core.run_cycle(request).model_dump(mode="json")


async def _run_pipeline(payload: dict) -> dict:
    pipeline_url = os.getenv("INTEGRATION_PIPELINE_URL", "http://integration-pipeline:8000").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{pipeline_url}/pipeline/run", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"end-to-end pipeline failed: {exc}") from exc


def _pipeline_payload(request: CycleRequest) -> dict:
    price_change = abs((request.price - request.previous_price) / request.previous_price)
    proposed_position = request.simulated_cash * request.max_exposure
    stop_distance = request.price * max(price_change, 0.01)
    return {
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


@app.post("/end-to-end")
async def end_to_end(request: CycleRequest) -> dict:
    result = await _run_pipeline(_pipeline_payload(request))
    return {"service": "echomatrix-core", "mode": "simulation", "real_money_execution": False, "cycle": result}


@app.post("/data-driven-cycle")
async def data_driven_cycle() -> dict:
    market_url = os.getenv("MARKET_DATA_URL", "http://market-data:8000").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{market_url}/demo/candle")
            response.raise_for_status()
            candle = response.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"market-data fetch failed: {exc}") from exc

    request = CycleRequest(
        symbol=candle["instrument"]["symbol"],
        price=candle["close"],
        previous_price=candle["open"],
        volume=candle.get("volume") or "0",
    )
    result = await _run_pipeline(_pipeline_payload(request))
    return {
        "service": "echomatrix-core",
        "mode": "simulation",
        "real_money_execution": False,
        "source": "market-data",
        "observation": candle,
        "cycle": result,
    }


@app.post("/brain-cycle")
async def brain_cycle() -> dict:
    """Run one complete sensory-to-learning simulation cycle."""
    return await data_driven_cycle()
