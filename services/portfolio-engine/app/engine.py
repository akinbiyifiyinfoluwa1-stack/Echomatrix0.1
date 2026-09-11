"""Portfolio accounting engine. No broker connectivity or real-money execution."""
from decimal import Decimal

from app.models import Fill, Portfolio, Position


class PortfolioEngine:
    """Apply fills and market prices to a portfolio's accounting state."""

    def __init__(self, portfolio: Portfolio) -> None:
        self.portfolio = portfolio

    def apply_fill(self, fill: Fill) -> Position:
        """Apply a buy/sell fill and update cash, position cost basis, and realized P/L."""
        position = next(
            (item for item in self.portfolio.positions if item.symbol == fill.symbol),
            None,
        )
        if position is None:
            position = Position(
                symbol=fill.symbol,
                asset_class=fill.asset_class,
            )
            self.portfolio.positions.append(position)

        signed_quantity = fill.quantity if fill.side == "buy" else -fill.quantity
        trade_value = fill.quantity * fill.price

        if fill.side == "buy":
            self.portfolio.cash -= trade_value + fill.fee
        else:
            self.portfolio.cash += trade_value - fill.fee

        old_quantity = position.quantity
        new_quantity = old_quantity + signed_quantity

        if old_quantity == 0 or (old_quantity > 0 and signed_quantity > 0) or (
            old_quantity < 0 and signed_quantity < 0
        ):
            old_value = abs(old_quantity) * position.average_entry_price
            new_value = abs(signed_quantity) * fill.price
            if new_quantity != 0:
                position.average_entry_price = (old_value + new_value) / abs(new_quantity)
        else:
            closed_quantity = min(abs(old_quantity), abs(signed_quantity))
            pnl_per_unit = fill.price - position.average_entry_price
            if old_quantity < 0:
                pnl_per_unit = -pnl_per_unit
            realized = closed_quantity * pnl_per_unit
            position.realized_pnl += realized
            self.portfolio.realized_pnl += realized

            # If a trade reverses the position, the remaining quantity starts a new cost basis.
            if new_quantity != 0 and abs(signed_quantity) > abs(old_quantity):
                position.average_entry_price = fill.price

        position.quantity = new_quantity
        if position.quantity == 0:
            position.average_entry_price = Decimal("0")
            position.unrealized_pnl = Decimal("0")

        self.portfolio.fills.append(fill)
        return position

    def mark_price(self, symbol: str, price: Decimal) -> Position:
        """Mark one position to a current market price and recompute unrealized P/L."""
        if price <= 0:
            raise ValueError("price must be greater than zero")

        position = self._get_position(symbol)
        position.mark_price = price
        position.unrealized_pnl = position.quantity * (price - position.average_entry_price)
        if position.quantity < 0:
            position.unrealized_pnl = position.quantity * (price - position.average_entry_price)
        return position

    def mark_all(self, prices: dict[str, Decimal]) -> Portfolio:
        for symbol, price in prices.items():
            self.mark_price(symbol, price)
        return self.portfolio

    def exposure_by_asset_class(self) -> dict[str, Decimal]:
        exposure: dict[str, Decimal] = {}
        for position in self.portfolio.positions:
            key = position.asset_class.value
            exposure[key] = exposure.get(key, Decimal("0")) + abs(position.market_value)
        return exposure

    def _get_position(self, symbol: str) -> Position:
        position = next(
            (item for item in self.portfolio.positions if item.symbol == symbol),
            None,
        )
        if position is None:
            raise ValueError(f"position not found: {symbol}")
        return position
