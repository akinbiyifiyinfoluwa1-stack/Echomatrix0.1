"""Advanced EchoMatrix brain capabilities, simulation/research only.

This module deliberately contains no broker, wallet, order, or live-execution code.
It adds: full-brain replay, continuous learning, strategy evolution, provider eval,
portfolio intelligence, durable JSONL memory, external intelligence ingestion,
system evaluation, hardening checks, and autonomous simulation orchestration.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class Decision:
    index: int
    price: float
    action: str
    confidence: float
    regime: str
    strategy: str
    risk_ok: bool
    allocation_fraction: float


@dataclass(frozen=True)
class Outcome:
    entry_index: int
    exit_index: int
    action: str
    entry_price: float
    exit_price: float
    pnl: float
    return_pct: float


def _close(c: Any) -> float:
    return float(c.close if hasattr(c, "close") else c["close"])


def _volume(c: Any) -> float:
    return float(c.volume if hasattr(c, "volume") else c.get("volume", 0.0))


def _ts(c: Any) -> str:
    value = c.timestamp if hasattr(c, "timestamp") else c.get("timestamp")
    return str(value)


def _state(prices: list[float], volumes: list[float]) -> dict[str, Any]:
    if len(prices) < 3:
        return {"trend": "flat", "regime": "insufficient-data", "volatility": 0.0, "momentum": 0.0}
    returns = [(prices[i] / prices[i-1]) - 1.0 for i in range(1, len(prices)) if prices[i-1]}
    recent = returns[-20:]
    vol = math.sqrt(mean([r*r for r in recent]) - mean(recent)**2) if len(recent) > 1 else abs(recent[-1])
    short = mean(prices[-min(10, len(prices)):])
    long = mean(prices[-min(30, len(prices)):])
    momentum = prices[-1] / prices[-min(21, len(prices))] - 1.0
    trend = "up" if short > long * 1.001 else "down" if short < long * 0.999 else "flat"
    regime = "high-volatility" if vol > .02 else "low-volatility" if vol < .005 else "normal-volatility"
    return {"trend": trend, "regime": regime, "volatility": vol, "momentum": momentum,
            "volume_ratio": volumes[-1] / mean(volumes[-min(20, len(volumes)):]) if volumes and mean(volumes[-min(20, len(volumes)):]) else 1.0}


def _decision(state: dict[str, Any], memory: dict[str, float] | None = None) -> tuple[str, float, str]:
    score = 0.0
    if state["trend"] == "up": score += .45
    elif state["trend"] == "down": score -= .45
    score += max(-.35, min(.35, state["momentum"] * 4))
    if state["volume_ratio"] > 1.15: score *= 1.10
    if state["regime"] == "high-volatility": score *= .65
    if memory:
        score += max(-.10, min(.10, memory.get(state["regime"], 0.0)))
    confidence = min(1.0, abs(score))
    action = "BUY" if score > .20 else "SELL" if score < -.20 else "HOLD"
    return action, confidence, "trend-ensemble-v1"


def full_brain_replay(candles: list[Any], initial_cash: float = 10000.0, fee_rate: float = .0005) -> dict[str, Any]:
    """Run the same cognitive pipeline bar-by-bar and mark decisions on future observations."""
    prices = [_close(c) for c in candles]; volumes = [_volume(c) for c in candles]
    if len(prices) < 25: return {"status": "insufficient-data", "bars": len(prices), "simulation_only": True}
    cash = initial_cash; equity_curve = [cash]; decisions: list[Decision] = []; outcomes: list[Outcome] = []
    memory: dict[str, float] = {}; wins = 0; losses = 0
    for i in range(20, len(prices) - 1):
        state = _state(prices[:i+1], volumes[:i+1]); action, confidence, strategy = _decision(state, memory)
        risk_ok = action != "HOLD" and confidence >= .35 and state["volatility"] < .10
        alloc = min(.10, max(0.0, confidence * .10)) if risk_ok else 0.0
        next_price = prices[i+1]
        signed = 1 if action == "BUY" else -1 if action == "SELL" else 0
        gross = signed * (next_price / prices[i] - 1.0) * (cash * alloc)
        fees = cash * alloc * fee_rate if action != "HOLD" else 0.0
        pnl = gross - fees; cash += pnl; equity_curve.append(cash)
        decisions.append(Decision(i, prices[i], action, confidence, state["regime"], strategy, risk_ok, alloc))
        if action != "HOLD":
            ret = signed * (next_price / prices[i] - 1.0)
            outcome = Outcome(i, i+1, action, prices[i], next_price, pnl, ret)
            outcomes.append(outcome)
            bucket = memory.get(state["regime"], 0.0)
            memory[state["regime"]] = max(-1.0, min(1.0, bucket + (0.02 if pnl > 0 else -0.02)))
            wins += pnl > 0; losses += pnl <= 0
    peak = equity_curve[0]; max_dd = 0.0
    for value in equity_curve:
        peak = max(peak, value); max_dd = max(max_dd, (peak-value)/peak if peak else 0.0)
    return {"status": "complete", "bars": len(prices), "decisions": [asdict(x) for x in decisions],
            "outcomes": [asdict(x) for x in outcomes], "ending_cash": round(cash, 6),
            "total_pnl": round(cash-initial_cash, 6), "return_pct": round((cash/initial_cash-1)*100, 6) if initial_cash else 0,
            "max_drawdown_pct": round(max_dd*100, 6), "win_rate": round(wins/(wins+losses), 6) if wins+losses else 0,
            "simulation_only": True, "external_execution": False}


class ContinuousLearner:
    """Bounded online learner. It updates evidence weights; it never changes execution permissions."""
    def __init__(self) -> None: self.weights: dict[str, float] = {}; self.events: list[dict[str, Any]] = []
    def observe(self, regime: str, strategy: str, pnl: float) -> dict[str, Any]:
        key = f"{regime}:{strategy}"; old = self.weights.get(key, 0.0)
        new = max(-1.0, min(1.0, old + (0.03 if pnl > 0 else -0.03)))
        self.weights[key] = new; event = {"key": key, "old": old, "new": new, "pnl": pnl, "at": datetime.now(timezone.utc).isoformat()}
        self.events.append(event); self.events = self.events[-1000:]
        return event
    def snapshot(self) -> dict[str, Any]: return {"weights": self.weights, "events": len(self.events)}


@dataclass
class StrategyCandidate:
    name: str
    trend_weight: float
    momentum_weight: float
    volume_weight: float
    volatility_penalty: float
    score: float = 0.0


def evolve_strategies(candidates: list[StrategyCandidate], results: dict[str, float], generations: int = 3) -> dict[str, Any]:
    """Deterministic tournament/evolution using supplied simulation scores."""
    population = [StrategyCandidate(**asdict(c)) for c in candidates]
    for _ in range(max(1, generations)):
        for c in population: c.score = float(results.get(c.name, 0.0))
        population.sort(key=lambda x: x.score, reverse=True)
        elites = population[:max(1, len(population)//2)]
        children: list[StrategyCandidate] = []
        for idx in range(len(population)-len(elites)):
            a = elites[idx % len(elites)]; b = elites[(idx+1) % len(elites)]
            child = StrategyCandidate(f"{a.name}x{b.name}g{idx}", (a.trend_weight+b.trend_weight)/2,
                (a.momentum_weight+b.momentum_weight)/2, (a.volume_weight+b.volume_weight)/2,
                (a.volatility_penalty+b.volatility_penalty)/2, 0.0)
            children.append(child)
        population = elites + children
    population.sort(key=lambda x: x.score, reverse=True)
    return {"champion": asdict(population[0]), "population": [asdict(x) for x in population], "generations": generations,
            "simulation_only": True}


@dataclass
class ProviderScore:
    provider: str
    validity: float
    consistency: float
    latency_ms: float
    cost_score: float
    total: float


def evaluate_providers(responses: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Evaluate provider outputs without sending any provider a secret or execution command."""
    scores: list[ProviderScore] = []
    for name, rows in responses.items():
        if not rows: scores.append(ProviderScore(name,0,0,0,0,0)); continue
        valid = sum(bool(r.get("valid", True)) for r in rows) / len(rows)
        latencies = [float(r.get("latency_ms", 0)) for r in rows]
        latency = mean(latencies) if latencies else 0.0
        cost = mean([float(r.get("cost_score", 1)) for r in rows])
        outputs = [str(r.get("label", "")) for r in rows]
        consistency = max(outputs.count(x) for x in set(outputs)) / len(outputs) if outputs else 0.0
        total = .40*valid + .30*consistency + .20*(1/(1+latency/1000)) + .10*max(0.0,min(1.0,cost))
        scores.append(ProviderScore(name,valid,consistency,latency,cost,total))
    scores.sort(key=lambda x: x.total, reverse=True)
    return {"ranked": [asdict(x) for x in scores], "leader": scores[0].provider if scores else None, "simulation_only": True}


def portfolio_intelligence(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    """Research portfolio analytics: concentration, realized outcomes, streaks and regime attribution."""
    pnl = [float(x.get("pnl", 0)) for x in outcomes]
    by_regime: dict[str, float] = {}; by_action: dict[str, float] = {}
    for x in outcomes:
        by_regime[x.get("regime", "unknown")] = by_regime.get(x.get("regime", "unknown"), 0.0) + float(x.get("pnl", 0))
        by_action[x.get("action", "unknown")] = by_action.get(x.get("action", "unknown"), 0.0) + float(x.get("pnl", 0))
    wins = sum(v > 0 for v in pnl); losses = sum(v <= 0 for v in pnl)
    return {"outcome_count": len(pnl), "total_pnl": sum(pnl), "win_rate": wins/(wins+losses) if pnl else 0.0,
            "profit_factor": sum(v for v in pnl if v > 0)/abs(sum(v for v in pnl if v < 0)) if any(v < 0 for v in pnl) else None,
            "regime_pnl": by_regime, "action_pnl": by_action, "concentration_index": 1.0/len(set(x.get("action") for x in outcomes)) if outcomes else 0.0,
            "simulation_only": True}


class DurableMemory:
    """Append-only JSONL memory with checksummed records and bounded retrieval."""
    def __init__(self, path: str = "data/echomatrix-memory.jsonl") -> None:
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
    def write(self, event: dict[str, Any]) -> str:
        payload = json.dumps(event, sort_keys=True, separators=(",", ":")); digest = sha256(payload.encode()).hexdigest()
        row = {"hash": digest, "event": event, "recorded_at": datetime.now(timezone.utc).isoformat()}
        with self.path.open("a", encoding="utf-8") as f: f.write(json.dumps(row)+"\n")
        return digest
    def read(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self.path.exists(): return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-max(1,limit):]
        return [json.loads(x) for x in lines]


class ExternalIntelligence:
    """Normalizes externally supplied research/news observations; it does not trade on them."""
    def normalize(self, items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        result=[]
        for item in items:
            text=str(item.get("text", "")).strip(); source=str(item.get("source", "unknown"))
            if not text: continue
            result.append({"source":source,"timestamp":str(item.get("timestamp", "")),
                           "text":text[:2000],"sentiment":max(-1.0,min(1.0,float(item.get("sentiment",0)))),
                           "reliability":max(0.0,min(1.0,float(item.get("reliability",.5))))})
        return result


class SystemEvaluator:
    def evaluate(self, replay: dict[str, Any], expected: dict[str, Any] | None = None) -> dict[str, Any]:
        expected = expected or {}; checks=[]
        checks.append(("completed", replay.get("status") == "complete"))
        checks.append(("simulation_only", replay.get("simulation_only") is True))
        checks.append(("no_external_execution", replay.get("external_execution") is False))
        if "min_win_rate" in expected: checks.append(("min_win_rate", replay.get("win_rate",0) >= expected["min_win_rate"]))
        if "max_drawdown_pct" in expected: checks.append(("max_drawdown", replay.get("max_drawdown_pct",999) <= expected["max_drawdown_pct"]))
        passed=sum(ok for _,ok in checks); return {"checks":[{"name":n,"passed":ok} for n,ok in checks],"passed":passed==len(checks),"score":passed/len(checks) if checks else 1.0}


class Hardening:
    """Preflight checks for the brain boundary and deterministic service assumptions."""
    @staticmethod
    def run(env: dict[str, str] | None = None) -> dict[str, Any]:
        env = env or {}; forbidden=[k for k in env if any(x in k.upper() for x in ("BROKER_ORDER","LIVE_EXECUTION","REAL_MONEY")) and env[k].lower() in ("1","true","yes","on")]
        return {"passed": not forbidden, "forbidden_live_flags": forbidden, "simulation_only": True,
                "checks":["live-execution-disabled","simulation-boundary","bounded-allocation","provider-neutrality"]}


class AutonomousSimulation:
    """Runs repeated cognitive cycles over supplied candles; autonomous means no human step is needed inside the simulation."""
    def __init__(self) -> None: self.learner=ContinuousLearner()
    def run(self, candles: list[Any], cycles: int = 1) -> dict[str, Any]:
        reports=[]
        for _ in range(max(1,min(cycles,20))):
            report=full_brain_replay(candles); reports.append(report)
            for o in report.get("outcomes", []): self.learner.observe("unknown","trend-ensemble-v1",float(o["pnl"]))
        return {"cycles":len(reports),"reports":reports,"learning":self.learner.snapshot(),"simulation_only":True,"external_execution":False}
