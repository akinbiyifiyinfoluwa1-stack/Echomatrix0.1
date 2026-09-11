"""Simulation domain models for paper trading and historical replay."""
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class SimulatedOrder(BaseModel):
    instrument_symbol: str = Field(min_length=1)
    side: Side
    order_type: OrderType = OrderType.MARKET
    quantity: Decimal = Field(gt=0)
    requested_price: Decimal | None = Field(default=None, gt=0)
    timestamp: datetime


class SimulationRequest(BaseModel):
    account_id: str = Field(default="demo-001", min_length=1)
    initial_cash: Decimal = Field(default=Decimal("10000"), gt=0)
    instrument_symbol: str = Field(min_length=1)
    side: Side
    quantity: Decimal = Field(gt=0)
    market_price: Decimal = Field(gt=0)
    fee_rate: Decimal = Field(default=Decimal("0.001"), ge=0, le=1)


class SimulatedFill(BaseModel):
    order: SimulatedOrder
    fill_price: Decimal = Field(gt=0)
    filled_quantity: Decimal = Field(gt=0)
    fee: Decimal = Field(default=Decimal("0"), ge=0)
    timestamp: datetime


class SimulatedPosition(BaseModel):
    instrument_symbol: str
    quantity: Decimal
    average_entry_price: Decimal = Field(gt=0)
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")


class SimulationAccount(BaseModel):
    account_id: str = Field(min_length=1)
    initial_cash: Decimal = Field(gt=0)
    cash: Decimal
    equity: Decimal
    positions: list[SimulatedPosition] = Field(default_factory=list)
    fills: list[SimulatedFill] = Field(default_factory=list)
