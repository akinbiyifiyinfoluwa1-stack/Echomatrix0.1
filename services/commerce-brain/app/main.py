from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .orchestrator import CommerceContext, CommerceOrchestrator

app = FastAPI(title="EchoMatrix Commerce Brain", version="0.1.0")
orchestrator = CommerceOrchestrator()


class CommerceRequest(BaseModel):
    customer_id: str = "guest"
    query: str = Field(min_length=1)
    product_id: str | None = None
    quantity: int = Field(default=1, ge=1, le=100)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "EchoMatrix Commerce Brain",
        "version": "0.1.0",
        "mode": "commerce-intelligence",
        "principle": "Brain first. Body later.",
    }


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {"status": "ok", "simulation_only": True}


@app.post("/commerce/plan")
def create_plan(request: CommerceRequest) -> dict:
    context = CommerceContext(
        customer_id=request.customer_id,
        query=request.query,
        product_id=request.product_id,
        quantity=request.quantity,
    )
    return orchestrator.plan(context)


@app.get("/commerce/demo")
def demo() -> dict:
    context = CommerceContext(
        customer_id="demo-customer",
        query="Find a product and prepare it for checkout",
        product_id="demo-product-001",
        quantity=2,
    )
    return orchestrator.plan(context)
