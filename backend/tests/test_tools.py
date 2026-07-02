"""do_math must evaluate arithmetic but never execute code (the eval() fix)."""

from features.agent.tools import do_math


def test_arithmetic():
    assert do_math("2*3+4") == "10"
    assert do_math("2 ** 5") == "32"
    assert do_math("-(3 + 1)") == "-4"


def test_rejects_code_injection():
    assert "error" in do_math("__import__('os').system('echo pwned')")
    assert "error" in do_math("open('/etc/passwd').read()")
