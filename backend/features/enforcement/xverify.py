"""Post-URL extraction and existence check.

Scope is deliberately narrow. We confirm that a URL *looks like* an X post and
that X will publicly render it — nothing more. We do NOT scrape X, and we do not
try to verify that the post contains a video, or when it was published:

- X's read API is paywalled, so any real verification costs money.
- The daily heartbeat puts the link in front of Daniel, who is a human with an
  incentive to look. He is the video check.

So the automated check answers one question — "does this public post exist?" —
and a human answers the rest. Claiming more than that would be security theatre.
"""

import logging
import re

import httpx

log = logging.getLogger("overseer")

# x.com or twitter.com, any handle, /status/<digits>. Trailing query is ignored.
POST_URL = re.compile(
    r"https?://(?:www\.)?(?:x|twitter)\.com/[A-Za-z0-9_]+/status/(\d+)",
    re.IGNORECASE,
)

OEMBED = "https://publish.twitter.com/oembed"
_TIMEOUT = 10.0


def extract_post_url(text: str) -> str | None:
    """First X/Twitter status URL in a message body, normalised without query."""
    if not text:
        return None
    match = POST_URL.search(text)
    return match.group(0) if match else None


async def post_exists(url: str) -> bool:
    """True when X's free oEmbed endpoint renders the post (HTTP 200).

    A deleted, private or fabricated URL returns 404/403. Network failure returns
    False — the default state is failure, so an unverifiable link is not accepted.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(OEMBED, params={"url": url, "omit_script": "1"})
    except Exception as e:
        log.warning("oEmbed check failed for %s: %s", url, e)
        return False

    if resp.status_code == 200:
        return True

    log.info("oEmbed rejected %s with HTTP %s", url, resp.status_code)
    return False
