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


def init_database():
    """Initialize database and create admin user if needed"""
    from sqlalchemy import inspect
    from sqlalchemy.orm import Session

    from app.core.security import hash_password
    from app.db.models import Base, User
    from app.db.session import engine

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)

        # Check if admin exists
        with Session(engine) as session:
            admin = session.query(User).filter(User.email == "admin@vendly.com").first()
            if not admin:
                # Create default admin user
                admin = User(
                    email="admin@vendly.com",
                    password_hash=hash_password("admin123"),
                    full_name="System Admin",
                    is_active=True,
                    role="admin",
                )
                session.add(admin)
                session.commit()
                print("[OK] Default admin created: admin@vendly.com / admin123")
    except Exception as e:
        print(f"[ERROR] Error in init_database: {e}")
        import traceback

        traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events"""
    try:
        # Startup
        print(f"[STARTUP] Starting {settings.APP_NAME} in {settings.APP_ENV} mode")

        # Initialize database
        init_database()

        # Initialize backup scheduler if enabled
        if settings.BACKUP_ENABLED and settings.SCHEDULER_ENABLED:
            try:
                from app.services.backup_scheduler import get_backup_scheduler

                scheduler = get_backup_scheduler()
                scheduler.start()
                print("[OK] Backup scheduler initialized")
            except Exception as e:
                print(f"[WARNING] Backup scheduler initialization failed: {e}")

        # Initialize Kafka producer if enabled
        if settings.KAFKA_ENABLED:
            try:
                from kafka.producer import producer

                await producer.start()
                print("[OK] Kafka producer connected")
            except Exception as e:
                print(f"[WARNING] Kafka connection failed: {e}")

        yield

        # Shutdown
        print(f"[SHUTDOWN] Shutting down {settings.APP_NAME}")

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
        print(f"[ERROR] Error in lifespan: {e}")
        import traceback

        traceback.print_exc()


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
