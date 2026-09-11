"""EchoMatrix persistence API."""
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.models import RecordQuery, StoredRecord
from app.store import PersistenceStore

app = FastAPI(
    title="EchoMatrix Persistence Layer",
    description="Durable-storage contract for EchoMatrix financial and wealth services.",
    version="0.1.0",
)

store = PersistenceStore()


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "echomatrix-persistence-layer",
        "message": "Give EchoMatrix memory that survives a process restart.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str | int]:
    return {"status": "ok", "service": "persistence-layer", "records": store.count()}


@app.post("/records", response_model=StoredRecord, tags=["records"])
def upsert_record(record: StoredRecord) -> StoredRecord:
    return store.upsert(record)


@app.get("/records/{record_id}", response_model=StoredRecord, tags=["records"])
def get_record(record_id: str) -> StoredRecord:
    record = store.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="record not found")
    return record


@app.post("/records/query", response_model=list[StoredRecord], tags=["records"])
def query_records(request: RecordQuery) -> list[StoredRecord]:
    return store.query(request)


@app.delete("/records/{record_id}", tags=["records"])
def delete_record(record_id: str) -> dict[str, bool]:
    deleted = store.delete(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="record not found")
    return {"deleted": True}


@app.post("/demo/record", response_model=StoredRecord, tags=["demo"])
def demo_record() -> StoredRecord:
    now = datetime.now(timezone.utc)
    return store.upsert(
        StoredRecord(
            record_id=str(uuid4()),
            record_type="decision",
            owner_id="demo-user",
            symbol="BTC/USD",
            payload={"action": "hold", "reason": "demo persistence record"},
            created_at=now,
            updated_at=now,
        )
    )
