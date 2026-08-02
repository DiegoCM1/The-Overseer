"""Liveness signalling to healthchecks.io.

This is the one control Diego does not own. The Overseer pings after every
judgment run; if the pings stop, healthchecks.io notifies Daniel directly.

Without it, killing the process is worth 200 MXN a day — a crashed server would
be indistinguishable from a clean one, and "it was down" becomes an excuse. The
whole point is that a dead server is LOUDER than a working one.

Failures here are logged and swallowed. A healthchecks outage must never stop a
verdict from being recorded.
"""

import logging

import httpx

from core.config import settings

log = logging.getLogger("overseer")

_TIMEOUT = 10.0


async def ping(suffix: str = "") -> bool:
    """Ping the check. `suffix` may be '/fail' or '/start' per healthchecks.io.

    Returns True on success. Never raises.
    """
    if not settings.HEALTHCHECKS_URL:
        log.warning(
            "HEALTHCHECKS_URL is not set — nobody is watching whether the Overseer "
            "is alive. A crashed server currently goes unnoticed."
        )
        return False

    url = settings.HEALTHCHECKS_URL.rstrip("/") + suffix
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        log.info("Healthcheck ping ok%s", f" ({suffix})" if suffix else "")
        return True
    except Exception as e:
        # Deliberately swallowed: a monitoring outage must not block enforcement.
        log.error("Healthcheck ping FAILED (%s): %s", url, e)
        return False
