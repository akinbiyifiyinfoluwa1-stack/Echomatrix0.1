"""Research contracts: sources, findings, and structured research requests."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class ResearchType(str, Enum):
    MARKET = "market"
    MACRO = "macro"
    COMPANY = "company"
    CRYPTO = "crypto"
    TECHNOLOGY = "technology"
    GENERAL = "general"


class ResearchRequest(BaseModel):
    query: str = Field(min_length=1)
    research_type: ResearchType = ResearchType.GENERAL
    symbol: str = ""
    max_sources: int = Field(default=5, ge=1, le=20)


class ResearchSource(BaseModel):
    title: str = Field(min_length=1)
    url: HttpUrl
    source_name: str = ""
    published_at: datetime | None = None


class ResearchFinding(BaseModel):
    query: str
    research_type: ResearchType
    summary: str
    key_points: list[str] = Field(default_factory=list)
    sources: list[ResearchSource] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    generated_at: datetime
