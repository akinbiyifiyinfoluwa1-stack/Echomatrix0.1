"""HTTP coordinator connecting EchoMatrix services end-to-end.

The pipeline is simulation-first: it can call the intelligence services and
persist the resulting decision, but it never sends an order to a broker.
"""
import os
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
            "workflow": os.getenv("WORKFLOW_ENGINE_URL", "http://workflow-engine:8000"),
            "persistence": os.getenv("PERSISTENCE_URL", "http://persistence-layer:8000"),
        }

    async def _get(self, client: httpx.AsyncClient, service: str, path: str) -> dict:
        response = await client.get(f"{self.services[service]}{path}")
        response.raise_for_status()
        return response.json()

    async def _post(self, client: httpx.AsyncClient, service: str, path: str, payload: dict) -> dict:
        response = await client.post(f"{self.services[service]}{path}", json=payload)
        response.raise_for_status()
        return response.json()

    async def run(self, request: PipelineRequest) -> PipelineResult:
        correlation_id = str(uuid4())
        stages: list[str] = []

        async with httpx.AsyncClient(timeout=20) as client:
            # 1. Verify the sensory layer is reachable.
            await self._get(client, "market-data", "/health")
            stages.append("market-data")

            # 2. Record the workflow start before downstream decisions.
            workflow = await self._post(client, "workflow", "/workflows", {})
            stages.append("workflow")

            # 3. Research and strategy are represented by their service contracts.
            research = await self._get(client, "research", "/health")
            stages.append("research")
            strategy = await self._get(client, "strategy", "/health")
            stages.append("strategy")

            # 4. Ask the orchestration engine to combine intelligence + risk constraints.
            decision_payload = {
                "symbol": request.symbol,
                "price": str(request.price),
                "previous_price": str(request.previous_price),
                "volume": str(request.volume),
                "portfolio_equity": str(request.portfolio_equity),
                "current_exposure": str(request.current_exposure),
                "proposed_position_value": str(request.proposed_position_value),
                "stop_distance": str(request.stop_distance),
                "daily_drawdown": str(request.daily_drawdown),
                "research_confidence": str(request.research_confidence),
                "ai_confidence": str(request.ai_confidence),
            }
            decision = await self._post(client, "orchestration", "/decision", decision_payload)
            stages.extend(["ai-core", "risk", "capital-allocation", "decision"])

            # 5. Persist the normalized decision as the system's permanent record.
            persisted_id = None
            audit_id = None
            if request.persist:
                persisted_id = str(uuid4())
                now = "2026-09-11T00:00:00Z"
                stored = await self._post(client, "persistence", "/records", {
                    "record_id": persisted_id,
                    "record_type": "decision",
                    "owner_id": "system",
                    "symbol": request.symbol,
                    "payload": {
                        "correlation_id": correlation_id,
                        "action": decision["action"],
                        "confidence": decision["confidence"],
                        "allocated_value": decision["allowed_position_value"],
                        "risk_amount": decision["risk_amount"],
                        "research_health": research,
                        "strategy_health": strategy,
                    },
                    "created_at": now,
                    "updated_at": now,
                })
                audit_id = stored["record_id"]
                stages.append("persistence")

            # 6. Close the workflow with a simulation-first event.
            events = [
                ("market.update", "market-data"),
                ("research.ready", "research"),
                ("strategy.signal", "strategy"),
                ("ai.analysis", "ai-core"),
                ("risk.decision", "risk"),
                ("capital.allocation", "capital-allocation"),
                ("trade.decision", "orchestration"),
            ]
            for event_type, source in events:
                await self._post(client, "workflow", f"/workflows/{workflow['workflow_id']}/events", {
                    "correlation_id": workflow["correlation_id"],
                    "event_type": event_type,
                    "source": source,
                    "payload": {"symbol": request.symbol, "correlation_id": correlation_id},
                })
            stages.append("workflow-events")

        return PipelineResult(
            correlation_id=correlation_id,
            symbol=request.symbol,
            action=decision["action"],
            confidence=Decimal(str(decision["confidence"])),
            allocated_value=Decimal(str(decision["allowed_position_value"])),
            risk_amount=Decimal(str(decision["risk_amount"])),
            stages_completed=stages,
            persisted_record_id=persisted_id,
            audit_record_id=audit_id,
        )
