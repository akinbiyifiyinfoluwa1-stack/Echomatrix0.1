"""EchoMatrix API Gateway - the public nervous-system entry point."""
import logging
import os
import time

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("echomatrix.api-gateway")

app = FastAPI(
    title="EchoMatrix API Gateway",
    description="Public entry point for the EchoMatrix AI Financial and Wealth Operating System.",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    environment: str
    uptime_seconds: float


def integration_url() -> str:
    return os.getenv("INTEGRATION_PIPELINE_URL", "http://integration-pipeline:8000").rstrip("/")


async def proxy(path: str, method: str = "GET", payload: dict | None = None) -> dict | list:
    url = f"{integration_url()}{path}"
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.request(method, url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500]
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
    except httpx.HTTPError as exc:
        logger.exception("EchoMatrix backend unavailable: %s", exc)
        raise HTTPException(status_code=502, detail="EchoMatrix integration pipeline unavailable") from exc


@app.get("/", tags=["meta"])
def root():
    return {
        "service": "echomatrix-api-gateway",
        "message": "Build the brain first. Give the brain a body later.",
        "mode": "simulation-first",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health():
    logger.info("Health check requested")
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        uptime_seconds=round(time.time() - START_TIME, 2),
    )


@app.get("/readiness", tags=["diagnostics"])
async def readiness():
    """Single public readiness check for the complete backend dependency graph."""
    return await proxy("/readiness")


@app.get("/pipeline/self-test", tags=["diagnostics"])
async def pipeline_self_test(use_ai: bool = False):
    """Run the bounded simulation-only backend smoke test through the gateway."""
    return await proxy(f"/pipeline/self-test?use_ai={'true' if use_ai else 'false'}")


@app.get("/pipeline/status", tags=["diagnostics"])
async def pipeline_status():
    """Read the last completed backend cycle without starting a new one."""
    return await proxy("/pipeline/status")


@app.get("/dashboard/overview", tags=["dashboard"])
async def dashboard_overview(account_id: str = "pipeline-demo"):
    return await proxy(f"/dashboard/overview?account_id={account_id}")


@app.get("/dashboard/positions", tags=["dashboard"])
async def dashboard_positions(account_id: str = "pipeline-demo"):
    return await proxy(f"/dashboard/positions?account_id={account_id}")


@app.get("/dashboard/history", tags=["dashboard"])
async def dashboard_history(account_id: str = "pipeline-demo"):
    return await proxy(f"/dashboard/history?account_id={account_id}")


@app.post("/dashboard/run-cycle", tags=["dashboard"])
async def dashboard_run_cycle():
    return await proxy("/dashboard/run-cycle", method="POST", payload={})


@app.get("/dashboard/health", tags=["dashboard"])
async def dashboard_health():
    """Expose the integration pipeline health through the single public gateway."""
    pipeline = await proxy("/health")
    return {
        "gateway": {"status": "ok"},
        "integration_pipeline": pipeline,
    }


@app.get("/dashboard", tags=["dashboard"])
async def dashboard_bundle(account_id: str = "pipeline-demo"):
    """One-call dashboard read model for clients that want a single request."""
    overview = await proxy(f"/dashboard/overview?account_id={account_id}")
    positions = await proxy(f"/dashboard/positions?account_id={account_id}")
    history = await proxy(f"/dashboard/history?account_id={account_id}")
    return {
        "overview": overview,
        "positions": positions,
        "history": history,
        "mode": "simulation",
    }
