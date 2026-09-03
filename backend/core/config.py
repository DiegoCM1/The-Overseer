from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # extra="ignore" so stale keys still sitting in .env don't block boot.
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    # Required: the app refuses to boot without these.
    APP_ENV: str                   # dev | prod

    # Observability
    LOG_LEVEL: str = "INFO"        # DEBUG | INFO | WARNING | ERROR

    # ---- Agent (Google ADK) — phase 1 ----
    GOOGLE_API_KEY: str = ""

    # ---- WhatsApp (Twilio) — phase 2, not wired up yet ----
    # Optional on purpose: nothing reads these until the WhatsApp webhook exists,
    # so requiring them would block boot on credentials the app never uses.
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = ""
    TWILIO_WHATSAPP_TO: str = ""

    TIMEZONE: str = "America/Mexico_City"


settings = Settings()
