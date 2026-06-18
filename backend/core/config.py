from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # AI
    OPENROUTER_API_KEY: str
    
    # MODE
    APP_ENV: str

    # DB
    DATABASE_URL: str
    
    
    # WA
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_FROM: str                                            
    TWILIO_WHATSAPP_TO: str

    class Config:
        env_file = BASE_DIR / ".env"

settings = Settings()

