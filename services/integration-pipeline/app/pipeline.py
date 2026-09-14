"""HTTP coordinator connecting EchoMatrix services end-to-end.

The pipeline is simulation-first: risk is authoritative before AI interpretation,
paper fills are marked to market, and the resulting outcome feeds the learning loop.
No broker, exchange, wallet, or real-money execution is performed.
"""
import os
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import httpx

from app.models import PipelineRequest, PipelineResult
from app.outcome import evaluate_outcome


class PipelineError(RuntimeError):
    pass


class EchoMatrixPipeline:
    def __init__(self) -> None:
        self.services = {
            "market-data": os.getenv("MARKET_DATA_URL", "http://market-data:8000"),
            "research": os.getenv("RESEARCH_INTELLIGENCE_URL", "http://research-intelligence:8000"),
            "strategy": os.getenv("STRATEGY_ENGINE_URL", "http://strategy-engine:8000"),
            "ai": os.getenv("AI_CORE_URL", "http://ai-core:8000"),
            "risk": os.getenv("RISK_ENGINE_URL", "http://risk-engine:8000"),
            "allocation": os.getenv("CAPITAL_ALLOCATION_URL", "http://capital-allocation-engine:8000"),
            "orchestration": os.getenv("ORCHESTRATION_URL", "http://orchestration-engine:8000"),
            "simulation": os.getenv("SIMULATION_ENGINE_URL", "http://simulation-engine:8000"),
            "portfolio": os.getenv("PORTFOLIO_ENGINE_URL", "http://portfolio-engine:8000"),
            "workflow": os.getenv("WORKFLOW_ENGINE_URL", "http://workflow-engine:8000"),
            "persistence": os.getenv("PERSISTENCE_URL", "http://persistence-layer:8000"),
            "memory": os.getenv("INTELLIGENCE_MEMORY_URL", "http://intelligence-memory:8000"),
        }

    async def _get(self, client: httpx.AsyncClient, service: str, path: str, params: dict | None = None) -> dict:
        response = await client.get(f"{self.services[service]}{path}", params=params)
        response.raise_for_status()
        return response.json()

    async def _post(self, client: httpx.AsyncClient, service: str, path: str, payload: dict) -> dict:
        response = await client.post(f"{self.services[service]}{path}", json=payload)
        response.raise_for_status()
        return response.json()

    async def run(self, request: PipelineRequest) -> PipelineResult:
        correlation_id = str(uuid4())
        stages: list[str] = []
        simulation_fill = None
        portfolio_state = None
        research = None
        ai_analysis = None
        memory_context: list[dict] = []
        outcome = None
        learning_result = None
        persisted_id = None
        audit_id = None

        async with httpx.AsyncClient(timeout=30) as client:
            await self._get(client, "market-data", "/health")
            stages.append("market-data")

            workflow = await self._post(client, "workflow", "/workflows", {})
            stages.append("workflow")

            portfolio_state = await self._post(client, "portfolio", "/accounts", {
                "account_id": request.account_id,
                "initial_cash": str(request.initial_cash),
            })
            stages.append("portfolio-state")

            observation = {
                "symbol": request.symbol,
                "price": str(request.price),
                "previous_price": str(request.previous_price),
                "volume": str(request.volume),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            strategy = await self._post(client, "strategy", "/ensemble", observation)
            stages.append("strategy-ensemble")

            research = await self._post(client, "research", "/market-context", {
                "symbol": request.symbol,
                "price": str(request.price),
                "previous_price": str(request.previous_price),
                "volume": str(request.volume),
                "source": "integration-pipeline-observation",
            })
            stages.append("research-context")

            # Memory is recalled before interpretation so the AI can compare the current
            # observation with prior simulated decisions and lessons.
            memory_context = await self._post(client, "memory", "/memories/search", {
                "query": f"{request.symbol} strategy research risk outcome",
                "symbol": request.symbol,
                "limit": 10,
            })
            stages.append("memory-recall")

            # Risk is evaluated BEFORE AI interpretation. The risk engine remains the
            # authoritative gate, and AI receives the actual risk decision rather than
            # a pre-risk approximation.
            risk = await self._post(client, "risk", "/evaluate", {
                "portfolio_equity": str(request.portfolio_equity),
                "current_exposure": str(request.current_exposure),
                "proposed_position_value": str(request.proposed_position_value),
                "stop_distance": str(request.stop_distance),
                "entry_price": str(request.price),
                "daily_drawdown": str(request.daily_drawdown),
            })
            stages.append("risk")

            if request.use_ai:
                ai_analysis = await self._post(client, "ai", "/analyze-context", {
                    "observation": observation,
                    "strategy": strategy,
                    "research": research,
                    "risk": risk,
                    "memory": memory_context,
                    "provider": "gemini",
                    "temperature": 0.2,
                })
            else:
                ai_analysis = {"provider": "disabled", "analysis": "AI disabled for this run"}
            stages.append("ai-core")

            # The deterministic orchestration layer remains the action authority. AI
            # supplies context; it does not get a direct execution path.
            allocation = await self._post(client, "allocation", "/allocate", {
                "available_capital": str(request.portfolio_equity),
                "proposed_position_value": str(request.proposed_position_value),
                "allowed_position_value": str(risk["allowed_position_value"]),
                "confidence": str(request.ai_confidence),
                "current_exposure": str(request.current_exposure),
                "max_portfolio_exposure": "7000",
                "allocation_floor": "0.25",
                "allocation_ceiling": "0.75",
            })
            stages.append("capital-allocation")

            decision = await self._post(client, "orchestration", "/decision", {
                "symbol": request.symbol,
                "price": str(request.price),
                "previous_price": str(request.previous_price),
                "volume": str(request.volume),
                "portfolio_equity": str(request.portfolio_equity),
                "current_exposure": str(request.current_exposure),
                "proposed_position_value": str(allocation["allocated_capital"]),
                "stop_distance": str(request.stop_distance),
                "daily_drawdown": str(request.daily_drawdown),
                "research_confidence": str(research["confidence"]),
                "ai_confidence": str(request.ai_confidence),
            })
            stages.append("decision")

            allocated_value = Decimal(str(decision["allowed_position_value"]))
            quantity = Decimal("0")
            entry_fee = Decimal("0")
            if request.simulate and decision["action"] in {"buy", "sell"} and allocated_value > 0:
                quantity = allocated_value / request.price
                entry_fee = quantity * request.price * request.fee_rate
                simulation_fill = await self._post(client, "simulation", "/simulate", {
                    "account_id": request.account_id,
                    "initial_cash": str(request.initial_cash),
                    "instrument_symbol": request.symbol,
                    "side": decision["action"],
                    "quantity": str(quantity),
                    "market_price": str(request.price),
                    "fee_rate": str(request.fee_rate),
                })
                stages.append("simulation")

                portfolio_state = await self._post(client, "portfolio", f"/accounts/{request.account_id}/fills", {
                    "symbol": request.symbol,
                    "asset_class": "crypto" if "/" in request.symbol and request.symbol.endswith("USD") else "other",
                    "side": decision["action"],
                    "quantity": str(quantity),
                    "price": str(request.price),
                    "fee": str(entry_fee),
                    "mark_price": str(request.price),
                })
                stages.append("portfolio-update")
            else:
                portfolio_state = await self._get(
                    client,
                    "portfolio",
                    f"/accounts/{request.account_id}",
                    params={"initial_cash": str(request.initial_cash)},
                )

            # Outcome evaluation is deliberately mark-to-market. A caller may provide a
            # later simulated mark; otherwise we record an entry mark and avoid inventing
            # future market data.
            if simulation_fill:
                mark_price = request.mark_price or request.price
                outcome = evaluate_outcome(
                    action=decision["action"],
                    entry_price=request.price,
                    mark_price=mark_price,
                    quantity=quantity,
                    entry_fee=entry_fee,
                    exit_fee_rate=request.fee_rate,
                    risk_amount=Decimal(str(decision["risk_amount"])),
                )
                if request.mark_price is None:
                    outcome["status"] = "awaiting-future-mark"
                stages.append("outcome-evaluated")

            # Write the research memory explicitly; outcome and decision memories are
            # followed by a learning call that turns results into an adjustment.
            await self._post(client, "memory", "/memories", {
                "memory_id": str(uuid4()),
                "symbol": request.symbol,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "integration-pipeline",
                "memory_type": "research",
                "title": f"Research context: {request.symbol}",
                "content": str(research),
                "confidence": str(research["confidence"]),
                "tags": ["research", "context"],
            })
            await self._post(client, "memory", "/memories", {
                "memory_id": str(uuid4()),
                "symbol": request.symbol,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "integration-pipeline",
                "memory_type": "observation",
                "title": f"Market observation: {request.symbol}",
                "content": f"Price={request.price}; previous_price={request.previous_price}; volume={request.volume}.",
                "confidence": str(research["confidence"]),
                "tags": ["market", "observation"],
            })
            await self._post(client, "memory", "/memories", {
                "memory_id": str(uuid4()),
                "symbol": request.symbol,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "integration-pipeline",
                "memory_type": "decision",
                "title": f"Decision: {decision['action']} {request.symbol}",
                "content": f"Action={decision['action']}; confidence={decision['confidence']}; allocated_value={allocated_value}; strategy={strategy['strategy']}; risk={risk}.",
                "confidence": str(decision["confidence"]),
                "tags": ["decision", "strategy", "risk", "allocation"],
            })
            if outcome:
                await self._post(client, "memory", "/memories", {
                    "memory_id": str(uuid4()),
                    "symbol": request.symbol,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "source": "integration-pipeline",
                    "memory_type": "outcome",
                    "title": f"Simulated outcome: {request.symbol}",
                    "content": str(outcome),
                    "confidence": str(decision["confidence"]),
                    "tags": ["outcome", "simulation", "mark-to-market"],
                })
            stages.append("intelligence-memory")

            # Learning consumes the actual simulated result and risk score. If no later
            # mark exists yet, the lesson explicitly knows the outcome is provisional.
            simulated_return = Decimal(str(outcome["return_pct"])) if outcome else Decimal("0")
            learning_result = await self._post(client, "memory", "/learn", {
                "symbol": request.symbol,
                "action": decision["action"],
                "strategy": strategy["strategy"],
                "simulated_return": str(simulated_return),
                "risk_score": str(risk["risk_score"]),
                "confidence": str(decision["confidence"]),
                "context": f"outcome={outcome}; ai={ai_analysis}; memory_items={len(memory_context)}",
            })
            stages.append("learning")

            if request.persist:
                persisted_id = str(uuid4())
                now = datetime.now(timezone.utc).isoformat()
                stored = await self._post(client, "persistence", "/records", {
                    "record_id": persisted_id,
                    "record_type": "pipeline_run",
                    "owner_id": "system",
                    "symbol": request.symbol,
                    "payload": {
                        "correlation_id": correlation_id,
                        "observation": observation,
                        "memory_context": memory_context,
                        "strategy": strategy,
                        "research": research,
                        "risk": risk,
                        "ai_analysis": ai_analysis,
                        "allocation": allocation,
                        "decision": decision,
                        "simulation_fill": simulation_fill,
                        "outcome": outcome,
                        "learning_result": learning_result,
                        "portfolio_state": portfolio_state,
                    },
                    "created_at": now,
                    "updated_at": now,
                })
                audit_id = stored["record_id"]
                stages.append("persistence")

            events = [
                ("market.update", "market-data"),
                ("strategy.signal", "strategy"),
                ("research.ready", "research"),
                ("memory.recalled", "intelligence-memory"),
                ("risk.decision", "risk"),
                ("ai.analysis", "ai-core"),
                ("capital.allocation", "capital-allocation"),
                ("trade.decision", "orchestration"),
            ]
            if simulation_fill:
                events.append(("simulation.fill", "simulation"))
            events.append(("outcome.recorded", "integration-pipeline"))
            events.append(("memory.written", "intelligence-memory"))
            events.append(("learning.updated", "intelligence-memory"))

            for event_type, source in events:
                await self._post(client, "workflow", f"/workflows/{workflow['workflow_id']}/events", {
                    "correlation_id": workflow["correlation_id"],
                    "event_type": event_type,
                    "source": source,
                    "payload": {
                        "symbol": request.symbol,
                        "correlation_id": correlation_id,
                        "account_id": request.account_id,
                    },
                })
            stages.append("workflow-events")

        return PipelineResult(
            correlation_id=correlation_id,
            symbol=request.symbol,
            action=decision["action"],
            confidence=Decimal(str(decision["confidence"])),
            allocated_value=allocated_value,
            risk_amount=Decimal(str(decision["risk_amount"])),
            stages_completed=stages,
            strategy=strategy,
            research=research,
            memory_context=memory_context,
            ai_analysis=ai_analysis,
            risk_decision=risk,
            allocation_decision=allocation,
            orchestration_decision=decision,
            persisted_record_id=persisted_id,
            simulation_fill=simulation_fill,
            outcome=outcome,
            learning_result=learning_result,
            portfolio_state=portfolio_state,
            audit_record_id=audit_id,
        )
