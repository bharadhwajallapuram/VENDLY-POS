# ===========================================
# Vendly POS - Main Application
# Created: 2024-01-15
# ===========================================

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers import api_router
from app.core.config import settings
from app.core.error_tracking import sentry_config
from app.services.metrics import MetricsMiddleware, get_metrics_endpoint

# Initialize Sentry error tracking
sentry_config.init_backend()


import logging

logger = logging.getLogger(__name__)


def init_database():
    """Initialize database and create admin user if needed"""
    from sqlalchemy.orm import Session

    from app.core.security import hash_password
    from app.db.models import Base, User
    from app.db.session import engine

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)

        # Only create default admin if enabled (use env vars in production!)
        if not settings.CREATE_DEFAULT_ADMIN:
            logger.info("Default admin creation disabled")
            return

        # Check if admin exists
        with Session(engine) as session:
            admin = (
                session.query(User)
                .filter(User.email == settings.DEFAULT_ADMIN_EMAIL)
                .first()
            )
            if not admin:
                # Create default admin user from environment config
                admin = User(
                    email=settings.DEFAULT_ADMIN_EMAIL,
                    password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                    full_name="System Admin",
                    is_active=True,
                    role="admin",
                )
                session.add(admin)
                session.commit()
                logger.info(f"Default admin created: {settings.DEFAULT_ADMIN_EMAIL}")
                if settings.APP_ENV == "development":
                    logger.warning("⚠️  Change default admin password in production!")
    except Exception as e:
        logger.error(f"Error in init_database: {e}", exc_info=True)


def init_subscription_plans():
    """Initialize subscription plans"""
    from sqlalchemy.orm import Session

    from app.db.session import engine
    from app.db.subscription_models import Base as SubscriptionBase

    try:
        # Create subscription tables
        SubscriptionBase.metadata.create_all(bind=engine)

        # Seed default plans
        from app.services.subscription_service import seed_plans

        with Session(engine) as session:
            seed_plans(session)
            logger.info("Subscription plans initialized")
    except Exception as e:
        logger.error(f"Error initializing subscription plans: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events"""
    try:
        # Startup
        logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode")

        # Initialize database
        init_database()

        # Initialize subscription plans
        init_subscription_plans()

        # Initialize backup scheduler if enabled
        if settings.BACKUP_ENABLED and settings.SCHEDULER_ENABLED:
            try:
                from app.services.backup_scheduler import get_backup_scheduler

                scheduler = get_backup_scheduler()
                scheduler.start()
                logger.info("Backup scheduler initialized")
            except Exception as e:
                logger.warning(f"Backup scheduler initialization failed: {e}")

        # Initialize Kafka producer if enabled
        if settings.KAFKA_ENABLED:
            try:
                from kafka.producer import producer

                await producer.start()
                logger.info("Kafka producer connected")
            except Exception as e:
                logger.warning(f"Kafka connection failed: {e}")

        yield

        # Shutdown
        logger.info(f"Shutting down {settings.APP_NAME}")

        # Stop backup scheduler
        try:
            from app.services.backup_scheduler import get_backup_scheduler

            scheduler = get_backup_scheduler()
            if scheduler.is_running:
                scheduler.stop()
        except Exception:
            pass

        if settings.KAFKA_ENABLED:
            try:
                from kafka.producer import producer

                await producer.stop()
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Error in lifespan: {e}", exc_info=True)


app = FastAPI(
    title="Vendly POS API",
    version="2.0.0",
    description="A modern, enterprise-grade point-of-sale system API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Metrics middleware (must be added before other middleware)
if settings.PROMETHEUS_ENABLED:
    app.add_middleware(MetricsMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": "2.0.0",
        "status": "running",
        "environment": settings.APP_ENV,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers and orchestrators"""
    return {
        "status": "healthy",
        "message": "API is operational",
        "service": settings.APP_NAME,
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Include metrics endpoint
if settings.PROMETHEUS_ENABLED:
    app.include_router(get_metrics_endpoint())
