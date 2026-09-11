"""Canonical persistence contracts for EchoMatrix."""
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class RecordType(str, Enum):
    ACCOUNT = "account"
    POSITION = "position"
    ORDER = "order"
    FILL = "fill"
    DECISION = "decision"
    MEMORY = "memory"
    RESEARCH = "research"
    WORKFLOW = "workflow"
    AUDIT = "audit"
    PORTFOLIO_STATE = "portfolio_state"
    PIPELINE_RUN = "pipeline_run"


class StoredRecord(BaseModel):
    record_id: str = Field(min_length=1)
    record_type: RecordType
    owner_id: str = "system"
    symbol: str = ""
    payload: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class RecordQuery(BaseModel):
    record_type: RecordType | None = None
    owner_id: str = ""
    symbol: str = ""
    limit: int = Field(default=100, ge=1, le=1000)


class AccountSnapshot(BaseModel):
    account_id: str = Field(min_length=1)
    owner_id: str = "system"
    currency: str = "USD"
    cash: Decimal
    equity: Decimal
    exposure: Decimal = Decimal("0")
    updated_at: datetime
