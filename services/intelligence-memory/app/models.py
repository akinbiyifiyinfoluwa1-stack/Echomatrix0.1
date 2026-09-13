"""Persistent intelligence-memory contracts for observations, decisions, outcomes, and lessons."""
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    OBSERVATION = "observation"
    DECISION = "decision"
    OUTCOME = "outcome"
    LESSON = "lesson"
    RESEARCH = "research"


class MemoryRecord(BaseModel):
    memory_id: str = Field(min_length=1)
    memory_type: MemoryType
    symbol: str = ""
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    confidence: Decimal = Field(default=Decimal("0.5"), ge=0, le=1)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    source: str = "ecometrics"


class MemoryQuery(BaseModel):
    query: str = Field(min_length=1)
    symbol: str = ""
    memory_type: MemoryType | None = None
    limit: int = Field(default=10, ge=1, le=100)


class LearningRequest(BaseModel):
    symbol: str = Field(min_length=1)
    action: str = Field(min_length=1)
    strategy: str = Field(default="unknown", min_length=1)
    simulated_return: Decimal
    risk_score: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    confidence: Decimal = Field(default=Decimal("0.5"), ge=0, le=1)
    context: str = ""


class LearningResult(BaseModel):
    lesson: MemoryRecord
    adjustment: str
