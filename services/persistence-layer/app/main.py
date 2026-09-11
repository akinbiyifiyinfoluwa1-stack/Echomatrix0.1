"""EchoMatrix persistence API with SQL-backed storage."""
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.db_models import AuditEvent, Record
from app.models import RecordQuery, StoredRecord
from app.sql_store import SQLPersistenceStore

app = FastAPI(
    title="EchoMatrix Persistence Layer",
    description="Persistent storage for EchoMatrix financial intelligence and wealth services.",
    version="0.2.0",
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "echomatrix-persistence-layer",
        "storage": "sql",
        "message": "Give EchoMatrix memory that survives a process restart.",
    }


@app.get("/health", tags=["meta"])
def health(db: Session = Depends(get_db)) -> dict[str, str | int]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "service": "persistence-layer", "records": db.query(Record).count()}


@app.post("/records", response_model=StoredRecord, tags=["records"])
def upsert_record(record: StoredRecord, db: Session = Depends(get_db)) -> StoredRecord:
    store = SQLPersistenceStore(db)
    result = store.upsert(record)
    store.audit(record.record_id, "record.upsert", record.owner_id, "upsert", record.record_type.value)
    return result


@app.get("/records/{record_id}", response_model=StoredRecord, tags=["records"])
def get_record(record_id: str, db: Session = Depends(get_db)) -> StoredRecord:
    record = SQLPersistenceStore(db).get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="record not found")
    return record


@app.post("/records/query", response_model=list[StoredRecord], tags=["records"])
def query_records(request: RecordQuery, db: Session = Depends(get_db)) -> list[StoredRecord]:
    return SQLPersistenceStore(db).query(request)


@app.delete("/records/{record_id}", tags=["records"])
def delete_record(record_id: str, db: Session = Depends(get_db)) -> dict[str, bool]:
    store = SQLPersistenceStore(db)
    deleted = store.delete(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="record not found")
    store.audit(record_id, "record.delete", "system", "delete")
    return {"deleted": True}


@app.get("/audit/{correlation_id}", tags=["audit"])
def audit_log(correlation_id: str, db: Session = Depends(get_db)) -> list[dict]:
    events = db.query(AuditEvent).filter(AuditEvent.correlation_id == correlation_id).order_by(AuditEvent.created_at.asc()).all()
    return [
        {
            "correlation_id": event.correlation_id,
            "event_type": event.event_type,
            "actor": event.actor,
            "action": event.action,
            "details": event.details,
            "created_at": event.created_at,
        }
        for event in events
    ]


@app.post("/demo/record", response_model=StoredRecord, tags=["demo"])
def demo_record(db: Session = Depends(get_db)) -> StoredRecord:
    now = datetime.now(timezone.utc)
    record = StoredRecord(
        record_id=str(uuid4()),
        record_type="decision",
        owner_id="demo-user",
        symbol="BTC/USD",
        payload={"action": "hold", "reason": "demo persistent record"},
        created_at=now,
        updated_at=now,
    )
    return SQLPersistenceStore(db).upsert(record)
