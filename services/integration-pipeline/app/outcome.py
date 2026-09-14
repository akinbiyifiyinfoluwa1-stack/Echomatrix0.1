"""Deterministic mark-to-market outcome accounting for simulation runs."""
from decimal import Decimal, ROUND_HALF_UP


ZERO = Decimal("0")
MONEY = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def evaluate_outcome(
    *,
    action: str,
    entry_price: Decimal,
    mark_price: Decimal,
    quantity: Decimal,
    entry_fee: Decimal = ZERO,
    exit_fee_rate: Decimal = ZERO,
    risk_amount: Decimal = ZERO,
) -> dict:
    """Mark a paper position to a later price without executing anything."""
    if entry_price <= ZERO or mark_price <= ZERO or quantity < ZERO:
        raise ValueError("prices must be positive and quantity cannot be negative")

    normalized_action = action.lower()
    if normalized_action not in {"buy", "sell", "hold"}:
        raise ValueError("action must be buy, sell, or hold")

    gross_entry_value = entry_price * quantity
    gross_mark_value = mark_price * quantity
    direction = Decimal("1") if normalized_action == "buy" else Decimal("-1")
    gross_pnl = (mark_price - entry_price) * quantity * direction
    exit_fee = gross_mark_value * exit_fee_rate
    net_pnl = gross_pnl - entry_fee - exit_fee
    invested = gross_entry_value if gross_entry_value > ZERO else Decimal("1")
    return_pct = net_pnl / invested
    risk_multiple = net_pnl / risk_amount if risk_amount > ZERO else ZERO

    return {
        "action": normalized_action,
        "entry_price": _money(entry_price),
        "mark_price": _money(mark_price),
        "quantity": quantity,
        "entry_value": _money(gross_entry_value),
        "mark_value": _money(gross_mark_value),
        "gross_pnl": _money(gross_pnl),
        "entry_fee": _money(entry_fee),
        "exit_fee": _money(exit_fee),
        "net_pnl": _money(net_pnl),
        "return_pct": return_pct,
        "risk_multiple": risk_multiple,
        "profitable": net_pnl > ZERO,
        "status": "marked-to-market",
        "execution_mode": "simulation-only",
    }
