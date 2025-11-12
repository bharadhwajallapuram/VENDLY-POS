from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+mysqldb://user:password@localhost:3306/vendly"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET: str = "change-me"  # set via env
    JWT_ALG: str = "HS256"
    ACCESS_TTL_MIN: int = 30
    REFRESH_TTL_DAYS: int = 7
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

settings = Settings()