"""
Ecometrics API Gateway - the first running service in the architecture.
"""
import logging
import time

from fastapi import FastAPI
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("ecometrics.api-gateway")

app = FastAPI(
    title="Ecometrics API Gateway",
    description="Entry point for the Ecometrics AI Financial and Wealth Operating System.",
    version="0.1.0",
)

START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    environment: str
    uptime_seconds: float


@app.get("/", tags=["meta"])
def root():
    return {
        "service": "ecometrics-api-gateway",
        "message": "Build the brain first. Give the brain a body later.",
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
