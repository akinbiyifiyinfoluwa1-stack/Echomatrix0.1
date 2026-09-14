"""Fast, deterministic long-only paper portfolio simulator."""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Sequence

D = Decimal

@dataclass
class SimTrade:
    index: int
    side: str
    price: D
    quantity: D
    fee: D
    realized_pnl: D = D("0")

@dataclass
class PaperPortfolio:
    initial_cash: D
    fee_rate: D
    cash: D = field(init=False)
    quantity: D = field(default=D("0"), init=False)
    cost_basis: D = field(default=D("0"), init=False)
    fees: D = field(default=D("0"), init=False)
    realized_pnl: D = field(default=D("0"), init=False)
    equity_curve: list[D] = field(default_factory=list, init=False)
    trades: list[SimTrade] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.cash = self.initial_cash

    def equity(self, price: D) -> D:
        return self.cash + self.quantity * price

    def rebalance(self, index: int, action: str, price: D, allocation: D) -> SimTrade | None:
        if action == "buy" and self.quantity == 0:
            notional = min(max(allocation, D("0")), self.cash)
            if notional <= 0: return None
            fee = notional * self.fee_rate
            qty = (notional - fee) / price
            self.cash -= notional
            self.quantity += qty
            self.cost_basis += notional
            self.fees += fee
            trade = SimTrade(index, "buy", price, qty, fee)
            self.trades.append(trade)
            return trade
        if action == "sell" and self.quantity > 0:
            qty = self.quantity
            gross = qty * price
            fee = gross * self.fee_rate
            basis = self.cost_basis
            realized = gross - fee - basis
            self.cash += gross - fee
            self.quantity = D("0")
            self.cost_basis = D("0")
            self.fees += fee
            self.realized_pnl += realized
            trade = SimTrade(index, "sell", price, qty, fee, realized)
            self.trades.append(trade)
            return trade
        return None

def replay(closes: Sequence[D], initial_cash: D, fee_rate: D, allocation_fraction: D, threshold: D) -> dict:
    if len(closes) < 3: raise ValueError("at least three prices are required")
    portfolio = PaperPortfolio(initial_cash, fee_rate)
    for i, price in enumerate(closes):
        previous = closes[i-1] if i else price
        change = D("0") if previous == 0 else (price - previous) / previous
        action = "buy" if change > threshold else "sell" if change < -threshold else "hold"
        portfolio.rebalance(i, action, price, portfolio.equity(price) * allocation_fraction)
        portfolio.equity_curve.append(portfolio.equity(price))
    final_equity = portfolio.equity(closes[-1])
    peak = portfolio.equity_curve[0]
    max_dd = D("0")
    for value in portfolio.equity_curve:
        peak = max(peak, value)
        if peak: max_dd = max(max_dd, (peak - value) / peak)
    sells = [t for t in portfolio.trades if t.side == "sell"]
    wins = [t for t in sells if t.realized_pnl > 0]
    losses = [t for t in sells if t.realized_pnl < 0]
    gross_profit = sum((t.realized_pnl for t in wins), D("0"))
    gross_loss = abs(sum((t.realized_pnl for t in losses), D("0")))
    return {
        "initial_equity": str(initial_cash), "final_equity": str(final_equity),
        "return_pct": str(((final_equity - initial_cash) / initial_cash) * D("100")),
        "max_drawdown_pct": str(max_dd * D("100")), "fees": str(portfolio.fees),
        "realized_pnl": str(portfolio.realized_pnl), "trade_count": len(portfolio.trades),
        "closed_trade_count": len(sells), "win_rate": str(D(len(wins)) / D(len(sells)) if sells else D("0")),
        "profit_factor": str(gross_profit / gross_loss if gross_loss else (D("0") if not gross_profit else D("Infinity"))),
        "equity_curve": [str(v) for v in portfolio.equity_curve],
        "trades": [t.__dict__ | {k: str(v) for k, v in t.__dict__.items() if isinstance(v, D)} for t in portfolio.trades],
    }
