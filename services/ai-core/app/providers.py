"""Provider-neutral AI adapters using HTTP APIs.

All providers are analysis-only. No provider has execution capability.
"""
from typing import Any
import httpx
from app.models import AIProvider, AIRequest, AIResponse

class AIProviderError(RuntimeError):
    pass

class AIClient:
    """Route analytical requests to Gemini, Groq, Dahl, or direct DeepSeek."""
    def __init__(self, gemini_api_key: str = "", groq_api_key: str = "", dahl_api_key: str = "", deepseek_api_key: str = "") -> None:
        self.gemini_api_key = gemini_api_key
        self.groq_api_key = groq_api_key
        self.dahl_api_key = dahl_api_key
        self.deepseek_api_key = deepseek_api_key

    async def generate(self, request: AIRequest) -> AIResponse:
        if request.provider == AIProvider.GEMINI: return await self._gemini(request)
        if request.provider == AIProvider.GROQ: return await self._groq(request)
        if request.provider == AIProvider.DAHL: return await self._dahl(request)
        return await self._deepseek(request)

    async def _gemini(self, request: AIRequest) -> AIResponse:
        if not self.gemini_api_key: raise AIProviderError("GEMINI_API_KEY is not configured")
        model = "gemini-2.5-flash"
        payload = {"system_instruction":{"parts":[{"text":request.system_instruction}]},"contents":[{"parts":[{"text":request.prompt}]}],"generationConfig":{"temperature":request.temperature}}
        async with httpx.AsyncClient(timeout=30) as client: response = await client.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", params={"key":self.gemini_api_key}, json=payload)
        if response.is_error: raise AIProviderError(f"Gemini request failed: HTTP {response.status_code}")
        try: content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc: raise AIProviderError("Gemini returned an unexpected response") from exc
        return AIResponse(provider=AIProvider.GEMINI, model=model, content=content)

    async def _openai_compatible(self, request: AIRequest, provider: AIProvider, key: str, base_url: str, model: str) -> AIResponse:
        if not key: raise AIProviderError(f"{provider.value.upper()}_API_KEY is not configured")
        payload = {"model":model,"messages":[{"role":"system","content":request.system_instruction},{"role":"user","content":request.prompt}],"temperature":request.temperature}
        async with httpx.AsyncClient(timeout=45) as client: response = await client.post(f"{base_url.rstrip('/')}/chat/completions", headers={"Authorization":f"Bearer {key}"}, json=payload)
        if response.is_error: raise AIProviderError(f"{provider.value} request failed: HTTP {response.status_code}")
        try: content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc: raise AIProviderError(f"{provider.value} returned an unexpected response") from exc
        return AIResponse(provider=provider, model=model, content=content)

    async def _groq(self, request: AIRequest) -> AIResponse:
        return await self._openai_compatible(request, AIProvider.GROQ, self.groq_api_key, "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile")

    async def _dahl(self, request: AIRequest) -> AIResponse:
        model = "MiniMaxAI/MiniMax-M2.7"
        return await self._openai_compatible(request, AIProvider.DAHL, self.dahl_api_key, "https://inference.dahl.global/v1", model)

    async def _deepseek(self, request: AIRequest) -> AIResponse:
        return await self._openai_compatible(request, AIProvider.DEEPSEEK, self.deepseek_api_key, "https://api.deepseek.com", "deepseek-v4-flash")
