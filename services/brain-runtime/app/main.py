"""Integrated EchoMatrix brain runtime: simulation-only cognitive runtime."""
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
from app.advanced import (
    full_brain_replay, evolve_strategies, evaluate_providers, portfolio_intelligence,
    DurableMemory, ExternalIntelligence, SystemEvaluator, Hardening, AutonomousSimulation,
    StrategyCandidate,
)

app = FastAPI(title="EchoMatrix Brain Runtime", version="2.0.0", description="Simulation-only integrated intelligence runtime. No broker, wallet, or order execution.")
memory = LearningMemory(); durable = DurableMemory(); autonomous = AutonomousSimulation()
last_cycle: dict | None = None

async def fetch_candles(symbol: str, timeframe: str, limit: int) -> list[dict]:
    base = os.getenv("MARKET_DATA_URL", "http://market-data:8000").rstrip("/")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{base}/market/candles", params={"symbol": symbol, "timeframe": timeframe, "limit": limit})
        r.raise_for_status(); data = r.json()
    return data.get("candles", data) if isinstance(data, dict) else data

@app.get("/", tags=["meta"])
def root(): return {"service":"echomatrix-brain-runtime","mode":"simulation-only","execution":False,"capabilities":10}

@app.get("/health", tags=["meta"])
def health(): return {"status":"ok","service":"brain-runtime","execution":False}

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
    # Current-cycle fill is marked against the next observation when available by the full replay endpoint.
    sim=simulate_decision(float(features["last_price"]), allocation["status"], allocation["allocated_value"], float(features["last_price"]))
    learning=memory.record(features["regime"],"trend",council.get("consensus","none"),sim["simulated_pnl"])
    durable_hash=durable.write({"kind":"brain-cycle","symbol":request.symbol,"timeframe":request.timeframe,"features":features,"research":research,"strategy":strategy,"simulation":sim})
    trace=["market.observed","data.quality","market.state","research.ready","strategy.ensemble","ai.council","risk.gate","capital.allocation","simulation.fill","outcome.recorded","memory.learned","durable.memory"]
    last_cycle={"mode":"simulation-only","symbol":request.symbol,"timeframe":request.timeframe,"data_quality":quality,"market_state":features,"research":research,"strategy":strategy,"ai_council":council,"risk":risk,"allocation":allocation,"simulation":sim,"learning":learning,"durable_memory_hash":durable_hash,"trace":trace}
    return last_cycle

@app.post("/brain/replay", tags=["research"])
def replay(request: ReplayRequest):
    quality=validate_candles(request.candles)
    if not quality["valid"]: raise HTTPException(status_code=422, detail=quality)
    result=replay_returns([float(c.close) for c in request.candles],float(request.allocation_fraction),float(request.fee_rate))
    result["data_quality"]=quality; result["mode"]="historical-research"; result["simulation_only"]=True
    return result

@app.post("/brain/full-replay", tags=["advanced"])
def full_replay(request: ReplayRequest):
    return full_brain_replay(request.candles, float(request.initial_cash), float(request.fee_rate))

@app.post("/brain/evolve", tags=["advanced"])
def evolve(payload: dict):
    candidates=[StrategyCandidate(**x) for x in payload.get("candidates", [])]
    if not candidates: candidates=[StrategyCandidate("trend",.5,.3,.2,.2),StrategyCandidate("momentum",.2,.6,.2,.25),StrategyCandidate("volume",.25,.25,.5,.2)]
    return evolve_strategies(candidates, payload.get("results", {}), int(payload.get("generations",3)))

@app.post("/brain/provider-evaluation", tags=["advanced"])
def provider_evaluation(payload: dict): return evaluate_providers(payload.get("responses", {}))

@app.post("/brain/portfolio-intelligence", tags=["advanced"])
def portfolio(payload: dict): return portfolio_intelligence(payload.get("outcomes", []))

@app.post("/brain/external-intelligence", tags=["advanced"])
def external_intelligence(payload: dict): return {"items":ExternalIntelligence().normalize(payload.get("items", [])),"simulation_only":True}

@app.get("/brain/memory", tags=["advanced"])
def memory_read(limit: int = 100): return {"records":durable.read(limit),"durable":True,"simulation_only":True}

@app.post("/brain/evaluate", tags=["advanced"])
def evaluate(payload: dict): return SystemEvaluator().evaluate(payload.get("replay", {}), payload.get("expected", {}))

@app.get("/brain/hardening", tags=["advanced"])
def hardening(): return Hardening.run(dict(os.environ))

@app.post("/brain/autonomous-simulation", tags=["advanced"])
def autonomous_simulation(request: ReplayRequest): return autonomous.run(request.candles, 1)

@app.get("/brain/status", tags=["diagnostics"])
def status(): return {"status":"ready","last_cycle":last_cycle,"memory_size":len(memory.records),"durable_memory":True,"real_money_execution":False,"advanced_capabilities":10}
