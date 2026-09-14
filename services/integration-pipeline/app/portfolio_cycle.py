"""Deterministic multi-cycle portfolio simulation utilities.

This module is deliberately pure and side-effect free. It lets the brain replay a
sequence of simulated market observations while preserving cash, positions,
fees, equity, and performance metrics between cycles.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

ZERO = Decimal("0")
MONEY = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


class PortfolioSimulator:
    def __init__(self, initial_cash: Decimal, fee_rate: Decimal = Decimal("0.001")) -> None:
        if initial_cash <= ZERO:
            raise ValueError("initial_cash must be positive")
        if fee_rate < ZERO or fee_rate > Decimal("1"):
            raise ValueError("fee_rate must be between 0 and 1")
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.fee_rate = fee_rate
        self.position_qty = ZERO
        self.position_side: str | None = None
        self.entry_price = ZERO
        self.total_fees = ZERO
        self.cycles = 0
        self.equity_curve: list[dict] = []
        self.trades: list[dict] = []

    def mark_equity(self, price: Decimal) -> Decimal:
        position_value = self.position_qty * price
        if self.position_side == "sell":
            position_value = -position_value
        return self.cash + position_value

    def apply_decision(self, action: str, price: Decimal, allocated_value: Decimal) -> dict:
        action = action.lower()
        if price <= ZERO or allocated_value < ZERO:
            raise ValueError("price must be positive and allocation cannot be negative")
        if action not in {"buy", "sell", "hold"}:
            raise ValueError("unsupported action")

        if action == "hold" or allocated_value == ZERO:
            return {"action": "hold", "quantity": ZERO, "fee": ZERO, "opened": False}

        quantity = allocated_value / price
        fee = allocated_value * self.fee_rate
        if action == "buy":
            self.cash -= allocated_value + fee
        else:
            self.cash -= fee

        self.position_qty = quantity
        self.position_side = action
        self.entry_price = price
        self.total_fees += fee
        trade = {
            "cycle": self.cycles,
            "action": action,
            "price": money(price),
            "quantity": quantity,
            "notional": money(allocated_value),
            "fee": money(fee),
        }
        self.trades.append(trade)
        return {"action": action, "quantity": quantity, "fee": fee, "opened": True}

    def snapshot(self, price: Decimal) -> dict:
        equity = self.mark_equity(price)
        peak = max((Decimal(str(item["equity"])) for item in self.equity_curve), default=self.initial_cash)
        drawdown = ZERO if peak <= ZERO else (peak - equity) / peak
        return {
            "cycle": self.cycles,
            "cash": money(self.cash),
            "position_quantity": self.position_qty,
            "position_side": self.position_side,
            "mark_price": money(price),
            "equity": money(equity),
            "return_pct": (equity - self.initial_cash) / self.initial_cash,
            "drawdown": drawdown,
            "total_fees": money(self.total_fees),
        }

    def record_cycle(self, price: Decimal, action: str, allocated_value: Decimal) -> dict:
        self.cycles += 1
        trade = self.apply_decision(action, price, allocated_value)
        snapshot = self.snapshot(price)
        self.equity_curve.append(snapshot)
        return {"trade": trade, "portfolio": snapshot}

    def summary(self, price: Decimal) -> dict:
        current = self.snapshot(price)
        wins = sum(1 for trade in self.trades if trade["action"] in {"buy", "sell"})
        return {
            "cycles": self.cycles,
            "trades": wins,
            "initial_cash": money(self.initial_cash),
            "cash": current["cash"],
            "equity": current["equity"],
            "return_pct": current["return_pct"],
            "drawdown": current["drawdown"],
            "total_fees": current["total_fees"],
            "open_position": self.position_qty > ZERO,
        }


def replay_prices(prices: Iterable[Decimal], initial_cash: Decimal, fee_rate: Decimal = Decimal("0.001")) -> dict:
    """Replay a deterministic momentum policy over prices for infrastructure tests."""
    simulator = PortfolioSimulator(initial_cash, fee_rate)
    previous = None
    for price in prices:
        if previous is None:
            action = "hold"
        else:
            change = (price - previous) / previous
            action = "buy" if change > Decimal("0.005") else "sell" if change < Decimal("-0.005") else "hold"
        allocation = simulator.cash * Decimal("0.10") if action != "hold" else ZERO
        simulator.record_cycle(price, action, allocation)
        previous = price
    return simulator.summary(previous or initial_cash)
