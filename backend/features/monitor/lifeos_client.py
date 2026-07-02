"""Reads deadline-miss truth from life-os. The Overseer never computes deadlines
itself — it asks life-os "what's overdue and how bad" via GET /api/v1/misses."""

import httpx

from core.config import settings


async def get_misses(date_str: str | None = None) -> dict:
    """Fetch per-goal severity for a date (defaults to life-os's today)."""
    params = {"date": date_str} if date_str else {}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.LIFEOS_API_URL}/api/v1/misses",
            params=params,
            headers={"X-API-Key": settings.LIFEOS_API_SECRET},
        )
        resp.raise_for_status()
        return resp.json()
