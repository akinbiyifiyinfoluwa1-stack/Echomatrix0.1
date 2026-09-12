"""Deterministic paper-trading engine. No broker or real-money connectivity."""
from decimal import Decimal

from app.models import (
    Side,
    SimulationAccount,
    SimulatedFill,
    SimulatedOrder,
    SimulatedPosition,
)


class SimulationEngine:
    """Execute simulated market orders against supplied prices."""

    def __init__(self, account: SimulationAccount) -> None:
        self.account = account

    def execute_market_order(
        self, order: SimulatedOrder, market_price: Decimal, fee_rate: Decimal = Decimal("0")
    ) -> SimulatedFill:
        if market_price <= 0:
            raise ValueError("market_price must be greater than zero")

        notional = order.quantity * market_price
        fee = notional * fee_rate

        if order.side == Side.BUY:
            total_cost = notional + fee
            if total_cost > self.account.cash:
                raise ValueError("insufficient simulated cash")
            self.account.cash -= total_cost
        else:
            self.account.cash += notional - fee

        fill = SimulatedFill(
            order=order,
            fill_price=market_price,
            filled_quantity=order.quantity,
            fee=fee,
            timestamp=order.timestamp,
        )
        self.account.fills.append(fill)
        self._update_position(order.side, order.instrument_symbol, order.quantity, market_price)
        self.account.equity = self.account.cash
        return fill

    def _update_position(
        self, side: Side, symbol: str, quantity: Decimal, price: Decimal
    ) -> None:
        position = next(
            (item for item in self.account.positions if item.instrument_symbol == symbol),
            None,
        )

        signed_quantity = quantity if side == Side.BUY else -quantity
        if position is None:
            self.account.positions.append(
                SimulatedPosition(
                    instrument_symbol=symbol,
                    quantity=signed_quantity,
                    average_entry_price=price,
                )
            )
            return

        old_quantity = position.quantity
        new_quantity = old_quantity + signed_quantity

        if old_quantity == 0 or (old_quantity > 0 and signed_quantity > 0) or (
            old_quantity < 0 and signed_quantity < 0
        ):
            total_cost = abs(old_quantity) * position.average_entry_price + abs(signed_quantity) * price
            position.average_entry_price = total_cost / abs(new_quantity)
        else:
            closed_quantity = min(abs(old_quantity), abs(signed_quantity))
            pnl_per_unit = price - position.average_entry_price
            if old_quantity < 0:
                pnl_per_unit = -pnl_per_unit
            position.realized_pnl += closed_quantity * pnl_per_unit

        position.quantity = new_quantity
