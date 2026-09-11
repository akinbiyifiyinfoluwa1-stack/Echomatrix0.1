"""Storage abstraction for EchoMatrix.

This first implementation is in-memory so the service can run immediately.
The interface is intentionally compatible with a later PostgreSQL adapter.
"""
from app.models import RecordQuery, RecordType, StoredRecord


class PersistenceStore:
    def __init__(self) -> None:
        self._records: dict[str, StoredRecord] = {}

    def upsert(self, record: StoredRecord) -> StoredRecord:
        self._records[record.record_id] = record
        return record

    def get(self, record_id: str) -> StoredRecord | None:
        return self._records.get(record_id)

    def query(self, request: RecordQuery) -> list[StoredRecord]:
        records = list(self._records.values())
        if request.record_type:
            records = [r for r in records if r.record_type == request.record_type]
        if request.owner_id:
            records = [r for r in records if r.owner_id == request.owner_id]
        if request.symbol:
            records = [r for r in records if r.symbol == request.symbol]
        records.sort(key=lambda r: r.updated_at, reverse=True)
        return records[: request.limit]

    def delete(self, record_id: str) -> bool:
        return self._records.pop(record_id, None) is not None

    def count(self, record_type: RecordType | None = None) -> int:
        if record_type is None:
            return len(self._records)
        return sum(r.record_type == record_type for r in self._records.values())
