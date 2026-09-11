"""AI Core API. API keys are read from environment variables, never stored in code."""
from fastapi import FastAPI, HTTPException

from app.models import AIRequest, AIResponse
from app.providers import AIClient, AIProviderError

app = FastAPI(
    title="Ecometrics AI Core",
    description="Provider-neutral intelligence layer for Gemini and Groq.",
    version="0.1.0",
)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": "ecometrics-ai-core",
        "message": "The intelligence layer stays above risk and execution.",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-core"}


@app.post("/generate", response_model=AIResponse, tags=["ai"])
async def generate(request: AIRequest) -> AIResponse:
    # Environment access is intentionally isolated here for this service.
    import os

    client = AIClient(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
    )
    try:
        return await client.generate(request)
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
