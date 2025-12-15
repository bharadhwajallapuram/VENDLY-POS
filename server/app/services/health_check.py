"""
Vendly POS - Health Check Service
==================================
Comprehensive health monitoring for all services
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redis_client import get_token_store
from app.db.session import SessionLocal, engine

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceHealth:
    """Health check information for a service"""

    def __init__(
        self,
        name: str,
        status: HealthStatus = HealthStatus.HEALTHY,
        message: str = "",
        response_time_ms: float = 0.0,
        details: Optional[Dict] = None,
    ):
        self.name = name
        self.status = status
        self.message = message
        self.response_time_ms = response_time_ms
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "response_time_ms": round(self.response_time_ms, 2),
            "details": self.details,
            "timestamp": self.timestamp,
        }


class HealthCheckService:
    """Service for performing comprehensive health checks"""

    @staticmethod
    async def check_database() -> ServiceHealth:
        """Check database connectivity and performance"""
        import time

        name = "Database"
        start_time = time.time()

        try:
            with SessionLocal() as session:
                # Test basic connectivity
                result = session.execute(text("SELECT 1")).scalar()
                response_time = (time.time() - start_time) * 1000

                if result == 1:
                    return ServiceHealth(
                        name=name,
                        status=HealthStatus.HEALTHY,
                        message="Database connection successful",
                        response_time_ms=response_time,
                    )
                else:
                    return ServiceHealth(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message="Database returned unexpected result",
                        response_time_ms=response_time,
                    )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")
            return ServiceHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                response_time_ms=response_time,
            )

    @staticmethod
    async def check_redis() -> ServiceHealth:
        """Check Redis connectivity"""
        import time

        name = "Redis"
        start_time = time.time()

        try:
            # Try to use Redis via the token store
            token_store = get_token_store()
            if not hasattr(token_store, "_client") or token_store._client is None:
                return ServiceHealth(
                    name=name,
                    status=HealthStatus.DEGRADED,
                    message="Redis not available, using in-memory fallback",
                    response_time_ms=(time.time() - start_time) * 1000,
                )

            # Try to ping Redis
            pong = token_store._client.ping()
            response_time = (time.time() - start_time) * 1000

            if pong:
                # Get Redis info
                info = token_store._client.info()
                return ServiceHealth(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    message="Redis connection successful",
                    response_time_ms=response_time,
                    details={
                        "redis_version": info.get("redis_version", "unknown"),
                        "connected_clients": info.get("connected_clients", 0),
                        "used_memory_human": info.get("used_memory_human", "unknown"),
                    },
                )
            else:
                return ServiceHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message="Redis ping failed",
                    response_time_ms=response_time,
                )
        except redis.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message="Failed to connect to Redis",
                response_time_ms=response_time,
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Redis health check failed: {e}")
            return ServiceHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Redis health check failed: {str(e)}",
                response_time_ms=response_time,
            )

    @staticmethod
    async def check_kafka() -> ServiceHealth:
        """Check Kafka connectivity"""
        import time

        name = "Kafka"
        start_time = time.time()

        if not settings.KAFKA_ENABLED:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                name=name,
                status=HealthStatus.DEGRADED,
                message="Kafka is disabled",
                response_time_ms=response_time,
            )

        try:
            from kafka import KafkaProducer
            from kafka.errors import KafkaError

            try:
                producer = KafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(","),
                    request_timeout_ms=5000,
                )
                producer.close()
                response_time = (time.time() - start_time) * 1000
                return ServiceHealth(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    message="Kafka connection successful",
                    response_time_ms=response_time,
                )
            except KafkaError as e:
                response_time = (time.time() - start_time) * 1000
                return ServiceHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Kafka connection failed: {str(e)}",
                    response_time_ms=response_time,
                )
        except ImportError:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                name=name,
                status=HealthStatus.DEGRADED,
                message="Kafka module not available",
                response_time_ms=response_time,
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Kafka health check failed: {e}")
            return ServiceHealth(
                name=name,
                status=HealthStatus.DEGRADED,
                message=f"Kafka health check failed: {str(e)}",
                response_time_ms=response_time,
            )

    @staticmethod
    async def check_api() -> ServiceHealth:
        """Check API health"""
        name = "API"
        return ServiceHealth(
            name=name,
            status=HealthStatus.HEALTHY,
            message="API is operational",
            details={
                "version": "2.0.0",
                "environment": settings.APP_ENV,
            },
        )

    @staticmethod
    async def get_all_health_checks() -> Dict:
        """Perform all health checks and return results"""
        import time

        start_time = time.time()

        # Run checks
        api_health = await HealthCheckService.check_api()
        db_health = await HealthCheckService.check_database()
        redis_health = await HealthCheckService.check_redis()
        kafka_health = await HealthCheckService.check_kafka()

        checks = [api_health, db_health, redis_health, kafka_health]

        # Determine overall health
        statuses = [c.status for c in checks]
        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        total_time = (time.time() - start_time) * 1000

        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "total_response_time_ms": round(total_time, 2),
            "services": [c.to_dict() for c in checks],
        }

    @staticmethod
    async def get_readiness_check() -> Dict:
        """
        Readiness check - only return ready if critical services are healthy
        Used for Kubernetes readiness probes
        """
        db_health = await HealthCheckService.check_database()
        api_health = await HealthCheckService.check_api()

        ready = (
            db_health.status == HealthStatus.HEALTHY
            and api_health.status == HealthStatus.HEALTHY
        )

        return {
            "ready": ready,
            "status": "ready" if ready else "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "services": [
                api_health.to_dict(),
                db_health.to_dict(),
            ],
        }

    @staticmethod
    async def get_liveness_check() -> Dict:
        """
        Liveness check - simple API responsiveness check
        Used for Kubernetes liveness probes
        """
        api_health = await HealthCheckService.check_api()

        return {
            "alive": api_health.status == HealthStatus.HEALTHY,
            "status": "alive" if api_health.status == HealthStatus.HEALTHY else "dead",
            "timestamp": datetime.utcnow().isoformat(),
        }
