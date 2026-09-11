"""Canonical financial market-data models used across Ecometrics."""
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class AssetClass(str, Enum):
    FOREX = "forex"
    CRYPTO = "crypto"
    STOCK = "stock"
    INDEX = "index"
    COMMODITY = "commodity"
    ENERGY = "energy"
    METAL = "metal"
    NFT = "nft"
    OTHER = "other"


class Instrument(BaseModel):
    symbol: str = Field(min_length=1)
    name: str = ""
    asset_class: AssetClass
    quote_currency: str = ""
    base_currency: str = ""
    exchange: str = ""


class MarketTick(BaseModel):
    instrument: Instrument
    timestamp: datetime
    bid: Decimal | None = None
    ask: Decimal | None = None
    last: Decimal | None = None
    volume: Decimal | None = None


class Candle(BaseModel):
    instrument: Instrument
    timestamp: datetime
    timeframe: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None = None

    @property
    def is_valid(self) -> bool:
        return self.high >= max(self.open, self.close, self.low) and self.low <= min(
            self.open, self.close, self.high
        )
