"""Message wording must NEVER block on the LLM: template fallback on no-client
and on any error; LLM text used only when the call succeeds."""

import types

from features.monitor import messages

GOAL = {"goal_id": "posted", "label": "Posted"}


def _fake_client(create):
    return types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create))
    )


def test_fallback_when_no_client(monkeypatch):
    monkeypatch.setattr(messages, "_client", None)
    out = messages.compose(GOAL, 1)
    assert "Posted" in out
    assert out == messages._TEMPLATES[1].format(label="Posted")


def test_fallback_on_error(monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("model down")

    monkeypatch.setattr(messages, "_client", _fake_client(boom))
    out = messages.compose(GOAL, 3)
    assert out == messages._TEMPLATES[3].format(label="Posted")


def test_uses_llm_text_on_success(monkeypatch):
    def ok(**kwargs):
        msg = types.SimpleNamespace(content="Get up. Posted isn't done. Move.")
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])

    monkeypatch.setattr(messages, "_client", _fake_client(ok))
    assert messages.compose(GOAL, 2) == "Get up. Posted isn't done. Move."


def test_blank_llm_text_falls_back(monkeypatch):
    def blank(**kwargs):
        msg = types.SimpleNamespace(content="   ")
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])

    monkeypatch.setattr(messages, "_client", _fake_client(blank))
    assert messages.compose(GOAL, 1) == messages._TEMPLATES[1].format(label="Posted")
