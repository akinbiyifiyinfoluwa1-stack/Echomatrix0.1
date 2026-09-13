"""HTTP entrypoint for the EchoMatrix core brain."""
from fastapi import FastAPI

from app.engine import EchoMatrixCore
from app.models import CycleRequest

app = FastAPI(
    title="EchoMatrix Core",
    description="Simulation-first intelligence runtime. No live execution.",
    version="0.1.0",
)
core = EchoMatrixCore()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "echomatrix-core", "mode": "simulation"}


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "echomatrix-core", "message": "Build the brain first. Give the brain a body later."}


@app.post("/cycle")
def cycle(request: CycleRequest) -> dict:
    return core.run_cycle(request).model_dump(mode="json")


@app.post("/demo/cycle")
def demo_cycle() -> dict:
    request = CycleRequest(
        symbol="BTC/USD",
        price="102000",
        previous_price="100000",
        volume="1",
    )
    return core.run_cycle(request).model_dump(mode="json")
