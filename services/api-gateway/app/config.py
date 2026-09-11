"""
Central configuration, loaded from environment variables.
This is the ONE place environment variables get read. Nothing else in the
codebase should call os.environ directly.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"
    log_level: str = "info"
    database_url: str = ""
    jwt_secret: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
