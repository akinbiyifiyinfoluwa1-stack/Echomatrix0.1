"""Pure simulation portfolio accounting for research; no external execution."""

def simulate_decision(price: float, action: str, allocated: float, next_price: float | None = None, fee_rate: float = 0.001) -> dict:
    future = price if next_price is None else next_price
    fee = allocated * fee_rate
    if action == "BUY": pnl = allocated * ((future - price) / price)
    elif action == "SELL": pnl = allocated * ((price - future) / price)
    else: pnl = 0.0
    return {"action": action, "entry_price": price, "mark_price": future, "allocated_value": round(allocated, 2), "fees": round(fee, 6), "simulated_pnl": round(pnl - fee, 6), "external_execution": False}


def replay_returns(prices: list[float], allocation_fraction: float = 0.10, fee_rate: float = 0.001) -> dict:
    if len(prices) < 3: raise ValueError("at least three prices required")
    equity = 10000.0; peak = equity; max_dd = 0.0; pnls = []; decisions = []
    for i in range(1, len(prices) - 1):
        change = (prices[i] - prices[i-1]) / prices[i-1]
        action = "BUY" if change > 0.005 else "SELL" if change < -0.005 else "HOLD"
        allocated = equity * max(0.0, min(allocation_fraction, 0.10)) if action != "HOLD" else 0.0
        result = simulate_decision(prices[i], action, allocated, prices[i+1], fee_rate)
        equity += result["simulated_pnl"]; pnls.append(result["simulated_pnl"]); decisions.append(result)
        peak = max(peak, equity); max_dd = max(max_dd, (peak - equity) / peak if peak else 0.0)
    wins = sum(1 for p in pnls if p > 0); losses = sum(1 for p in pnls if p < 0)
    gross_profit = sum(p for p in pnls if p > 0); gross_loss = abs(sum(p for p in pnls if p < 0))
    return {"initial_equity": 10000.0, "final_equity": round(equity, 6), "return": round((equity/10000.0)-1, 6), "max_drawdown": round(max_dd, 6), "win_rate": round(wins / len(pnls), 6) if pnls else 0.0, "profit_factor": round(gross_profit / gross_loss, 6) if gross_loss else None, "observations": len(prices), "decisions": decisions, "simulation_only": True}
