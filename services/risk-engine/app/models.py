"""Risk-domain models used to evaluate capital before simulation."""
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class RiskStatus(str, Enum):
    APPROVED = "approved"
    BLOCKED = "blocked"
    REDUCED = "reduced"


class RiskLimits(BaseModel):
    max_position_value: Decimal = Field(gt=0)
    max_portfolio_exposure: Decimal = Field(gt=0)
    max_risk_per_trade: Decimal = Field(gt=0, le=1)
    max_drawdown: Decimal = Field(gt=0, le=1)


class RiskRequest(BaseModel):
    portfolio_equity: Decimal = Field(gt=0)
    current_exposure: Decimal = Field(ge=0)
    proposed_position_value: Decimal = Field(gt=0)
    stop_distance: Decimal = Field(gt=0)
    entry_price: Decimal = Field(gt=0)
    daily_drawdown: Decimal = Field(ge=0, le=1)


class RiskDecision(BaseModel):
    status: RiskStatus
    allowed_position_value: Decimal = Field(ge=0)
    risk_amount: Decimal = Field(ge=0)
    portfolio_exposure_after: Decimal = Field(ge=0)
    reasons: list[str] = Field(default_factory=list)
    risk_utilization: Decimal = Field(default=Decimal("0"), ge=0)
    exposure_utilization_after: Decimal = Field(default=Decimal("0"), ge=0)
    drawdown_utilization: Decimal = Field(default=Decimal("0"), ge=0)
    risk_score: Decimal = Field(default=Decimal("0"), ge=0, le=1)
