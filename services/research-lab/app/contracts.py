"""Typed contracts for the simulation-only research laboratory."""
from decimal import Decimal
from pydantic import BaseModel, Field

class Candle(BaseModel):
    timestamp: int = Field(ge=0)
    open: Decimal = Field(gt=0)
    high: Decimal = Field(gt=0)
    low: Decimal = Field(gt=0)
    close: Decimal = Field(gt=0)
    volume: Decimal = Field(ge=0)

class ResearchRequest(BaseModel):
    symbol: str = Field(min_length=1)
    candles: list[Candle] = Field(min_length=3)
    initial_cash: Decimal = Field(default=Decimal("10000"), gt=0)
    fee_rate: Decimal = Field(default=Decimal("0.001"), ge=0, le=1)
    allocation_fraction: Decimal = Field(default=Decimal("0.10"), ge=0, le=1)
    threshold: Decimal = Field(default=Decimal("0.005"), ge=0, le=1)

class ExperimentRequest(ResearchRequest):
    thresholds: list[Decimal] = Field(default_factory=lambda: [Decimal("0.003"), Decimal("0.005"), Decimal("0.008")])
    allocations: list[Decimal] = Field(default_factory=lambda: [Decimal("0.05"), Decimal("0.10"), Decimal("0.20")])

class StressRequest(ResearchRequest):
    shock_pct: Decimal = Field(default=Decimal("0.10"), gt=0, lt=1)

class ResearchResponse(BaseModel):
    mode: str
    symbol: str
    report: dict
