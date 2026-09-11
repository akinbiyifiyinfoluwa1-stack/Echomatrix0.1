"""Portfolio API for the Ecometrics capital layer."""
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI

from app.engine import PortfolioEngine
from app.models import AssetClass, Fill, Portfolio

app = FastAPI(
    title="Ecometrics Portfolio Engine",
    description="Portfolio accounting, positions, exposure, and mark-to-market state.",
    version="0.1.0",
)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "ecometrics-portfolio-engine",
        "message": "Turn simulated fills into portfolio intelligence.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "portfolio-engine"}


@app.get("/demo/portfolio", tags=["demo"])
def demo_portfolio() -> dict:
    portfolio = Portfolio(
        portfolio_id="demo-portfolio-001",
        starting_cash=Decimal("10000"),
        cash=Decimal("10000"),
    )
    engine = PortfolioEngine(portfolio)
    engine.apply_fill(
        Fill(
            symbol="BTC/USD",
            asset_class=AssetClass.CRYPTO,
            side="buy",
            quantity=Decimal("0.05"),
            price=Decimal("100000"),
            fee=Decimal("5"),
            timestamp=datetime.now(timezone.utc),
        )
    )
    engine.mark_price("BTC/USD", Decimal("101000"))

    return {
        "portfolio_id": portfolio.portfolio_id,
        "cash": str(portfolio.cash),
        "market_value": str(portfolio.market_value),
        "equity": str(portfolio.equity),
        "realized_pnl": str(portfolio.realized_pnl),
        "unrealized_pnl": str(portfolio.unrealized_pnl),
        "exposure_by_asset_class": {
            key: str(value) for key, value in engine.exposure_by_asset_class().items()
        },
        "positions": [position.model_dump(mode="json") for position in portfolio.positions],
        "fills": [fill.model_dump(mode="json") for fill in portfolio.fills],
    }
