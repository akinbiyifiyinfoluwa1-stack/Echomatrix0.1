"""Intelligence memory API: the system's first explicit learning ledger."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import FastAPI

from app.models import MemoryQuery, MemoryRecord, MemoryType
from app.store import MemoryStore

app = FastAPI(
    title="Ecometrics Intelligence Memory",
    description="Memory layer for observations, decisions, outcomes, research, and lessons.",
    version="0.1.0",
)

store = MemoryStore()


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "ecometrics-intelligence-memory",
        "message": "Remember what the brain observed, decided, and learned.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "intelligence-memory"}


@app.post("/memories", response_model=MemoryRecord, tags=["memory"])
def write_memory(record: MemoryRecord) -> MemoryRecord:
    return store.write(record)


@app.post("/memories/search", response_model=list[MemoryRecord], tags=["memory"])
def search_memory(query: MemoryQuery) -> list[MemoryRecord]:
    return store.search(query)


@app.get("/memories", response_model=list[MemoryRecord], tags=["memory"])
def list_memories() -> list[MemoryRecord]:
    return store.all()


@app.post("/demo/lesson", response_model=MemoryRecord, tags=["demo"])
def demo_lesson() -> MemoryRecord:
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
    return store.write(record)
