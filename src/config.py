from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_BOT_USERNAME: str

    # Database
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # Cache
    CACHE_HOST: str
    CACHE_PORT: int
    CACHE_DB: int
    CACHE_MAX_CONNECTIONS: int

    class Config:
        env_file = Path(__file__).parent / ".env"


settings = Settings()
