"""EchoMatrix Research Laboratory API — simulation and research only."""
from decimal import Decimal
from fastapi import FastAPI, HTTPException
from app.contracts import ExperimentRequest, ResearchRequest, ResearchResponse, StressRequest
from app.dataset import normalize, quality_report
from app.engine import run_research, compare, stress
from app.lab import run_lab

app = FastAPI(title="EchoMatrix Research Laboratory", version="2.0.0", description="Historical research, simulation, experiments, robustness and scenario analysis. No external execution.")

@app.get("/")
def root() -> dict:
    return {"service": "research-lab", "mode": "simulation-only", "version": "2.0.0", "capabilities": ["dataset-quality", "features", "ensemble", "paper-replay", "performance", "experiments", "stress-tests", "scenario-matrix", "robustness-ranking", "unified-lab"]}

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": "simulation", "version": "2.0.0"}

@app.post("/dataset/quality")
def dataset_quality(rows: list[dict]) -> dict:
    try:
        candles = normalize(rows)
        return {"mode": "simulation-only", "quality": quality_report(candles)}
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/research", response_model=ResearchResponse)
def research(request: ResearchRequest) -> ResearchResponse:
    try:
        return ResearchResponse(mode="simulation-only", symbol=request.symbol, report=run_research(request.symbol, request.candles, request.initial_cash, request.fee_rate, request.allocation_fraction, request.threshold))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/experiments")
def experiments(request: ExperimentRequest) -> dict:
    try:
        return compare(request.symbol, request.candles, request.initial_cash, request.fee_rate, request.thresholds, request.allocations)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/stress")
def stress_test(request: StressRequest) -> dict:
    try:
        return stress(request.symbol, request.candles, request.initial_cash, request.fee_rate, request.allocation_fraction, request.threshold, request.shock_pct)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/lab")
def laboratory(request: ExperimentRequest, shock_pct: Decimal = Decimal("0.10")) -> dict:
    """Run the complete simulation research stack in one call."""
    try:
        return run_lab(request.symbol, request.candles, request.initial_cash, request.fee_rate, request.thresholds, request.allocations, shock_pct)
    except (ValueError, ArithmeticError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
