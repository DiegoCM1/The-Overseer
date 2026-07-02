"""Hermetic test setup: dummy env so `Settings()` builds without a real .env, and
DATABASE_URL forced to sqlite so nothing ever touches the real Railway DB. Set at
import time — this runs before any test module imports core.config."""

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "ACtest")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test-token")
os.environ.setdefault("TWILIO_WHATSAPP_FROM", "whatsapp:+10000000000")
os.environ.setdefault("TWILIO_WHATSAPP_TO", "whatsapp:+20000000000")
