"""SQLAlchemy-backed persistence implementation."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models import AuditEvent, Record
from app.models import RecordQuery, StoredRecord


class SQLPersistenceStore:
    def __init__(self, db: Session):
        self.db = db

    def upsert(self, item: StoredRecord) -> StoredRecord:
        row = self.db.scalar(select(Record).where(Record.record_id == item.record_id))
        if row is None:
            row = Record(record_id=item.record_id)
            self.db.add(row)

        row.record_type = item.record_type.value
        row.owner_id = item.owner_id
        row.symbol = item.symbol
        row.payload = item.payload
        row.created_at = item.created_at
        row.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(row)
        return item.model_copy(update={"updated_at": row.updated_at})

    def get(self, record_id: str) -> StoredRecord | None:
        row = self.db.scalar(select(Record).where(Record.record_id == record_id))
        if row is None:
            return None
        return StoredRecord(
            record_id=row.record_id,
            record_type=row.record_type,
            owner_id=row.owner_id,
            symbol=row.symbol,
            payload=row.payload,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def query(self, request: RecordQuery) -> list[StoredRecord]:
        statement = select(Record).order_by(Record.updated_at.desc()).limit(request.limit)
        if request.record_type:
            statement = statement.where(Record.record_type == request.record_type.value)
        if request.owner_id:
            statement = statement.where(Record.owner_id == request.owner_id)
        if request.symbol:
            statement = statement.where(Record.symbol == request.symbol)

        return [
            StoredRecord(
                record_id=row.record_id,
                record_type=row.record_type,
                owner_id=row.owner_id,
                symbol=row.symbol,
                payload=row.payload,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in self.db.scalars(statement)
        ]

    def delete(self, record_id: str) -> bool:
        row = self.db.scalar(select(Record).where(Record.record_id == record_id))
        if row is None:
            return False
        self.db.delete(row)
        self.db.commit()
        return True

    def audit(self, correlation_id: str, event_type: str, actor: str, action: str, details: str = "") -> None:
        self.db.add(AuditEvent(
            correlation_id=correlation_id,
            event_type=event_type,
            actor=actor,
            action=action,
            details=details,
        ))
        self.db.commit()
