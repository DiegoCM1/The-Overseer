from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    # AI
    OPENROUTER_API_KEY: str
    
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


    # WA
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_FROM: str
    TWILIO_WHATSAPP_TO: str          # Diego — the one under obligation

    # ---- Enforcement (the bet) ----
    # Daniel is the counterparty. His WhatsApp thread doubles as an out-of-band
    # replica of the history that Diego cannot rewrite, so this is load-bearing.
    TWILIO_WHATSAPP_DANIEL: str = ""

    # healthchecks.io check URL. Pinged after every judgment run; if the Overseer
    # dies, healthchecks notifies Daniel directly. Without it a crashed server is
    # worth 200 MXN to Diego, which is a terrible incentive to leave lying around.
    HEALTHCHECKS_URL: str = ""

    HEARTBEAT_HOUR: int = 20         # local hour for Daniel's daily streak report

    # life-os integration (the system of record the Overseer polls)
    LIFEOS_API_URL: str = "http://localhost:8000"
    LIFEOS_API_SECRET: str = ""

    # Escalation ladder (minutes past a deadline before each step fires)
    POLL_MINUTES: int = 15
    GRACE1_MIN: int = 60      # → firmer message
    GRACE2_MIN: int = 180     # → call
    QUIET_START: int = 22     # no calls placed inside [QUIET_START, QUIET_END)
    QUIET_END: int = 8
    ENABLE_CALLS: bool = False  # calls are built but off until flipped on

    # Delivery targets (E.164 for SMS/voice). WhatsApp uses the vars above.
    MY_PHONE: str = ""            # e.g. +5217151459328
    TWILIO_SMS_FROM: str = ""     # an SMS-capable Twilio number
    TWILIO_VOICE_FROM: str = ""   # a voice-capable Twilio number (not the WA sandbox)
    PUBLIC_BASE_URL: str = ""     # public URL of THIS service, for the TwiML callback

    TIMEZONE: str = "America/Mexico_City"

settings = Settings()

