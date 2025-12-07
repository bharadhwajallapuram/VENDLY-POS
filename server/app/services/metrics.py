# ===========================================
# Vendly POS - Prometheus Metrics Service
# ===========================================

from typing import Callable
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# Simple metrics storage (in production, use prometheus_client library)
class MetricsStore:
    """Simple metrics store for Prometheus exposition"""

    def __init__(self):
        self.request_count = {}
        self.request_duration = {}
        self.error_count = {}
        self.active_connections = 0

    def record_request(self, method: str, path: str, status: int, duration: float):
        """Record a request metric"""
        key = f"{method}:{path}:{status}"

        if key not in self.request_count:
            self.request_count[key] = 0
            self.request_duration[key] = []

        self.request_count[key] += 1
        self.request_duration[key].append(duration)

        # Keep only last 1000 durations to prevent memory issues
        if len(self.request_duration[key]) > 1000:
            self.request_duration[key] = self.request_duration[key][-1000:]

        if status >= 400:
            error_key = f"{method}:{path}"
            self.error_count[error_key] = self.error_count.get(error_key, 0) + 1

    def get_metrics(self) -> str:
        """Generate Prometheus metrics format"""
        lines = []

        # Request count
        lines.append("# HELP vendly_http_requests_total Total number of HTTP requests")
        lines.append("# TYPE vendly_http_requests_total counter")
        for key, count in self.request_count.items():
            method, path, status = key.split(":", 2)
            lines.append(
                f'vendly_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
            )

        # Request duration
        lines.append(
            "# HELP vendly_http_request_duration_seconds HTTP request duration in seconds"
        )
        lines.append("# TYPE vendly_http_request_duration_seconds histogram")
        for key, durations in self.request_duration.items():
            if durations:
                method, path, status = key.split(":", 2)
                avg = sum(durations) / len(durations)
                lines.append(
                    f'vendly_http_request_duration_seconds{{method="{method}",path="{path}",le="avg"}} {avg:.6f}'
                )

        # Error count
        lines.append("# HELP vendly_http_errors_total Total number of HTTP errors")
        lines.append("# TYPE vendly_http_errors_total counter")
        for key, count in self.error_count.items():
            method, path = key.split(":", 1)
            lines.append(
                f'vendly_http_errors_total{{method="{method}",path="{path}"}} {count}'
            )

        # Active connections
        lines.append("# HELP vendly_active_connections Current active connections")
        lines.append("# TYPE vendly_active_connections gauge")
        lines.append(f"vendly_active_connections {self.active_connections}")

        return "\n".join(lines)


# Global metrics store
metrics_store = MetricsStore()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        metrics_store.active_connections += 1
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Normalize path to avoid high cardinality
            path = self._normalize_path(request.url.path)

            metrics_store.record_request(
                method=request.method,
                path=path,
                status=response.status_code,
                duration=duration,
            )

            return response
        finally:
            metrics_store.active_connections -= 1

    def _normalize_path(self, path: str) -> str:
        """Normalize path to reduce cardinality"""
        # Replace UUIDs with placeholder
        import re

        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", ":id", path
        )
        # Replace numeric IDs with placeholder
        path = re.sub(r"/\d+", "/:id", path)
        return path


def get_metrics_endpoint():
    """Endpoint to expose Prometheus metrics"""
    from fastapi import APIRouter
    from fastapi.responses import PlainTextResponse

    router = APIRouter()

    @router.get("/metrics", response_class=PlainTextResponse)
    async def metrics():
        return metrics_store.get_metrics()

    return router
