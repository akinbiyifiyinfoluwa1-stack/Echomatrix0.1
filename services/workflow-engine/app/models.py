"""Event and workflow contracts for the EchoMatrix brain."""
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    MARKET_UPDATE = "market.update"
    RESEARCH_READY = "research.ready"
    STRATEGY_SIGNAL = "strategy.signal"
    AI_ANALYSIS = "ai.analysis"
    RISK_DECISION = "risk.decision"
    CAPITAL_ALLOCATION = "capital.allocation"
    TRADE_DECISION = "trade.decision"
    SIMULATION_FILL = "simulation.fill"
    OUTCOME_RECORDED = "outcome.recorded"
    MEMORY_WRITTEN = "memory.written"


class WorkflowStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    source: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowRun(BaseModel):
    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    correlation_id: str
    status: WorkflowStatus = WorkflowStatus.CREATED
    events: list[EventEnvelope] = Field(default_factory=list)
    current_stage: str = "created"
    error: str | None = None
