"""Decision-context builder for the EchoMatrix intelligence layer."""
from __future__ import annotations

import json
from typing import Any


def build_decision_prompt(context: dict[str, Any]) -> str:
    """Create a bounded, auditable prompt from structured brain state."""
    payload = json.dumps(context, sort_keys=True, default=str)
    return (
        "Analyze this EchoMatrix simulation decision context. "
        "Separate observations from inference, identify contradictions and uncertainty, "
        "evaluate whether the strategy evidence is sufficiently supported by research and risk, "
        "and return a concise directional bias, confidence, key reasons, risks, and what evidence "
        "would change the conclusion. Do not execute trades or provide broker instructions. "
        f"\nCONTEXT:\n{payload}"
    )
