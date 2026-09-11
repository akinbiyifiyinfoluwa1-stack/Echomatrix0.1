"""Simulation API for the EchoMatrix paper-trading brain."""
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI

from app.engine import SimulationEngine
from app.models import (
    OrderType,
    Side,
    SimulatedAccount,
    SimulatedOrder,
    SimulationRequest,
)

app = FastAPI(
    title="EchoMatrix Simulation Engine",
    description="Paper-trading and capital simulation service. No real-money execution.",
    version="0.2.0",
)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "echomatrix-simulation-engine",
        "message": "Test the brain before giving it a body.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "simulation-engine"}


@app.post("/simulate", tags=["simulation"])
def simulate(request: SimulationRequest) -> dict:
    """Execute one deterministic paper fill at the supplied market price."""
    account = SimulatedAccount(
        account_id=request.account_id,
        initial_cash=request.initial_cash,
        cash=request.initial_cash,
        equity=request.initial_cash,
    )
    order = SimulatedOrder(
        instrument_symbol=request.instrument_symbol,
        side=request.side,
        order_type=OrderType.MARKET,
        quantity=request.quantity,
        timestamp=datetime.now(timezone.utc),
    )
    engine = SimulationEngine(account)
    fill = engine.execute_market_order(order, request.market_price, request.fee_rate)
    return {"fill": fill.model_dump(mode="json"), "account": account.model_dump(mode="json")}


@app.post("/demo/buy", tags=["demo"])
def demo_buy() -> dict:
    return simulate(
        SimulationRequest(
            instrument_symbol="BTC/USD",
            side=Side.BUY,
            quantity=Decimal("0.01"),
            market_price=Decimal("100000"),
        )
    )
