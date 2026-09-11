"""Capital allocation contracts for converting approved opportunities into allocations."""
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class AllocationAction(str, Enum):
    ALLOCATE = "allocate"
    REDUCE = "reduce"
    HOLD = "hold"


class AllocationRequest(BaseModel):
    available_capital: Decimal = Field(gt=0)
    proposed_position_value: Decimal = Field(gt=0)
    allowed_position_value: Decimal = Field(ge=0)
    confidence: Decimal = Field(ge=0, le=1)
    current_exposure: Decimal = Field(ge=0)
    max_portfolio_exposure: Decimal = Field(gt=0)
    allocation_floor: Decimal = Field(default=Decimal("0"), ge=0)
    allocation_ceiling: Decimal = Field(default=Decimal("1"), gt=0, le=1)


class AllocationDecision(BaseModel):
    action: AllocationAction
    allocated_capital: Decimal = Field(ge=0)
    allocation_ratio: Decimal = Field(ge=0, le=1)
    projected_exposure: Decimal = Field(ge=0)
    rationale: list[str] = Field(default_factory=list)
