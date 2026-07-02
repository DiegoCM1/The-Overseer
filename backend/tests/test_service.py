"""The tick core: escalate the right levels, exactly once, with calls gated.

DB and Twilio are mocked — these tests assert control flow, not delivery."""

import pytest

from features.monitor import service


def _data(severity="missed", deadline_hour=19, now="2026-07-01T19:30:00-06:00"):
    # 19:30 vs a 19:00 deadline = 30 min past → desired level 1 for "missed".
    return {
        "date": "2026-07-01",
        "now": now,
        "goals": [{
            "goal_id": "posted", "label": "Posted", "severity": severity,
            "deadline_hour": deadline_hour, "fail_hour": None,
            "done_at": None, "tregua": False,
        }],
    }


@pytest.fixture
def spy(monkeypatch):
    """Mock all I/O, capturing what would be sent/recorded."""
    calls = {"wa": [], "call": [], "recorded": []}
    monkeypatch.setattr(service, "_already_sent", lambda *a: False)
    monkeypatch.setattr(service, "_record", lambda *a: calls["recorded"].append(a))
    monkeypatch.setattr(service, "send_whatsapp", lambda body: calls["wa"].append(body))
    monkeypatch.setattr(service, "make_call", lambda body: calls["call"].append(body))
    monkeypatch.setattr(service.messages, "compose", lambda g, level: f"L{level}")
    return calls


def test_l1_fires_and_records(spy):
    service._process(_data())
    assert spy["wa"] == ["L1"]
    assert spy["call"] == []
    assert len(spy["recorded"]) == 1


def test_backfills_every_step_up_to_target(spy):
    # 21:00 vs 19:00 = 120 min → still L2, so L1+L2 both fire (with their trail).
    service._process(_data(now="2026-07-01T21:00:00-06:00"))
    assert spy["wa"] == ["L1", "L2"]
    assert len(spy["recorded"]) == 2


def test_dedupe_skips_already_sent(monkeypatch):
    sent = []
    monkeypatch.setattr(service, "_already_sent", lambda *a: True)
    monkeypatch.setattr(service, "send_whatsapp", lambda body: sent.append(body))
    monkeypatch.setattr(service, "_record", lambda *a: None)
    monkeypatch.setattr(service.messages, "compose", lambda g, level: "x")
    service._process(_data())
    assert sent == []  # nothing re-sent


def test_healthy_goal_does_nothing(spy):
    service._process(_data(severity="ok"))
    assert spy["wa"] == [] and spy["call"] == [] and spy["recorded"] == []


def test_l3_calls_off_degrades_to_whatsapp(spy, monkeypatch):
    monkeypatch.setattr(service.settings, "ENABLE_CALLS", False)
    service._process(_data(severity="failed"))
    assert spy["call"] == []
    assert any(body.startswith("[CALL-WORTHY]") for body in spy["wa"])


def test_l3_calls_on_places_call(spy, monkeypatch):
    monkeypatch.setattr(service.settings, "ENABLE_CALLS", True)
    # 20:00 is outside quiet hours → the call goes through.
    service._process(_data(severity="failed", now="2026-07-01T20:00:00-06:00"))
    assert spy["call"] == ["L3"]


def test_l3_call_deferred_in_quiet_hours(spy, monkeypatch):
    monkeypatch.setattr(service.settings, "ENABLE_CALLS", True)
    # 23:00 is inside quiet hours → no call, degrade to WhatsApp.
    service._process(_data(severity="failed", now="2026-07-01T23:00:00-06:00"))
    assert spy["call"] == []
    assert any(body.startswith("[CALL-WORTHY]") for body in spy["wa"])


def test_delivery_failure_is_not_recorded(monkeypatch):
    """A failed send must NOT be recorded, so the next poll retries it."""
    recorded = []
    monkeypatch.setattr(service, "_already_sent", lambda *a: False)
    monkeypatch.setattr(service, "_record", lambda *a: recorded.append(a))
    monkeypatch.setattr(service.messages, "compose", lambda g, level: "x")

    def boom(body):
        raise RuntimeError("twilio down")

    monkeypatch.setattr(service, "send_whatsapp", boom)
    service._process(_data())
    assert recorded == []
