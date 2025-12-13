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
    AUDIT_LOG_ENABLED: bool = Field(default=True, alias="AUDIT_LOG_ENABLED")
    AUDIT_LOG_FILE: str = Field(default="audit.log", alias="AUDIT_LOG_FILE")
    AUDIT_LOG_LEVEL: str = Field(default="INFO", alias="AUDIT_LOG_LEVEL")

    # Session Management
    SESSION_TIMEOUT_MINUTES: int = Field(default=15, alias="SESSION_TIMEOUT_MINUTES")
    SESSION_WARNING_SECONDS: int = Field(default=60, alias="SESSION_WARNING_SECONDS")
    ACTIVITY_DEBOUNCE_MS: int = Field(default=5000, alias="ACTIVITY_DEBOUNCE_MS")

    # Two-Factor Authentication (2FA)
    TWO_FACTOR_ENABLED: bool = Field(default=True, alias="TWO_FACTOR_ENABLED")
    TWO_FACTOR_BACKUP_CODES: int = Field(default=10, alias="TWO_FACTOR_BACKUP_CODES")
    TWO_FACTOR_TOTP_WINDOW: int = Field(default=1, alias="TWO_FACTOR_TOTP_WINDOW")
    TWO_FACTOR_REQUIRED_ROLES: List[str] = Field(
        default=["admin", "manager"], alias="TWO_FACTOR_REQUIRED_ROLES"
    )
    TWO_FACTOR_RATE_LIMIT: str = Field(
        default="5/minute", alias="TWO_FACTOR_RATE_LIMIT"
    )

    # Email Configuration (for 2FA and notifications)
    SMTP_ENABLED: bool = Field(default=False, alias="SMTP_ENABLED")
    SMTP_HOST: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, alias="SMTP_PORT")
    SMTP_USER: str = Field(default="", alias="SMTP_USER")
    SMTP_PASSWORD: str = Field(default="", alias="SMTP_PASSWORD")
    SMTP_FROM: str = Field(default="noreply@vendly.com", alias="SMTP_FROM")
    SMTP_TLS: bool = Field(default=True, alias="SMTP_TLS")

    # SMS Configuration (for 2FA)
    SMS_ENABLED: bool = Field(default=False, alias="SMS_ENABLED")
    SMS_PROVIDER: str = Field(
        default="twilio", alias="SMS_PROVIDER"
    )  # twilio, aws_sns, nexmo
    TWILIO_ENABLED: bool = Field(default=False, alias="TWILIO_ENABLED")
    TWILIO_ACCOUNT_SID: str = Field(default="", alias="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = Field(default="", alias="TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str = Field(default="", alias="TWILIO_PHONE_NUMBER")
    TWILIO_WHATSAPP_NUMBER: str = Field(default="", alias="TWILIO_WHATSAPP_NUMBER")

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
