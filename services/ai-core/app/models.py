"""Provider-neutral AI Core contracts for Gemini, Groq, Dahl and direct DeepSeek."""
from enum import Enum
from pydantic import BaseModel, Field

class AIProvider(str, Enum):
    GEMINI = "gemini"
    GROQ = "groq"
    DAHL = "dahl"
    DEEPSEEK = "deepseek"

class AIRequest(BaseModel):
    prompt: str = Field(min_length=1)
    system_instruction: str = "You are an analytical component of EchoMatrix."
    provider: AIProvider = AIProvider.GEMINI
    temperature: float = Field(default=0.2, ge=0, le=2)

class AIResponse(BaseModel):
    provider: AIProvider
    model: str
    content: str
    fallback_used: bool = False

class DecisionContextRequest(BaseModel):
    observation: dict
    strategy: dict
    research: dict
    risk: dict
    memory: list[dict] = Field(default_factory=list)
    provider: AIProvider = AIProvider.GEMINI
    temperature: float = Field(default=0.2, ge=0, le=2)

class DecisionContextResponse(BaseModel):
    analysis: AIResponse
    context_fields: list[str]
    memory_items_used: int

class CouncilRequest(BaseModel):
    prompt: str = Field(min_length=1)
    system_instruction: str = "You are an EchoMatrix simulation-only intelligence council."
    providers: list[AIProvider] = Field(default_factory=lambda: [AIProvider.GEMINI, AIProvider.GROQ, AIProvider.DAHL])
    temperature: float = Field(default=0.2, ge=0, le=2)

class CouncilResponse(BaseModel):
    responses: list[AIResponse]
    consensus: str
    disagreement: bool
    available_provider_count: int
