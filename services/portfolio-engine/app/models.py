"""Portfolio domain models for positions, fills, and mark-to-market state."""
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class AssetClass(str, Enum):
    FOREX = "forex"
    CRYPTO = "crypto"
    STOCK = "stock"
    INDEX = "index"
    COMMODITY = "commodity"
    ENERGY = "energy"
    METAL = "metal"
    NFT = "nft"
    OTHER = "other"


class Position(BaseModel):
    symbol: str = Field(min_length=1)
    asset_class: AssetClass = AssetClass.OTHER
    quantity: Decimal = Decimal("0")
    average_entry_price: Decimal = Field(default=Decimal("0"), ge=0)
    mark_price: Decimal = Field(default=Decimal("0"), ge=0)
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")

    @property
    def market_value(self) -> Decimal:
        return self.quantity * self.mark_price


class Fill(BaseModel):
    symbol: str = Field(min_length=1)
    asset_class: AssetClass = AssetClass.OTHER
    side: str = Field(pattern="^(buy|sell)$")
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    fee: Decimal = Field(default=Decimal("0"), ge=0)
    timestamp: datetime


class Portfolio(BaseModel):
    portfolio_id: str = Field(min_length=1)
    starting_cash: Decimal = Field(gt=0)
    cash: Decimal
    realized_pnl: Decimal = Decimal("0")
    positions: list[Position] = Field(default_factory=list)
    fills: list[Fill] = Field(default_factory=list)

    @property
    def market_value(self) -> Decimal:
        return sum((position.market_value for position in self.positions), Decimal("0"))

    @property
    def unrealized_pnl(self) -> Decimal:
        return sum((position.unrealized_pnl for position in self.positions), Decimal("0"))

    @property
    def equity(self) -> Decimal:
        return self.cash + self.market_value
