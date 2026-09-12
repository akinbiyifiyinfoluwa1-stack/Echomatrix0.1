"""EchoMatrix single-process cloud runtime.

This deployment surface exposes the public dashboard contract while the deeper
microservices remain modular under services/. It is simulation-only by design.
"""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="EchoMatrix Core",
    description="AI Financial and Wealth Operating System — simulation runtime.",
    version="0.4.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOCK = Lock()
ACCOUNT_ID = "pipeline-demo"
INITIAL_CASH = Decimal("10000")
state = {
    "cash": INITIAL_CASH,
    "positions": {},
    "history": [],
    "cycles": 0,
    "last_cycle": None,
}


class CycleResult(BaseModel):
    correlation_id: str
    symbol: str
    action: str
    price: Decimal
    quantity: Decimal
    allocated_value: Decimal
    confidence: Decimal
    simulated_pnl: Decimal
    timestamp: str


def q(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def run_cycle() -> CycleResult:
    with LOCK:
        state["cycles"] += 1
        cycle = state["cycles"]
        # Deterministic market stream: enough movement to demonstrate the
        # intelligence loop without connecting to a live venue.
        price = Decimal("101000") + Decimal(str((cycle % 7) * 175 - 350))
        previous = Decimal("100650") + Decimal(str(((cycle - 1) % 7) * 175 - 350))
        momentum = (price - previous) / previous
        action = "BUY" if momentum >= 0 else "HOLD"
        confidence = min(Decimal("0.97"), Decimal("0.70") + abs(momentum) * 30)
        allocated = Decimal("1000") if action == "BUY" else Decimal("0")
        quantity = q(allocated / price) if allocated else Decimal("0")
        pnl = q((price - previous) * quantity) if quantity else Decimal("0")

        if action == "BUY" and quantity > 0:
            state["cash"] = q(state["cash"] - allocated)
            position = state["positions"].setdefault(
                "BTC/USD", {"symbol": "BTC/USD", "quantity": Decimal("0"), "average_price": price}
            )
            old_qty = position["quantity"]
            new_qty = old_qty + quantity
            position["average_price"] = q(
                ((old_qty * position["average_price"]) + (quantity * price)) / new_qty
            )
            position["quantity"] = new_qty

        result = CycleResult(
            correlation_id=str(uuid4()),
            symbol="BTC/USD",
            action=action,
            price=price,
            quantity=quantity,
            allocated_value=allocated,
            confidence=q(confidence),
            simulated_pnl=pnl,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        state["history"].insert(0, result.model_dump(mode="json"))
        state["history"] = state["history"][:50]
        state["last_cycle"] = result.model_dump(mode="json")
        return result


def position_rows() -> list[dict]:
    rows = []
    for position in state["positions"].values():
        rows.append(
            {
                "symbol": position["symbol"],
                "quantity": str(position["quantity"]),
                "average_price": str(position["average_price"]),
                "mark_price": str(state["last_cycle"]["price"] if state["last_cycle"] else position["average_price"]),
                "mode": "simulation",
            }
        )
    return rows


@app.get("/")
def root():
    return {"service": "echomatrix-core", "mode": "simulation", "message": "Build the brain first. Give the brain a body later."}


@app.get("/api/health")
@app.get("/health")
def health():
    return {"status": "ok", "service": "echomatrix-core", "mode": "simulation"}


@app.get("/dashboard")
def dashboard(account_id: str = ACCOUNT_ID):
    return dashboard_overview(account_id)


@app.get("/dashboard/overview")
def dashboard_overview(account_id: str = ACCOUNT_ID):
    positions = position_rows()
    exposure = sum(Decimal(row["quantity"]) * Decimal(row["mark_price"]) for row in positions)
    equity = q(state["cash"] + exposure)
    last = state["last_cycle"]
    return {
        "mode": "simulation",
        "account": {
            "account_id": account_id,
            "starting_cash": str(INITIAL_CASH),
            "cash": str(state["cash"]),
            "market_value": str(q(exposure)),
            "equity": str(equity),
            "realized_pnl": "0.00",
            "unrealized_pnl": "0.00",
            "total_pnl": str(q(equity - INITIAL_CASH)),
            "trade_count": len(state["history"]),
        },
        "latest_cycle": last,
        "ai_confidence": last["confidence"] if last else None,
        "stages": [
            "market_data",
            "strategy",
            "research",
            "ai",
            "risk",
            "capital_allocation",
            "simulation",
            "portfolio",
            "memory",
        ] if last else [],
    }


@app.get("/dashboard/positions")
def dashboard_positions(account_id: str = ACCOUNT_ID):
    return position_rows()


@app.get("/dashboard/history")
def dashboard_history(account_id: str = ACCOUNT_ID):
    return state["history"]


@app.post("/dashboard/run-cycle", response_model=CycleResult)
def dashboard_run_cycle():
    return run_cycle()
