"""Outcome-to-learning memory records with bounded updates."""
from collections import defaultdict

class LearningMemory:
    def __init__(self) -> None:
        self.records: list[dict] = []
        self.stats = defaultdict(lambda: {"count": 0, "wins": 0, "pnl": 0.0})

    def record(self, regime: str, strategy: str, model_consensus: str, pnl: float) -> dict:
        key = f"{regime}:{strategy}"
        item = {"regime": regime, "strategy": strategy, "model_consensus": model_consensus, "pnl": round(pnl, 6)}
        self.records.append(item)
        stat = self.stats[key]; stat["count"] += 1; stat["wins"] += int(pnl > 0); stat["pnl"] += pnl
        return {"recorded": True, "memory_size": len(self.records), "key": key, "performance": {"count": stat["count"], "win_rate": round(stat["wins"] / stat["count"], 4), "pnl": round(stat["pnl"], 6)}}

    def recall(self, regime: str, strategy: str) -> dict:
        key = f"{regime}:{strategy}"; stat = self.stats[key]
        return {"key": key, "count": stat["count"], "win_rate": round(stat["wins"] / stat["count"], 4) if stat["count"] else None, "pnl": round(stat["pnl"], 6)}
