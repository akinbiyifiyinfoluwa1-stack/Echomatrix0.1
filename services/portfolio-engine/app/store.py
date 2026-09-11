"""Durable account-state store backed by the EchoMatrix persistence service."""
import os
from datetime import datetime, timezone
from decimal import Decimal

import httpx

from app.models import Portfolio


class PortfolioStore:
    def __init__(self) -> None:
        self.persistence_url = os.getenv("PERSISTENCE_URL", "http://persistence-layer:8000").rstrip("/")

    async def load(self, account_id: str, initial_cash: Decimal) -> Portfolio:
        record_id = f"portfolio-account:{account_id}"
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{self.persistence_url}/records/{record_id}")
            if response.status_code == 200:
                return Portfolio.model_validate(response.json()["payload"])
            if response.status_code != 404:
                response.raise_for_status()
        return Portfolio(portfolio_id=account_id, starting_cash=initial_cash, cash=initial_cash)

    async def save(self, portfolio: Portfolio) -> str:
        record_id = f"portfolio-account:{portfolio.portfolio_id}"
        now = datetime.now(timezone.utc).isoformat()
        payload = portfolio.model_dump(mode="json")
        for field in ("starting_cash", "cash", "realized_pnl"):
            payload[field] = str(getattr(portfolio, field))
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self.persistence_url}/records",
                json={
                    "record_id": record_id,
                    "record_type": "portfolio_state",
                    "owner_id": portfolio.portfolio_id,
                    "symbol": "",
                    "payload": payload,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            response.raise_for_status()
        return record_id
