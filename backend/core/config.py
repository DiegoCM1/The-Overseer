from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # extra="ignore" so stale keys left in .env don't block boot.
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    # MODE
    APP_ENV: str

    # DB
    DATABASE_URL: str

    # Fail loud, fail fast: an unreachable DB should raise in seconds, not hang.
    DB_CONNECT_TIMEOUT: int = 10   # seconds; postgres only
    DB_POOL_RECYCLE: int = 1800    # seconds; stay under pooler idle timeouts
    SQL_ECHO: bool = False         # true → log every SQL statement (noisy; debugging only)

    # Observability
    LOG_LEVEL: str = "INFO"        # DEBUG | INFO | WARNING | ERROR

    # ---- Agent (Google ADK) ----
    # Optional for now: filled in when the agent is wired up.
    GOOGLE_API_KEY: str = ""

    # ---- WhatsApp (Twilio) — phase 2 ----
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_FROM: str
    TWILIO_WHATSAPP_TO: str

    TIMEZONE: str = "America/Mexico_City"


settings = Settings()
