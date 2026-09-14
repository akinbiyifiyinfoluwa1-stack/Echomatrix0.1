"""Bounded simulated capital allocation; never connects to an account."""

def allocation_snapshot(strategy: dict, risk: dict, equity: float = 10000.0, fraction: float = 0.10) -> dict:
    if not risk["approved"]:
        return {"allocated_value": 0.0, "fraction": 0.0, "status": "HOLD", "external_execution": False}
    bounded = max(0.0, min(float(fraction), 0.10))
    value = equity * bounded * float(risk["confidence"])
    return {"allocated_value": round(value, 2), "fraction": round(value / equity, 6) if equity else 0.0, "status": strategy["action"], "external_execution": False}
