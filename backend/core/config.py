from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENROUTER_API_KEY: str
    APP_ENV: str
    #Add WA variables

    class Config:
        env_file = "../.env"

settings = Settings()

