"""Contracts for the integrated, simulation-only EchoMatrix brain."""
from decimal import Decimal
from pydantic import BaseModel, Field

class Candle(BaseModel):
    timestamp: int
    symbol: str
    timeframe: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    source: str

class BrainCycleRequest(BaseModel):
    symbol: str = Field(default="BTC/USD", min_length=1)
    timeframe: str = Field(default="1h", min_length=1)
    limit: int = Field(default=120, ge=20, le=1000)
    use_ai: bool = True
    simulate: bool = True

class ReplayRequest(BaseModel):
    candles: list[Candle] = Field(min_length=30)
    initial_cash: Decimal = Field(default=Decimal("10000"), gt=0)
    allocation_fraction: Decimal = Field(default=Decimal("0.10"), ge=0, le=1)
    fee_rate: Decimal = Field(default=Decimal("0.001"), ge=0, le=1)

class BrainCycleResponse(BaseModel):
    mode: str
    symbol: str
    timeframe: str
    data_quality: dict
    market_state: dict
    research: dict
    strategy: dict
    ai_council: dict
    risk: dict
    allocation: dict
    simulation: dict
    learning: dict
    trace: list[str]
