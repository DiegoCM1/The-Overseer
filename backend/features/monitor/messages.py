"""Message wording. The LLM writes the nag; deterministic templates are the
fallback so a notification NEVER blocks on the model being slow or down."""

from openai import OpenAI

from core.config import settings

_client = (
    OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.OPENROUTER_API_KEY)
    if settings.OPENROUTER_API_KEY
    else None
)

_TEMPLATES = {
    1: "⚠️ {label}: the deadline passed and it's still not done. Handle it now.",
    2: "🔥 {label} — still not done. Second warning. Stop stalling and move.",
    3: "🚨 {label}: you blew the deadline. This is the failure that earns a call. No excuses — go.",
}

_TONE = {
    1: "a firm nudge",
    2: "a sharper, impatient second warning",
    3: "a furious, no-excuses wake-up call",
}


def _fallback(label: str, level: int) -> str:
    return _TEMPLATES[level].format(label=label)


def compose(goal: dict, level: int) -> str:
    label = goal["label"]
    if _client is None:
        return _fallback(label, level)
    prompt = (
        f"Write ONE short message (max 220 chars) to Diego, who missed his goal "
        f"'{label}' past its deadline. Tone: {_TONE[level]}. Second person, direct, "
        f"a little Joe Rogan discipline energy. Just the message — no preamble, no quotes."
    )
    try:
        resp = _client.chat.completions.create(
            model="deepseek/deepseek-v4-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            timeout=8,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or _fallback(label, level)
    except Exception:
        return _fallback(label, level)
