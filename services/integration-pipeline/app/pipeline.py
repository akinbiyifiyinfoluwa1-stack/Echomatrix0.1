"""HTTP coordinator connecting EchoMatrix services end-to-end.

The pipeline calls the real domain service contracts in sequence. It is
simulation-first: approved decisions may produce paper fills, but no broker
or exchange receives an order.
"""
import os
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import httpx

from app.models import PipelineRequest, PipelineResult


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

            strategy = await self._post(client, "strategy", "/evaluate", {
                "symbol": request.symbol,
                "price": str(request.price),
                "previous_price": str(request.previous_price),
                "volume": str(request.volume),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            stages.append("strategy")

            research_request = {
                "query": f"{request.symbol} market conditions and trading risks",
                "research_type": "market",
                "symbol": request.symbol,
                "max_sources": 5,
            }
            research = await self._post(client, "research", "/prompt", research_request)
            stages.append("research")

            if request.use_ai:
                ai_analysis = await self._post(client, "ai", "/generate", {
                    "provider": "gemini",
                    "prompt": (
                        f"Symbol={request.symbol}; price={request.price}; previous_price={request.previous_price}; "
                        f"volume={request.volume}; strategy={strategy}; research={research['prompt']}. "
                        "Analyze the evidence, state directional bias and confidence, and do not execute trades."
                    ),
                    "system_instruction": "You are EchoMatrix AI Core. Analyze evidence conservatively and never execute trades.",
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
                "research_confidence": str(request.research_confidence),
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
                ("ai.analysis", "ai-core"),
                ("risk.decision", "risk"),
                ("capital.allocation", "capital-allocation"),
                ("trade.decision", "orchestration"),
            ]
            if simulation_fill:
                events.append(("simulation.fill", "simulation"))
                events.append(("outcome.recorded", "portfolio-engine"))
            else:
                events.append(("outcome.recorded", "integration-pipeline"))

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
            ai_analysis=ai_analysis,
            risk_decision=risk,
            allocation_decision=allocation,
            persisted_record_id=persisted_id,
            simulation_fill=simulation_fill,
            portfolio_state=portfolio_state,
            audit_record_id=audit_id,
        )
