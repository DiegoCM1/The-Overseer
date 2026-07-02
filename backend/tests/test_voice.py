"""TwiML endpoint returns valid, XML-escaped speech."""

from features.voice.router import voice_twiml


def test_twiml_structure_and_escaping():
    resp = voice_twiml(msg='Calisthenics <you & I> "late"')
    body = resp.body.decode()
    assert body.startswith("<?xml")
    assert "<Say" in body and "</Say>" in body
    # user text is escaped, not injected as raw markup
    assert "&lt;you &amp; I&gt;" in body
    assert "<you" not in body


def test_twiml_default_message():
    body = voice_twiml().body.decode()
    assert "<Say" in body and "deadline" in body.lower()
