"""AI Core API. API keys are read from environment variables, never stored in code."""
import os

from fastapi import FastAPI, HTTPException

from app.context import build_decision_prompt
from app.models import AIRequest, AIResponse, DecisionContextRequest, DecisionContextResponse
from app.providers import AIClient, AIProviderError

app = FastAPI(
    title="EchoMatrix AI Core",
    description="Provider-neutral intelligence layer for Gemini, Groq, and DeepSeek.",
    version="0.3.0",
)


def _client() -> AIClient:
    return AIClient(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    )


@app.get("/", tags=["meta"])
def root() -> dict[str, str | list[str]]:
    return {
        "service": "echomatrix-ai-core",
        "message": "The intelligence layer stays above risk and execution.",
        "context_engine": "enabled",
        "providers": ["gemini", "groq", "deepseek"],
        "execution": "false",
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-core", "mode": "simulation", "execution": "false"}


@app.post("/generate", response_model=AIResponse, tags=["ai"])
async def generate(request: AIRequest) -> AIResponse:
    try:
        return await _client().generate(request)
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/analyze-context", response_model=DecisionContextResponse, tags=["ai"])
async def analyze_context(request: DecisionContextRequest) -> DecisionContextResponse:
    """Reason over the complete structured brain state without executing anything."""
    context = {
        "observation": request.observation,
        "strategy": request.strategy,
        "research": request.research,
        "risk": request.risk,
        "memory": request.memory,
    }
    ai_request = AIRequest(
        prompt=build_decision_prompt(context),
        system_instruction=(
            "You are EchoMatrix AI Core. You are a decision-support component inside a "
            "simulation-only financial intelligence system. Never execute trades. "
            "Treat memory as historical context, not truth. Explicitly surface uncertainty."
        ),
        provider=request.provider,
        temperature=request.temperature,
    )
    try:
        analysis = await _client().generate(ai_request)
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return DecisionContextResponse(
        analysis=analysis,
        context_fields=list(context.keys()),
        memory_items_used=len(request.memory),
    )
