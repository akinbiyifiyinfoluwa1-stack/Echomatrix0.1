"""Point-in-time data quality gates and lineage metadata."""
from decimal import Decimal


def validate_candles(candles: list) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    seen = set()
    previous = None
    for i, c in enumerate(candles):
        if c.timestamp in seen:
            errors.append(f"duplicate timestamp at index {i}")
        seen.add(c.timestamp)
        if previous is not None and c.timestamp <= previous:
            errors.append(f"timestamps not strictly increasing at index {i}")
        previous = c.timestamp
        if c.low > min(c.open, c.close) or c.high < max(c.open, c.close):
            errors.append(f"invalid OHLC relationship at index {i}")
        if c.low <= 0 or c.high <= 0 or c.open <= 0 or c.close <= 0:
            errors.append(f"non-positive price at index {i}")
        if c.volume < 0:
            errors.append(f"negative volume at index {i}")
    if len(candles) < 30:
        warnings.append("small observation window")
    sources = sorted({c.source for c in candles})
    return {"valid": not errors, "errors": errors, "warnings": warnings, "count": len(candles), "sources": sources, "lineage": {"first_timestamp": candles[0].timestamp if candles else None, "last_timestamp": candles[-1].timestamp if candles else None}}
