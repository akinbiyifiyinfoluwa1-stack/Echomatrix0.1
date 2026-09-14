"""Integrated EchoMatrix brain runtime: real observations -> intelligence -> simulation -> learning."""
import os
from fastapi import FastAPI, HTTPException
import httpx
from app.models import BrainCycleRequest, BrainCycleResponse, ReplayRequest
from app.data_quality import validate_candles
from app.features import feature_snapshot
from app.research import research_snapshot
from app.strategy import strategy_snapshot
from app.risk import risk_snapshot
from app.allocation import allocation_snapshot
from app.simulation import replay_returns, simulate_decision
from app.council import run_council
from app.learning import LearningMemory

app = FastAPI(title="EchoMatrix Brain Runtime", version="1.0.0", description="Simulation-only integrated intelligence runtime. No broker, wallet, or order execution.")
memory = LearningMemory()
last_cycle: dict | None = None

async def fetch_candles(symbol: str, timeframe: str, limit: int) -> list[dict]:
    base = os.getenv("MARKET_DATA_URL", "http://market-data:8000").rstrip("/")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{base}/market/candles", params={"symbol": symbol, "timeframe": timeframe, "limit": limit})
        r.raise_for_status(); data = r.json()
    return data.get("candles", data) if isinstance(data, dict) else data

@app.get("/", tags=["meta"])
def root(): return {"service":"echomatrix-brain-runtime","mode":"simulation-only","execution":"false","principle":"Build the brain first. Give the brain a body later."}

@app.get("/health", tags=["meta"])
def health(): return {"status":"ok","service":"brain-runtime","execution":"false"}

@app.post("/brain/cycle", response_model=BrainCycleResponse, tags=["brain"])
async def cycle(request: BrainCycleRequest):
    global last_cycle
    try: raw = await fetch_candles(request.symbol, request.timeframe, request.limit)
    except Exception as exc: raise HTTPException(status_code=502, detail=f"market-data unavailable: {exc}") from exc
    try:
        from app.models import Candle
        candles=[Candle(**item) for item in raw]
    except Exception as exc: raise HTTPException(status_code=502, detail=f"invalid market observations: {exc}") from exc
    quality=validate_candles(candles)
    if not quality["valid"]: raise HTTPException(status_code=422, detail=quality)
    features=feature_snapshot(candles); research=research_snapshot(features); strategy=strategy_snapshot(features, research)
    context={"observation":features,"research":research,"strategy":strategy,"memory":memory.recall(features["regime"],"trend")}
    council=await run_council(context, request.use_ai)
    risk=risk_snapshot(features,strategy); allocation=allocation_snapshot(strategy,risk)
    sim=simulate_decision(float(features["last_price"]), allocation["status"], allocation["allocated_value"], float(features["last_price"]))
    learning=memory.record(features["regime"],"trend",council.get("consensus","none"),sim["simulated_pnl"])
    trace=["market.observed","data.quality","market.state","research.ready","strategy.ensemble","ai.council","risk.gate","capital.allocation","simulation.fill","outcome.recorded","memory.learned"]
    last_cycle={"mode":"simulation-only","symbol":request.symbol,"timeframe":request.timeframe,"data_quality":quality,"market_state":features,"research":research,"strategy":strategy,"ai_council":council,"risk":risk,"allocation":allocation,"simulation":sim,"learning":learning,"trace":trace}
    return last_cycle

@app.post("/brain/replay", tags=["research"])
def replay(request: ReplayRequest):
    quality=validate_candles(request.candles)
    if not quality["valid"]: raise HTTPException(status_code=422, detail=quality)
    prices=[float(c.close) for c in request.candles]
    result=replay_returns(prices,float(request.allocation_fraction),float(request.fee_rate))
    result["data_quality"]=quality; result["mode"]="historical-research"; result["simulation_only"]=True
    return result

@app.get("/brain/status", tags=["diagnostics"])
def status(): return {"status":"ready","last_cycle":last_cycle,"memory_size":len(memory.records),"real_money_execution":False}
