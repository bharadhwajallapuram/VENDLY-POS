"""
Vendly POS - Health Check Endpoints
====================================
API endpoints for health monitoring and status checks
"""

from fastapi import APIRouter, Response

from app.services.health_check import HealthCheckService

router = APIRouter(prefix="/health", tags=["Health & Status"])


@router.get("/", response_description="Basic health check")
async def basic_health_check():
    """Basic health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "service": "Vendly POS API",
        "version": "2.0.0",
    }


@router.get("/live", response_description="Liveness probe")
async def liveness_probe(response: Response):
    """
    Kubernetes liveness probe endpoint
    Returns 200 if the application is alive and responsive
    """
    result = await HealthCheckService.get_liveness_check()

    if not result["alive"]:
        response.status_code = 503

    return result


@router.get("/ready", response_description="Readiness probe")
async def readiness_probe(response: Response):
    """
    Kubernetes readiness probe endpoint
    Returns 200 only if the service is ready to handle traffic
    (database and other critical services are healthy)
    """
    result = await HealthCheckService.get_readiness_check()

    if not result["ready"]:
        response.status_code = 503

    return result


@router.get("/detailed", response_description="Detailed health check")
async def detailed_health_check(response: Response):
    """
    Detailed health check endpoint
    Returns comprehensive health information for all services
    """
    result = await HealthCheckService.get_all_health_checks()

    # Return 503 Service Unavailable if overall status is unhealthy
    if result["status"] != "healthy":
        response.status_code = 503

    return result


@router.get("/startup", response_description="Startup probe")
async def startup_probe(response: Response):
    """
    Kubernetes startup probe endpoint
    Returns 200 once the application has started successfully
    """
    db_health = await HealthCheckService.check_database()

    # Application is considered started once database is accessible
    started = db_health.status.value == "healthy"

    if not started:
        response.status_code = 503

    return {
        "started": started,
        "status": "started" if started else "starting",
        "database": db_health.to_dict(),
    }
