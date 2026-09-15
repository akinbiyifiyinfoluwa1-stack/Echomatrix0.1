"""HTTP coordinator connecting EchoMatrix services end-to-end.

The pipeline calls the domain services in sequence. It is simulation-first:
approved decisions may produce paper fills, but no broker or exchange receives an order.
"""
import os
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import httpx

from app.models import PipelineRequest, PipelineResult
from app.brain_v1 import build_brain_v1_pipeline_record


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
        learning_result = None

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

            try:
                memory_context = await self._post(client, "memory", "/memories/search", {
                    "query": f"{request.symbol} {strategy.get('strategy', 'strategy')} risk lesson outcome",
                    "symbol": request.symbol,
                    "limit": 8,
                })
            except httpx.HTTPError:
                memory_context = []
            stages.append("memory-recall")

            if request.use_ai:
                ai_analysis = await self._post(client, "ai", "/analyze-context", {
                    "provider": "gemini",
                    "observation": observation,
                    "strategy": strategy,
                    "research": research,
                    "risk": {
                        "requested_position_value": str(request.proposed_position_value),
                        "daily_drawdown": str(request.daily_drawdown),
                        "stop_distance": str(request.stop_distance),
                    },
                    "memory": memory_context,
                    "temperature": 0.2,
                })
            else:
                ai_analysis = {"provider": "disabled", "content": "AI disabled for this run"}
            stages.append("ai-core")

            risk = await self._post(client, "risk", "/evaluate", {
                "portfolio_equity": str(request.portfolio_equity),
                "current_exposure": str(request.current_exposure),
                "proposed_position_value": str(request.proposed_position_value),
                "stop_distance": str(request.stop_distance),
                "entry_price": str(request.price),
                "daily_drawdown": str(request.daily_drawdown),
            })
            stages.append("risk")

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
            if request.simulate and decision["action"] in {"buy", "sell"} and allocated_value > 0:
                quantity = allocated_value / request.price
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
                    "fee": str(Decimal(str(quantity)) * request.price * request.fee_rate),
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

            persisted_id = None
            audit_id = None
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
                        "strategy": strategy,
                        "research": research,
                        "ai_analysis": ai_analysis,
                        "risk": risk,
                        "allocation": allocation,
                        "decision": decision,
                        "simulation_fill": simulation_fill,
                        "portfolio_state": portfolio_state,
                        "memory_context": memory_context,
                    },
                    "created_at": now,
                    "updated_at": now,
                })
                audit_id = stored["record_id"]
                stages.append("persistence")

            memory_payloads = [
                {
                    "memory_type": "observation",
                    "title": f"Market observation: {request.symbol}",
                    "content": f"Price={request.price}; previous_price={request.previous_price}; volume={request.volume}.",
                    "confidence": str(research["confidence"]),
                    "tags": ["market", "observation", "research"],
                },
                {
                    "memory_type": "research",
                    "title": f"Research context: {request.symbol}",
                    "content": research.get("summary", "Research context recorded."),
                    "confidence": str(research["confidence"]),
                    "tags": ["research", "context"],
                },
                {
                    "memory_type": "decision",
                    "title": f"Decision: {decision['action']} {request.symbol}",
                    "content": f"Action={decision['action']}; confidence={decision['confidence']}; allocated_value={allocated_value}; strategy={strategy.get('strategy', 'unknown')}.",
                    "confidence": str(decision["confidence"]),
                    "tags": ["decision", "strategy", "risk", "allocation"],
                },
            ]
            if simulation_fill:
                memory_payloads.append({
                    "memory_type": "outcome",
                    "title": f"Simulated outcome: {request.symbol}",
                    "content": f"Simulation fill recorded for {decision['action']} with quantity={quantity} at price={request.price}.",
                    "confidence": str(decision["confidence"]),
                    "tags": ["outcome", "simulation"],
                })

            for memory in memory_payloads:
                await self._post(client, "memory", "/memories", {
                    "memory_id": str(uuid4()),
                    "symbol": request.symbol,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "source": "integration-pipeline",
                    **memory,
                })
            stages.append("intelligence-memory")

            simulated_return = Decimal("0")
            if simulation_fill:
                fill_price = Decimal(str(simulation_fill.get("fill_price", request.price)))
                simulated_return = (request.price - fill_price) / fill_price if fill_price else Decimal("0")
            risk_score = Decimal(str(risk.get("risk_score", "0")))
            learning_result = await self._post(client, "memory", "/learn", {
                "symbol": request.symbol,
                "action": decision["action"],
                "strategy": strategy.get("strategy", "unknown"),
                "simulated_return": str(simulated_return),
                "risk_score": str(risk_score),
                "confidence": str(decision["confidence"]),
                "context": f"risk={risk.get('status')}; memory_recall={len(memory_context)}; correlation={correlation_id}",
            })
            stages.append("learning-loop")

            brain_v1 = build_brain_v1_pipeline_record(
                correlation_id=correlation_id,
                symbol=request.symbol,
                observation=observation,
                strategy=strategy,
                research=research,
                ai_analysis=ai_analysis,
                risk=risk,
                allocation=allocation,
                decision=decision,
                simulation_fill=simulation_fill,
                portfolio_state=portfolio_state,
                learning_result=learning_result,
                memory_context=memory_context,
                persisted_record_id=persisted_id,
            )
            stages.append("brain-v1")

            events = [
                ("market.update", "market-data"),
                ("strategy.signal", "strategy"),
                ("research.ready", "research"),
                ("memory.recalled", "intelligence-memory"),
                ("ai.analysis", "ai-core"),
                ("risk.decision", "risk"),
                ("capital.allocation", "capital-allocation"),
                ("trade.decision", "orchestration"),
                ("brain.v1.completed", "integration-pipeline"),
            ]
            if simulation_fill:
                events.append(("simulation.fill", "simulation"))
                events.append(("outcome.recorded", "portfolio-engine"))
            else:
                events.append(("outcome.recorded", "integration-pipeline"))
            events.extend([
                ("memory.written", "intelligence-memory"),
                ("learning.updated", "intelligence-memory"),
            ])

            for event_type, source in events:
                await self._post(client, "workflow", f"/workflows/{workflow['workflow_id']}/events", {
                    "correlation_id": workflow["correlation_id"],
                    "event_type": event_type,
                    "source": source,
                    "payload": {"symbol": request.symbol, "correlation_id": correlation_id, "account_id": request.account_id},
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
            outcome={"simulated_return": str(simulated_return), "simulation_only": True},
            learning_result=learning_result,
            portfolio_state=portfolio_state,
            audit_record_id=audit_id,
            brain_v1=brain_v1,
        )
