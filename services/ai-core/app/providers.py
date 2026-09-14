"""Provider-neutral AI adapters using HTTP APIs.

EchoMatrix can use Gemini, Groq, or DeepSeek for analysis. These providers
only receive analytical context; they have no execution capability.
"""
from typing import Any

import httpx

from app.models import AIProvider, AIRequest, AIResponse


class AIProviderError(RuntimeError):
    pass


class AIClient:
    """Route requests to a configured Gemini, Groq, or DeepSeek provider."""

    def __init__(self, gemini_api_key: str = "", groq_api_key: str = "", deepseek_api_key: str = "") -> None:
        self.gemini_api_key = gemini_api_key
        self.groq_api_key = groq_api_key
        self.deepseek_api_key = deepseek_api_key

    async def generate(self, request: AIRequest) -> AIResponse:
        if request.provider == AIProvider.GEMINI:
            return await self._gemini(request)
        if request.provider == AIProvider.GROQ:
            return await self._groq(request)
        return await self._deepseek(request)

    async def _gemini(self, request: AIRequest) -> AIResponse:
        if not self.gemini_api_key:
            raise AIProviderError("GEMINI_API_KEY is not configured")
        model = "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload: dict[str, Any] = {
            "system_instruction": {"parts": [{"text": request.system_instruction}]},
            "contents": [{"parts": [{"text": request.prompt}]}],
            "generationConfig": {"temperature": request.temperature},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params={"key": self.gemini_api_key}, json=payload)
        if response.is_error:
            raise AIProviderError(f"Gemini request failed: HTTP {response.status_code}")
        data = response.json()
        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError("Gemini returned an unexpected response") from exc
        return AIResponse(provider=AIProvider.GEMINI, model=model, content=content)

    async def _groq(self, request: AIRequest) -> AIResponse:
        if not self.groq_api_key:
            raise AIProviderError("GROQ_API_KEY is not configured")
        model = "llama-3.3-70b-versatile"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": request.system_instruction},
                {"role": "user", "content": request.prompt},
            ],
            "temperature": request.temperature,
        }
        headers = {"Authorization": f"Bearer {self.groq_api_key}"}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
            )
        if response.is_error:
            raise AIProviderError(f"Groq request failed: HTTP {response.status_code}")
        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError("Groq returned an unexpected response") from exc
        return AIResponse(provider=AIProvider.GROQ, model=model, content=content)

    async def _deepseek(self, request: AIRequest) -> AIResponse:
        if not self.deepseek_api_key:
            raise AIProviderError("DEEPSEEK_API_KEY is not configured")
        model = "deepseek-v4-flash"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": request.system_instruction},
                {"role": "user", "content": request.prompt},
            ],
            "temperature": request.temperature,
        }
        headers = {"Authorization": f"Bearer {self.deepseek_api_key}"}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers=headers,
                json=payload,
            )
        if response.is_error:
            raise AIProviderError(f"DeepSeek request failed: HTTP {response.status_code}")
        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError("DeepSeek returned an unexpected response") from exc
        return AIResponse(provider=AIProvider.DEEPSEEK, model=model, content=content)
