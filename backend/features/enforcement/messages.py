"""Message wording for the bet.

Same shape as features/monitor/messages.py: the LLM writes the copy, deterministic
templates are the fallback, and a send NEVER blocks on the model being slow or down.

One rule specific to this domain: **the LLM never produces a fact.** The streak
number is formatted deterministically and appended outside the model's output, so
a hallucinated or "rounded up" number cannot reach Daniel. The model chooses tone;
the code states the number.
"""

import logging

from openai import OpenAI

from core.config import settings

log = logging.getLogger("overseer")

_client = (
    OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.OPENROUTER_API_KEY)
    if settings.OPENROUTER_API_KEY
    else None
)

_MODEL = "deepseek/deepseek-v4-flash"


def _llm(prompt: str, fallback: str, max_tokens: int = 120) -> str:
    if _client is None:
        return fallback
    try:
        resp = _client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            timeout=8,
        )
        return (resp.choices[0].message.content or "").strip() or fallback
    except Exception as e:
        log.warning("LLM copy failed, using template: %s", e)
        return fallback


# --------------------------------------------------------------------------- #
# 13:30 — 30 minutes left, nothing submitted
# --------------------------------------------------------------------------- #


def compose_reminder(minutes_left: int) -> str:
    fallback = (
        f"⏳ {minutes_left} minutes to 2 PM and nothing is logged. "
        f"Post the video and send me the link, or it's 200 MXN."
    )
    return _llm(
        f"Write ONE short message (max 200 chars) to Diego. He has {minutes_left} "
        f"minutes left to publish a video on X before a 2 PM deadline, and he has "
        f"submitted nothing. Missing it costs him 200 MXN. Tone: urgent, clipped, "
        f"no sympathy. Second person. Just the message — no preamble, no quotes.",
        fallback,
    )


# --------------------------------------------------------------------------- #
# 14:00 — the verdict was FAIL
# --------------------------------------------------------------------------- #


def compose_fail_for_diego(streak_lost: int) -> str:
    lost = (
        f" You just lost a {streak_lost}-day streak." if streak_lost else ""
    )
    fallback = f"❌ 2 PM passed with nothing posted. You owe Daniel 200 MXN.{lost}"
    body = _llm(
        f"Write ONE short message (max 200 chars) to Diego. The 2 PM deadline just "
        f"passed with no video published. He owes his brother Daniel 200 MXN"
        + (f" and just lost a {streak_lost}-day streak." if streak_lost else ".")
        + " Tone: flat, final, zero comfort. No advice, no encouragement. "
        "Just the message — no preamble, no quotes.",
        fallback,
    )
    # The consequence is stated by the code, never by the model.
    return f"{body}\n\n— 200 MXN owed. Streak reset to 0."


def compose_fail_for_daniel(streak_lost: int) -> str:
    fallback = "📉 Diego missed today's 2 PM deadline. You're owed 200 MXN."
    body = _llm(
        "Write ONE short message (max 160 chars) telling Daniel that his brother "
        "Diego missed today's 2 PM posting deadline and now owes him 200 MXN. "
        "Tone: dry, mildly amused. Just the message — no preamble, no quotes.",
        fallback,
    )
    return (
        f"{body}\n\n"
        f"— 200 MXN owed. Reply 'págame' within 24h to claim it, "
        f"or it expires. Streak reset from {streak_lost} to 0."
    )


# --------------------------------------------------------------------------- #
# Daily — the heartbeat to Daniel
# --------------------------------------------------------------------------- #


def compose_heartbeat(streak: int) -> str:
    """Daniel's out-of-band copy of the record.

    The number is appended deterministically. The model only decorates it.
    """
    fallback = "🫀 Overseer checking in."
    body = _llm(
        f"Write ONE very short line (max 100 chars) reporting to Daniel that the "
        f"accountability system is alive. Do NOT mention any number. "
        f"Tone: deadpan. Just the line — no preamble, no quotes.",
        fallback,
        max_tokens=60,
    )
    return f"{body}\n\nDiego's current streak: {streak} day(s)."


def compose_debt_claimed(streak: int) -> str:
    return f"✅ Debt claimed. 200 MXN owed to Daniel.\n\nDiego's current streak: {streak} day(s)."
