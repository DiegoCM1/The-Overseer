from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    OPENROUTER_API_KEY: str
    APP_ENV: str

    # WA variables
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN : str
    TWILIO_WHATSAPP_FROM:str                                                
    TWILIO_WHATSAPP_TO:str

    class Config:
        env_file = BASE_DIR / ".env"

settings = Settings()

