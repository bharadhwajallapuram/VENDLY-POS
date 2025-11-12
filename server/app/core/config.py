import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = (
        f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vendly.db')}"
    )
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "change-me-in-production"  # set via env
    JWT_ALG: str = "HS256"
    ACCESS_TTL_MIN: int = 30
    REFRESH_TTL_DAYS: int = 7
    CORS_ORIGINS: List[str] = ["*"]  # Allow all origins for development

    class Config:
        env_file = ".env"


settings = Settings()
