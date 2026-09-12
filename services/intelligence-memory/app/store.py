"""Memory store with an in-process cache and optional durable persistence mirror."""
from __future__ import annotations

from app.models import MemoryQuery, MemoryRecord


class MemoryStore:
    def __init__(self) -> None:
        self._records: list[MemoryRecord] = []

    def write(self, record: MemoryRecord) -> MemoryRecord:
        self._records = [item for item in self._records if item.memory_id != record.memory_id]
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
            haystack = " ".join([record.title, record.content, record.symbol, *record.tags]).lower()
            score = sum(1 for term in terms if term in haystack)
            if score:
                scored.append((score, record))

        scored.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
        return [record for _, record in scored[: query.limit]]

    def all(self) -> list[MemoryRecord]:
        return sorted(self._records, key=lambda item: item.created_at, reverse=True)

    def load(self, records: list[MemoryRecord]) -> int:
        for record in records:
            self.write(record)
        return len(records)
