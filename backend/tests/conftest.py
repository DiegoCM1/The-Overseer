"""Hermetic test setup: dummy env so `Settings()` builds without a real .env, and
DATABASE_URL forced to sqlite so nothing ever touches the real database. Set at
import time — this runs before any test module imports core.config."""

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "ACtest")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test-token")
os.environ.setdefault("TWILIO_WHATSAPP_FROM", "whatsapp:+10000000000")
os.environ.setdefault("TWILIO_WHATSAPP_TO", "whatsapp:+20000000000")
# The verdict is timezone-sensitive. Pin it so a value in a developer's .env
# cannot quietly change what PASS means.
os.environ.setdefault("TIMEZONE", "America/Mexico_City")

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402


@pytest.fixture
def db():
    """A real sqlite database per test, schema built from the models.

    StaticPool pins every session to the same in-memory connection. Without it,
    each checkout would get a fresh empty database and nothing would persist.
    """
    from core.db import Base
    import features.enforcement.ledger  # noqa: F401  (registers `events`)
    import features.monitor.models  # noqa: F401  (registers `notifications`)

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
