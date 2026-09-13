"""Core contracts for a simulation-only EchoMatrix brain cycle."""
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field

Action = Literal["BUY", "SELL", "HOLD"]


class CycleRequest(BaseModel):
    symbol: str = Field(default="BTC/USD", min_length=3)
    price: Decimal = Field(gt=0)
    previous_price: Decimal = Field(gt=0)
    volume: Decimal = Field(default=Decimal("1"), ge=0)
    simulated_cash: Decimal = Field(default=Decimal("10000"), gt=0)
    max_exposure: Decimal = Field(default=Decimal("0.25"), gt=0, le=1)
    confidence_threshold: Decimal = Field(default=Decimal("0.60"), ge=0, le=1)


class CycleResult(BaseModel):
    cycle_id: str
    symbol: str
    action: Action
    confidence: Decimal
    price_change: Decimal
    proposed_notional: Decimal
    risk_approved: bool
    simulated_cash: Decimal
    simulated_exposure: Decimal
    stages: list[str]
    lesson: str
