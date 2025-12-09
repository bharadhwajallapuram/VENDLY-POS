# ===========================================
# Vendly POS - Application Configuration
# Based on BVM-POS Architecture
# ===========================================

import os
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    APP_NAME: str = "Vendly POS"
    APP_ENV: str = Field(default="development", alias="APP_ENV")
    DEBUG: bool = Field(default=True, alias="DEBUG")
    SECRET_KEY: str = Field(default="change-me-in-production", alias="SECRET_KEY")

    # Database
    DATABASE_URL: str = Field(
        default=f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vendly.db')}",
        alias="DATABASE_URL",
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL: int = 3600  # 1 hour

    # JWT Authentication
    JWT_SECRET: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    JWT_ALG: str = "HS256"
    ACCESS_TTL_MIN: int = 30  # Token expires after 30 minutes
    REFRESH_TTL_DAYS: int = 7

    # Testing
    TESTING: bool = Field(default=False)

    # Rate Limiting (disabled during testing)
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_LOGIN: str = "5/minute"  # 5 login attempts per minute per IP
    RATE_LIMIT_API: str = "100/minute"  # 100 API calls per minute per user

    # Audit Logging
    AUDIT_LOG_ENABLED: bool = True

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Stripe Payments
    STRIPE_SECRET_KEY: str = Field(default="", alias="STRIPE_SECRET_KEY")

    # Kafka (Event Streaming)
    KAFKA_ENABLED: bool = False
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS"
    )
    KAFKA_CONSUMER_GROUP: str = "vendly-pos-group"

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"

    # AI/ML
    ML_ENABLED: bool = False
    ML_MODEL_PATH: str = "./ai_ml/models"

    # File Storage
    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = "./uploads"


settings = Settings()
