"""Small in-process memory store used as the first persistence contract.

The interface is intentionally storage-agnostic so PostgreSQL/vector storage can
replace this implementation later without changing callers.
"""
from app.models import MemoryQuery, MemoryRecord


class MemoryStore:
    def __init__(self) -> None:
        self._records: list[MemoryRecord] = []

    def write(self, record: MemoryRecord) -> MemoryRecord:
        self._records.append(record)
        return record

    def search(self, query: MemoryQuery) -> list[MemoryRecord]:
        terms = query.query.lower().split()
        candidates = self._records

        if query.symbol:
            candidates = [item for item in candidates if item.symbol.lower() == query.symbol.lower()]
        if query.memory_type:
            candidates = [item for item in candidates if item.memory_type == query.memory_type]

        scored: list[tuple[int, MemoryRecord]] = []
        for record in candidates:
            haystack = " ".join(
                [record.title, record.content, record.symbol, *record.tags]
            ).lower()
            score = sum(1 for term in terms if term in haystack)
            if score:
                scored.append((score, record))

        scored.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
        return [record for _, record in scored[: query.limit]]

    def all(self) -> list[MemoryRecord]:
        return list(self._records)
