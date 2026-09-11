"""Provider-neutral AI Core contracts for Gemini and Groq."""
from enum import Enum

from pydantic import BaseModel, Field


class AIProvider(str, Enum):
    GEMINI = "gemini"
    GROQ = "groq"


class AIRequest(BaseModel):
    prompt: str = Field(min_length=1)
    system_instruction: str = "You are an analytical component of Ecometrics."
    provider: AIProvider = AIProvider.GEMINI
    temperature: float = Field(default=0.2, ge=0, le=2)


class AIResponse(BaseModel):
    provider: AIProvider
    model: str
    content: str
    fallback_used: bool = False
