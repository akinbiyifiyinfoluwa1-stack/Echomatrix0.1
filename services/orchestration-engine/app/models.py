"""Contracts for the Ecometrics cross-service decision pipeline."""
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class DecisionAction(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    BLOCK = "block"


class PipelineRequest(BaseModel):
    symbol: str = Field(min_length=1)
    price: Decimal = Field(gt=0)
    previous_price: Decimal = Field(gt=0)
    volume: Decimal = Field(ge=0)
    portfolio_equity: Decimal = Field(gt=0)
    current_exposure: Decimal = Field(ge=0)
    proposed_position_value: Decimal = Field(gt=0)
    stop_distance: Decimal = Field(gt=0)
    daily_drawdown: Decimal = Field(ge=0, le=1)
    research_confidence: Decimal = Field(default=Decimal("0.5"), ge=0, le=1)
    ai_confidence: Decimal = Field(default=Decimal("0.5"), ge=0, le=1)


class PipelineDecision(BaseModel):
    symbol: str
    action: DecisionAction
    confidence: Decimal = Field(ge=0, le=1)
    proposed_position_value: Decimal = Field(ge=0)
    allowed_position_value: Decimal = Field(ge=0)
    risk_amount: Decimal = Field(ge=0)
    portfolio_exposure_after: Decimal = Field(ge=0)
    reasons: list[str] = Field(default_factory=list)
    stages: list[str] = Field(default_factory=list)
