"""Domain persistence schema for the EchoMatrix financial and wealth OS."""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("user_id", "account_name", name="uq_user_account_name"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    account_name: Mapped[str] = mapped_column(String(160))
    provider: Mapped[str] = mapped_column(String(64), default="demo")
    account_type: Mapped[str] = mapped_column(String(32), default="simulation")
    currency: Mapped[str] = mapped_column(String(16), default="USD")
    balance: Mapped[Decimal] = mapped_column(Numeric(28, 10), default=Decimal("0"))
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Instrument(Base):
    __tablename__ = "instruments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), default="")
    asset_class: Mapped[str] = mapped_column(String(32), index=True)
    exchange: Mapped[str] = mapped_column(String(80), default="")
    base_currency: Mapped[str] = mapped_column(String(16), default="")
    quote_currency: Mapped[str] = mapped_column(String(16), default="")


class MarketObservation(Base):
    __tablename__ = "market_observations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), index=True)
    timeframe: Mapped[str] = mapped_column(String(16), default="tick")
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    open: Mapped[Decimal | None] = mapped_column(Numeric(28, 10), nullable=True)
    high: Mapped[Decimal | None] = mapped_column(Numeric(28, 10), nullable=True)
    low: Mapped[Decimal | None] = mapped_column(Numeric(28, 10), nullable=True)
    close: Mapped[Decimal | None] = mapped_column(Numeric(28, 10), nullable=True)
    volume: Mapped[Decimal | None] = mapped_column(Numeric(32, 10), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), index=True)
    correlation_id: Mapped[str] = mapped_column(String(128), index=True)
    side: Mapped[str] = mapped_column(String(16))
    order_type: Mapped[str] = mapped_column(String(16), default="market")
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 10))
    requested_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 10), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Fill(Base):
    __tablename__ = "fills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    fill_price: Mapped[Decimal] = mapped_column(Numeric(28, 10))
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 10))
    fee: Mapped[Decimal] = mapped_column(Numeric(28, 10), default=Decimal("0"))
    filled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Position(Base):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 10), default=Decimal("0"))
    average_entry_price: Mapped[Decimal] = mapped_column(Numeric(28, 10), default=Decimal("0"))
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(28, 10), default=Decimal("0"))
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(28, 10), default=Decimal("0"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    equity: Mapped[Decimal] = mapped_column(Numeric(28, 10))
    cash: Mapped[Decimal] = mapped_column(Numeric(28, 10))
    exposure: Mapped[Decimal] = mapped_column(Numeric(28, 10), default=Decimal("0"))
    drawdown: Mapped[Decimal] = mapped_column(Numeric(12, 8), default=Decimal("0"))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class IntelligenceDecision(Base):
    __tablename__ = "intelligence_decisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    correlation_id: Mapped[str] = mapped_column(String(128), index=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    stage: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[Decimal] = mapped_column(Numeric(8, 6), default=Decimal("0"))
    rationale: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
