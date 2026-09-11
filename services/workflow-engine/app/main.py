"""EchoMatrix workflow API: the event backbone connecting the intelligence layers."""
from fastapi import FastAPI, HTTPException

from app.engine import WorkflowEngine
from app.models import EventEnvelope, WorkflowRun

app = FastAPI(
    title="EchoMatrix Workflow Engine",
    description="Coordinates the event-driven intelligence workflow without real-money execution.",
    version="0.1.0",
)

engine = WorkflowEngine()
workflows: dict[str, WorkflowRun] = {}

@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"service": "echomatrix-workflow-engine", "message": "Connect the brain before giving it a body."}

@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "workflow-engine"}

@app.post("/workflows", response_model=WorkflowRun, tags=["workflow"])
def create_workflow() -> WorkflowRun:
    workflow = engine.create()
    workflows[workflow.workflow_id] = workflow
    return workflow

@app.get("/workflows/{workflow_id}", response_model=WorkflowRun, tags=["workflow"])
def get_workflow(workflow_id: str) -> WorkflowRun:
    workflow = workflows.get(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="workflow not found")
    return workflow

@app.post("/workflows/{workflow_id}/events", response_model=WorkflowRun, tags=["workflow"])
def append_event(workflow_id: str, event: EventEnvelope) -> WorkflowRun:
    workflow = workflows.get(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="workflow not found")
    if event.correlation_id != workflow.correlation_id:
        raise HTTPException(status_code=400, detail="correlation_id does not match workflow")
    return engine.append_event(workflow, event.event_type, event.source, event.payload)

@app.get("/demo/workflow", response_model=WorkflowRun, tags=["demo"])
def demo_workflow() -> WorkflowRun:
    workflow = engine.create(correlation_id="demo-echomatrix-001")
    for stage, event_type in engine.STAGES:
        engine.append_event(workflow, event_type, source=stage, payload={"demo": True, "stage": stage})
    return workflow
