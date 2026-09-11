"""Simulation API for the Ecometrics paper-trading brain."""
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI

from app.engine import SimulationEngine
from app.models import OrderType, Side, SimulatedAccount, SimulatedOrder

app = FastAPI(
    title="Ecometrics Simulation Engine",
    description="Paper-trading and capital simulation service. No real-money execution.",
    version="0.1.0",
)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "ecometrics-simulation-engine",
        "message": "Test the brain before giving it a body.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "simulation-engine"}


@app.post("/demo/buy", tags=["demo"])
def demo_buy() -> dict:
    account = SimulatedAccount(
        account_id="demo-001",
        initial_cash=Decimal("10000"),
        cash=Decimal("10000"),
        equity=Decimal("10000"),
    )
    order = SimulatedOrder(
        instrument_symbol="BTC/USD",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("0.01"),
        timestamp=datetime.now(timezone.utc),
    )
    engine = SimulationEngine(account)
    fill = engine.execute_market_order(order, Decimal("100000"), Decimal("0.001"))
    return {"fill": fill.model_dump(mode="json"), "account": account.model_dump(mode="json")}
