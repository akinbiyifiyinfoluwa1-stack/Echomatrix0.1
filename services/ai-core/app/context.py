"""Decision-context builder for the EchoMatrix intelligence layer."""
from __future__ import annotations

import json
from typing import Any


def build_decision_prompt(context: dict[str, Any]) -> str:
    payload = json.dumps(context, sort_keys=True, default=str)
    return (
        "Analyze this EchoMatrix simulation decision context. Separate observations from inference, "
        "identify contradictions and uncertainty, evaluate strategy evidence against research and risk, "
        "and return directional bias, confidence, key reasons, risks, and what evidence would change the conclusion. "
        "Do not execute trades or provide broker instructions.\nCONTEXT:\n" + payload
    )
