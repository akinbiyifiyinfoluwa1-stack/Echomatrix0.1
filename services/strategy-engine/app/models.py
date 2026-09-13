"""Strategy-domain models for market analysis and trade proposals."""
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class Signal(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class MarketSnapshot(BaseModel):
    symbol: str = Field(min_length=1)
    price: Decimal = Field(gt=0)
    previous_price: Decimal = Field(gt=0)
    volume: Decimal = Field(default=Decimal("0"), ge=0)
    timestamp: datetime


class StrategyConfig(BaseModel):
    name: str = Field(min_length=1)
    momentum_threshold: Decimal = Field(gt=0)
    minimum_volume: Decimal = Field(ge=0)


class TradeProposal(BaseModel):
    strategy: str
    symbol: str
    signal: Signal
    confidence: Decimal = Field(ge=0, le=1)
    reference_price: Decimal = Field(gt=0)
    rationale: list[str] = Field(default_factory=list)
    timestamp: datetime


class StrategyComponent(BaseModel):
    name: str
    signal: Signal
    score: Decimal = Field(ge=-1, le=1)
    confidence: Decimal = Field(ge=0, le=1)
    rationale: str


class StrategyEnsembleResult(BaseModel):
    symbol: str
    signal: Signal
    confidence: Decimal = Field(ge=0, le=1)
    composite_score: Decimal = Field(ge=-1, le=1)
    regime: str
    components: list[StrategyComponent] = Field(default_factory=list)
    proposal: TradeProposal
    timestamp: datetime
