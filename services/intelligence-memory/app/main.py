"""Intelligence memory API: the system's explicit learning ledger."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import os

import httpx
from fastapi import FastAPI

from app.models import LearningRequest, LearningResult, MemoryQuery, MemoryRecord, MemoryType
from app.store import MemoryStore

app = FastAPI(
    title="EchoMatrix Intelligence Memory",
    description="Memory layer for observations, decisions, outcomes, research, and lessons.",
    version="0.3.0",
)

store = MemoryStore()
PERSISTENCE_URL = os.getenv("PERSISTENCE_URL", "http://persistence-layer:8000").rstrip("/")


def _persistence_payload(record: MemoryRecord) -> dict:
    now = record.created_at.isoformat()
    return {
        "record_id": f"memory:{record.memory_id}",
        "record_type": "memory",
        "owner_id": "intelligence-memory",
        "symbol": record.symbol,
        "payload": record.model_dump(mode="json"),
        "created_at": now,
        "updated_at": now,
    }


async def _persist(record: MemoryRecord) -> bool:
    """Mirror memory to the SQL persistence service without making it a hard dependency."""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.post(f"{PERSISTENCE_URL}/records", json=_persistence_payload(record))
            response.raise_for_status()
        return True
    except Exception:
        return False


async def _hydrate() -> int:
    """Restore durable memory into the fast in-process search cache."""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.post(
                f"{PERSISTENCE_URL}/records/query",
                json={"record_type": "memory", "owner_id": "intelligence-memory", "limit": 1000},
            )
            response.raise_for_status()
            rows = response.json()
        records: list[MemoryRecord] = []
        for row in rows:
            payload = row.get("payload", {})
            if not payload:
                continue
            try:
                records.append(MemoryRecord.model_validate(payload))
            except Exception:
                continue
        return store.load(records)
    except Exception:
        return 0


def _learning_adjustment(request: LearningRequest) -> str:
    if request.simulated_return > 0 and request.risk_score <= Decimal("0.50"):
        return "retain-context"
    if request.simulated_return > 0 and request.risk_score > Decimal("0.50"):
        return "retain-result-reduce-risk"
    if request.simulated_return <= 0 and request.risk_score > Decimal("0.50"):
        return "reduce-risk-and-require-more-confirmation"
    return "review-context-before-repeating"


@app.on_event("startup")
async def startup() -> None:
    await _hydrate()


@app.get("/", tags=["meta"])
def root() -> dict[str, str | int]:
    return {
        "service": "echomatrix-intelligence-memory",
        "message": "Remember what the brain observed, decided, and learned.",
        "cached_records": len(store.all()),
        "durable_backend": PERSISTENCE_URL,
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str | int]:
    return {"status": "ok", "service": "intelligence-memory", "records": len(store.all())}


@app.post("/memories", response_model=MemoryRecord, tags=["memory"])
async def write_memory(record: MemoryRecord) -> MemoryRecord:
    store.write(record)
    await _persist(record)
    return record


@app.post("/memories/search", response_model=list[MemoryRecord], tags=["memory"])
def search_memory(query: MemoryQuery) -> list[MemoryRecord]:
    return store.search(query)


@app.get("/memories", response_model=list[MemoryRecord], tags=["memory"])
def list_memories() -> list[MemoryRecord]:
    return store.all()


@app.post("/learn", response_model=LearningResult, tags=["learning"])
async def learn(request: LearningRequest) -> LearningResult:
    adjustment = _learning_adjustment(request)
    lesson = MemoryRecord(
        memory_id=str(uuid4()),
        memory_type=MemoryType.LESSON,
        symbol=request.symbol,
        title=f"Learning lesson: {request.strategy}",
        content=(
            f"Action={request.action}; simulated_return={request.simulated_return}; "
            f"risk_score={request.risk_score}; confidence={request.confidence}; "
            f"context={request.context or 'none'}. Adjustment={adjustment}."
        ),
        confidence=request.confidence,
        tags=["lesson", "learning-loop", request.strategy, adjustment],
        created_at=datetime.now(timezone.utc),
        source="intelligence-memory-learning-loop",
    )
    store.write(lesson)
    await _persist(lesson)
    return LearningResult(lesson=lesson, adjustment=adjustment)


@app.post("/demo/lesson", response_model=MemoryRecord, tags=["demo"])
async def demo_lesson() -> MemoryRecord:
    record = MemoryRecord(
        memory_id=str(uuid4()),
        memory_type=MemoryType.LESSON,
        symbol="BTC/USD",
        title="Momentum needs confirmation",
        content="A strong short-term price move should be evaluated with volume and risk context before capital is allocated.",
        confidence=Decimal("0.85"),
        tags=["momentum", "volume", "risk"],
        created_at=datetime.now(timezone.utc),
        source="demo",
    )
    store.write(record)
    await _persist(record)
    return record
