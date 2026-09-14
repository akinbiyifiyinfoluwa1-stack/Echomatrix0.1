"""AI council bridge. The council is optional and always remains advisory/simulation-only."""
import os
import httpx

async def run_council(context: dict, use_ai: bool = True) -> dict:
    if not use_ai:
        return {"enabled": False, "available_provider_count": 0, "consensus": "deterministic", "disagreement": False, "responses": []}
    base = os.getenv("AI_CORE_URL", "http://ai-core:8000").rstrip("/")
    prompt = "Return a concise analytical assessment of this simulation state. Do not execute or recommend real-money actions. State uncertainty.\n" + repr(context)
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{base}/council", json={"prompt": prompt})
            r.raise_for_status()
            data = r.json()
            return {"enabled": True, **data}
    except Exception as exc:
        return {"enabled": True, "available_provider_count": 0, "consensus": "unavailable", "disagreement": False, "responses": [], "error": str(exc)}
