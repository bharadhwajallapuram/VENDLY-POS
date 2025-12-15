"""
Vendly POS - Error Tracking with Sentry
========================================
Centralized error monitoring and reporting for frontend and backend
"""

import logging
import os
from typing import Any, Literal, Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

logger = logging.getLogger(__name__)


class SentryConfig:
    """Sentry configuration for Vendly POS"""

    def __init__(self):
        self.dsn = os.getenv("SENTRY_DSN", "")
        self.environment = os.getenv("SENTRY_ENVIRONMENT", "production")
        self.traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
        self.enable_debug = os.getenv("SENTRY_DEBUG", "False").lower() == "true"
        self.enabled = bool(self.dsn)

    def init_backend(self):
        """Initialize Sentry for FastAPI backend"""
        if not self.enabled:
            logger.info("[INFO] Sentry not configured for backend (DSN not set)")
            return

        try:
            sentry_sdk.init(
                dsn=self.dsn,
                integrations=[
                    FastApiIntegration(),
                    HttpxIntegration(),
                    SqlalchemyIntegration(),
                    RedisIntegration(),
                    LoggingIntegration(
                        level=logging.INFO,  # Capture info and above
                        event_level=logging.ERROR,  # Send errors as events
                    ),
                ],
                environment=self.environment,
                traces_sample_rate=self.traces_sample_rate,
                debug=self.enable_debug,
                # Performance Monitoring
                enable_tracing=True,
                # Release tracking
                release=os.getenv("APP_VERSION", "2.0.0"),
                # Ignore specific errors
                ignore_errors=[
                    "HTTPException",
                    "WebSocketDisconnect",
                ],
                # Before send hook for filtering
                before_send=self._before_send,
            )
            logger.info(f"[OK] Sentry initialized for backend (env={self.environment})")
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize Sentry backend: {e}")

    def init_frontend(self):
        """
        Return frontend Sentry configuration object
        This should be used in Next.js via @sentry/nextjs
        """
        if not self.enabled:
            return None

        return {
            "dsn": self.dsn,
            "environment": self.environment,
            "tracesSampleRate": self.traces_sample_rate,
            "debug": self.enable_debug,
            "release": os.getenv("APP_VERSION", "2.0.0"),
            "integrations": [
                {
                    "name": "Breadcrumbs",
                },
                {
                    "name": "GlobalHandlers",
                },
                {
                    "name": "HttpClient",
                },
                {
                    "name": "Replay",
                    "maskAllText": True,
                    "blockAllMedia": True,
                },
            ],
            "replaysSessionSampleRate": 0.1,
            "replaysOnErrorSampleRate": 1.0,
        }

    @staticmethod
    def _before_send(event, hint):
        """Filter sensitive information before sending to Sentry"""
        # Remove headers that might contain sensitive data
        if "request" in event:
            headers = event["request"].get("headers", {})
            sensitive_headers = [
                "Authorization",
                "Cookie",
                "X-API-Key",
                "X-Auth-Token",
            ]
            for header in sensitive_headers:
                if header in headers:
                    headers[header] = "[REDACTED]"

        # Filter breadcrumbs for sensitive data
        if "breadcrumbs" in event:
            for breadcrumb in event["breadcrumbs"]:
                if breadcrumb.get("category") == "http.request":
                    if "data" in breadcrumb:
                        breadcrumb["data"]["url"] = "[REDACTED_URL]"

        return event

    @staticmethod
    def capture_exception(
        error: Exception, level: str = "error", context: Optional[dict] = None
    ):
        """Manually capture an exception"""
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context("custom", {key: value})
            scope.level = level
            sentry_sdk.capture_exception(error)

    @staticmethod
    def capture_message(
        message: str,
        level: Literal[
            "fatal", "critical", "error", "warning", "info", "debug"
        ] = "info",
        context: Optional[dict] = None,
    ):
        """Manually capture a message"""
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context("custom", {key: value})
            scope.level = level
            sentry_sdk.capture_message(message, level=level)

    @staticmethod
    def add_breadcrumb(
        message: str,
        category: str = "custom",
        level: str = "info",
        data: Optional[dict] = None,
    ):
        """Add a breadcrumb for tracking user actions"""
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {},
        )

    @staticmethod
    def set_user_context(user_id: str, email: str = "", username: str = ""):
        """Set user context for error tracking"""
        sentry_sdk.set_user(
            {
                "id": user_id,
                "email": email,
                "username": username,
            }
        )

    @staticmethod
    def set_tag(key: str, value: str):
        """Set a tag for grouping errors"""
        sentry_sdk.set_tag(key, value)

    @staticmethod
    def set_context(name: str, data: dict):
        """Set additional context for errors"""
        sentry_sdk.set_context(name, data)


# Global instance
sentry_config = SentryConfig()
