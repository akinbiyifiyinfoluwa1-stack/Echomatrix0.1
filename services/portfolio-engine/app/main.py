"""EchoMatrix persistent portfolio/account state API."""
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.engine import PortfolioEngine
from app.models import AssetClass, Fill
from app.store import PortfolioStore

app = FastAPI(
    title="EchoMatrix Portfolio Engine",
    description="Persistent balances, positions, P&L, exposure, and trade history for simulation accounts.",
    version="0.2.0",
)
store = PortfolioStore()


class AccountCreate(BaseModel):
    account_id: str = Field(min_length=1)
    initial_cash: Decimal = Field(gt=0)


class FillRequest(BaseModel):
    symbol: str = Field(min_length=1)
    asset_class: AssetClass = AssetClass.OTHER
    side: str = Field(pattern="^(buy|sell)$")
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    fee: Decimal = Field(default=Decimal("0"), ge=0)
    mark_price: Decimal | None = Field(default=None, gt=0)


def snapshot(portfolio, engine: PortfolioEngine) -> dict:
    return {
        "account_id": portfolio.portfolio_id,
        "starting_cash": str(portfolio.starting_cash),
        "cash": str(portfolio.cash),
        "market_value": str(portfolio.market_value),
        "equity": str(portfolio.equity),
        "realized_pnl": str(portfolio.realized_pnl),
        "unrealized_pnl": str(portfolio.unrealized_pnl),
        "total_pnl": str(portfolio.realized_pnl + portfolio.unrealized_pnl),
        "exposure_by_asset_class": {k: str(v) for k, v in engine.exposure_by_asset_class().items()},
        "positions": [p.model_dump(mode="json") for p in portfolio.positions if p.quantity != 0],
        "trade_count": len(portfolio.fills),
        "fills": [f.model_dump(mode="json") for f in portfolio.fills],
    }


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"service": "echomatrix-portfolio-engine", "mode": "persistent-simulation"}


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "portfolio-engine"}


@app.post("/accounts", tags=["accounts"])
async def create_account(request: AccountCreate) -> dict:
    portfolio = await store.load(request.account_id, request.initial_cash)
    record_id = await store.save(portfolio)
    return {"account_id": portfolio.portfolio_id, "created": portfolio.starting_cash == portfolio.cash, "record_id": record_id, "snapshot": snapshot(portfolio, PortfolioEngine(portfolio))}


@app.get("/accounts/{account_id}", tags=["accounts"])
async def get_account(account_id: str, initial_cash: Decimal = Decimal("10000")) -> dict:
    portfolio = await store.load(account_id, initial_cash)
    return snapshot(portfolio, PortfolioEngine(portfolio))


@app.post("/accounts/{account_id}/fills", tags=["accounts"])
async def apply_fill(account_id: str, request: FillRequest, initial_cash: Decimal = Decimal("10000")) -> dict:
    portfolio = await store.load(account_id, initial_cash)
    engine = PortfolioEngine(portfolio)
    fill = Fill(timestamp=datetime.now(timezone.utc), **request.model_dump(exclude={"mark_price"}))
    position = engine.apply_fill(fill)
    if request.mark_price is not None and position.quantity != 0:
        engine.mark_price(request.symbol, request.mark_price)
    record_id = await store.save(portfolio)
    return {"record_id": record_id, "position": position.model_dump(mode="json"), "snapshot": snapshot(portfolio, engine)}


@app.post("/accounts/{account_id}/mark", tags=["accounts"])
async def mark_account(account_id: str, prices: dict[str, Decimal]) -> dict:
    portfolio = await store.load(account_id, Decimal("10000"))
    engine = PortfolioEngine(portfolio)
    for symbol, price in prices.items():
        if any(p.symbol == symbol and p.quantity != 0 for p in portfolio.positions):
            engine.mark_price(symbol, price)
    await store.save(portfolio)
    return snapshot(portfolio, engine)


@app.get("/accounts/{account_id}/positions", tags=["accounts"])
async def positions(account_id: str) -> list[dict]:
    portfolio = await store.load(account_id, Decimal("10000"))
    return [p.model_dump(mode="json") for p in portfolio.positions if p.quantity != 0]


@app.get("/accounts/{account_id}/history", tags=["accounts"])
async def history(account_id: str) -> list[dict]:
    portfolio = await store.load(account_id, Decimal("10000"))
    return [f.model_dump(mode="json") for f in portfolio.fills]


@app.get("/demo/portfolio", tags=["demo"])
async def demo_portfolio() -> dict:
    return await get_account("demo-portfolio-001", Decimal("10000"))
