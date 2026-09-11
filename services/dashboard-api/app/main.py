"""Safe EchoMatrix dashboard API.

This service is simulation-only. It never connects to brokers, exchanges,
wallets, or real-money execution systems.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="EchoMatrix Dashboard API",
    description="Simulation-only read model and intelligence-cycle API for EchoMatrix.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOCK = Lock()
STARTING_CASH = Decimal("10000")
state = {
    "cash": STARTING_CASH,
    "equity": STARTING_CASH,
    "exposure": Decimal("0"),
    "confidence": None,
    "cycle": None,
    "positions": [],
    "history": [],
    "equity_curve": [STARTING_CASH],
}


class CycleResult(BaseModel):
    correlation_id: str
    action: str
    symbol: str
    confidence: Decimal
    allocated_value: Decimal
    risk_amount: Decimal
    stages_completed: list[str]
    simulation_fill: dict | None = None


def dec(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value))


def snapshot() -> dict:
    return {
        "cash": state["cash"],
        "equity": state["equity"],
        "starting_cash": STARTING_CASH,
        "market_value": state["exposure"],
        "exposure": state["exposure"],
        "total_pnl": state["equity"] - STARTING_CASH,
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "dashboard-api", "mode": "simulation"}


@app.get("/")
def root():
    return {
        "service": "echomatrix-dashboard-api",
        "mode": "simulation-only",
        "message": "Build the brain first. Give the brain a body later.",
    }


@app.get("/dashboard")
def dashboard(account_id: str = "pipeline-demo"):
    return {
        "overview": {
            "mode": "simulation",
            "account_id": account_id,
            "account": snapshot(),
            "latest_cycle": state["cycle"],
            "ai_confidence": state["confidence"],
            "stages": state["cycle"]["stages_completed"] if state["cycle"] else [],
        },
        "positions": state["positions"],
        "history": state["history"],
        "equity_curve": state["equity_curve"],
    }


@app.get("/dashboard/overview")
def dashboard_overview(account_id: str = "pipeline-demo"):
    return dashboard(account_id)["overview"]


@app.get("/dashboard/positions")
def dashboard_positions(account_id: str = "pipeline-demo"):
    return state["positions"]


@app.get("/dashboard/history")
def dashboard_history(account_id: str = "pipeline-demo"):
    return state["history"]


@app.post("/dashboard/run-cycle", response_model=CycleResult)
def run_cycle():
    """Run one deterministic, simulation-only intelligence cycle."""
    with LOCK:
        price = Decimal("101000") if not state["cycle"] else Decimal("101000") + dec(len(state["history"])) * Decimal("250")
        previous = price - Decimal("1000")
        momentum = (price - previous) / previous
        confidence = min(Decimal("0.95"), Decimal("0.70") + momentum * Decimal("20"))
        allocated = Decimal("1000")
        risk_amount = allocated * Decimal("0.01")
        correlation_id = str(uuid4())
        stages = [
            "market.update",
            "research.ready",
            "strategy.signal",
            "ai.analysis",
            "risk.decision",
            "capital.allocation",
            "trade.decision",
            "simulation.fill",
            "outcome.recorded",
            "memory.written",
        ]
        fill = {
            "symbol": "BTC/USD",
            "side": "BUY",
            "quantity": str((allocated / price).quantize(Decimal("0.00000001"))),
            "price": str(price),
            "value": str(allocated),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        # Keep one small virtual position so the dashboard visibly demonstrates
        # the complete lifecycle. No broker/exchange call is made.
        state["positions"] = [{
            "symbol": fill["symbol"],
            "side": fill["side"],
            "quantity": fill["quantity"],
            "average_entry_price": fill["price"],
            "mark_price": fill["price"],
            "unrealized_pnl": "0",
            "status": "OPEN",
        }]
        state["cash"] = STARTING_CASH - allocated
        state["exposure"] = allocated
        state["equity"] = STARTING_CASH
        state["confidence"] = confidence
        state["equity_curve"].append(state["equity"])
        result = CycleResult(
            correlation_id=correlation_id,
            action="BUY",
            symbol="BTC/USD",
            confidence=confidence,
            allocated_value=allocated,
            risk_amount=risk_amount,
            stages_completed=stages,
            simulation_fill=fill,
        )
        state["cycle"] = result.model_dump(mode="json")
        state["history"].insert(0, {
            "id": correlation_id,
            "timestamp": fill["timestamp"],
            "symbol": "BTC/USD",
            "action": "BUY",
            "value": str(allocated),
            "mode": "simulation",
        })
        return result


@app.get("/dashboard/health")
def dashboard_health():
    return {
        "gateway": {"status": "ok"},
        "dashboard_api": {"status": "ok", "mode": "simulation"},
        "portfolio": {"status": "ok"},
        "simulation": {"status": "ok"},
    }
