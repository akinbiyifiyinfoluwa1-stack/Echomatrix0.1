"""Deterministic workflow coordinator for EchoMatrix.

This layer owns workflow state, event sequencing, correlation IDs and
idempotency. It does not execute real-money transactions.
"""
from app.models import EventEnvelope, EventType, WorkflowRun, WorkflowStatus


class WorkflowEngine:
    """Create and advance a normalized intelligence-to-outcome workflow."""

    STAGES = [
        ("market-data", EventType.MARKET_UPDATE),
        ("research", EventType.RESEARCH_READY),
        ("strategy", EventType.STRATEGY_SIGNAL),
        ("ai-core", EventType.AI_ANALYSIS),
        ("risk", EventType.RISK_DECISION),
        ("capital-allocation", EventType.CAPITAL_ALLOCATION),
        ("decision", EventType.TRADE_DECISION),
        ("simulation", EventType.SIMULATION_FILL),
        ("outcome", EventType.OUTCOME_RECORDED),
        ("memory", EventType.MEMORY_WRITTEN),
    ]

    def create(self, correlation_id: str | None = None) -> WorkflowRun:
        from uuid import uuid4

        return WorkflowRun(
            correlation_id=correlation_id or str(uuid4()),
            status=WorkflowStatus.RUNNING,
            current_stage="market-data",
        )

    def append_event(
        self, workflow: WorkflowRun, event_type: EventType, source: str, payload: dict
    ) -> WorkflowRun:
        """Append an event exactly once for a correlation ID + event type."""
        duplicate = any(
            event.event_type == event_type and event.correlation_id == workflow.correlation_id
            for event in workflow.events
        )
        if duplicate:
            return workflow

        workflow.events.append(
            EventEnvelope(
                correlation_id=workflow.correlation_id,
                event_type=event_type,
                source=source,
                payload=payload,
            )
        )
        self._advance(workflow, event_type)
        return workflow

    def _advance(self, workflow: WorkflowRun, event_type: EventType) -> None:
        for index, (_, expected_event) in enumerate(self.STAGES):
            if expected_event == event_type:
                if index == len(self.STAGES) - 1:
                    workflow.current_stage = "completed"
                    workflow.status = WorkflowStatus.COMPLETED
                else:
                    workflow.current_stage = self.STAGES[index + 1][0]
                return

    def fail(self, workflow: WorkflowRun, error: str) -> WorkflowRun:
        workflow.status = WorkflowStatus.FAILED
        workflow.error = error
        return workflow
