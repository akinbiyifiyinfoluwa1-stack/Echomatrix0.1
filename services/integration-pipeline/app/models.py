"""Contracts for the EchoMatrix end-to-end intelligence pipeline."""
from decimal import Decimal

from pydantic import BaseModel, Field


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
    research_confidence: Decimal = Field(default=Decimal("0.8"), ge=0, le=1)
    ai_confidence: Decimal = Field(default=Decimal("0.8"), ge=0, le=1)
    use_ai: bool = True
    simulate: bool = True
    persist: bool = True
    account_id: str = Field(default="pipeline-demo", min_length=1)
    initial_cash: Decimal = Field(default=Decimal("10000"), gt=0)
    fee_rate: Decimal = Field(default=Decimal("0.001"), ge=0, le=1)


class PipelineResult(BaseModel):
    correlation_id: str
    symbol: str
    action: str
    confidence: Decimal
    allocated_value: Decimal
    risk_amount: Decimal
    stages_completed: list[str]
    strategy: dict | None = None
    research: dict | None = None
    ai_analysis: dict | None = None
    risk_decision: dict | None = None
    allocation_decision: dict | None = None
    persisted_record_id: str | None = None
    simulation_fill: dict | None = None
    portfolio_state: dict | None = None
    audit_record_id: str | None = None
